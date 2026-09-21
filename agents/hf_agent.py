"""
SuperFarmer Local Agent — Ollama qwen2.5:7b
Native agentic tool-calling loop with persistent in-memory conversation history.
No smolagents / litellm dependency needed.
"""

import json
import ollama
from config import execute_fluxbase_sql

# ── Tool definitions (OpenAI-compatible schema for Ollama) ────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_farmer_profile",
            "description": "Fetch the farmer's profile: name, land size, location, water availability, farming goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "farmer_id": {"type": "integer", "description": "The farmer's unique ID"}
                },
                "required": ["farmer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_crop_plan",
            "description": "Get the farmer's latest crop plan: sowing schedule, irrigation plan, fertilizer schedule, harvest timeline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "farmer_id": {"type": "integer", "description": "The farmer's unique ID"}
                },
                "required": ["farmer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get 3-day weather forecast and farming advice for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or region name in India"}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_crop_recommendations",
            "description": "Fetch the last AI-generated crop recommendation for this farmer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "farmer_id": {"type": "integer", "description": "The farmer's unique ID"}
                },
                "required": ["farmer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nutrient_risk",
            "description": "Check latest nutrient deficiency risk level and suggested corrective action for this farmer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "farmer_id": {"type": "integer", "description": "The farmer's unique ID"}
                },
                "required": ["farmer_id"]
            }
        }
    }
]

# ── Tool execution (calls real Fluxbase DB or WeatherAgent) ──────────

def _execute_tool(name: str, args: dict) -> str:
    try:
        if name == "get_farmer_profile":
            fid = int(args["farmer_id"])
            res = execute_fluxbase_sql(
                f"SELECT * FROM farmer_profile WHERE farmer_id={fid} LIMIT 1"
            )
            rows = res.get("rows", [])
            return json.dumps(rows[0]) if rows else "No profile found."

        elif name == "get_crop_plan":
            fid = int(args["farmer_id"])
            res = execute_fluxbase_sql(
                f"SELECT * FROM crop_plans WHERE farmer_id={fid} ORDER BY created_at DESC LIMIT 1"
            )
            rows = res.get("rows", [])
            return json.dumps(rows[0]) if rows else "No crop plan found."

        elif name == "get_weather":
            from agents.agents import WeatherAgent
            return WeatherAgent.analyze_weather(args["location"])

        elif name == "get_crop_recommendations":
            fid = int(args["farmer_id"])
            res = execute_fluxbase_sql(
                f"SELECT recommended_crops, created_at FROM crop_recommendations "
                f"WHERE farmer_id={fid} ORDER BY created_at DESC LIMIT 1"
            )
            rows = res.get("rows", [])
            return json.dumps(rows[0]) if rows else "No past recommendation found."

        elif name == "get_nutrient_risk":
            fid = int(args["farmer_id"])
            res = execute_fluxbase_sql(
                f"SELECT risk_level, risk_probability, suggested_action FROM nutrient_risk_log "
                f"WHERE farmer_id={fid} ORDER BY logged_at DESC LIMIT 1"
            )
            rows = res.get("rows", [])
            return json.dumps(rows[0]) if rows else "No nutrient risk data."

        else:
            return f"Unknown tool: {name}"

    except Exception as e:
        return f"Tool error ({name}): {e}"


# ── System prompt ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are SuperFarmer AI — a decision-making agricultural agent for Indian farmers.

STRICT RULES:
- You are NOT a chatbot. You are a tool-using agent.
- Always call get_farmer_profile(farmer_id) FIRST before answering any question.
- NEVER guess or invent values. Use your tools to get real data.
- Detect the language from the user's message and reply in the SAME language and script.
- Supported languages: Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Kannada, Punjabi, Odia, Malayalam, English.

MANDATORY OUTPUT FORMAT (always use this exact structure):
📋 FARM SUMMARY
[Name, location, land size, water availability — from get_farmer_profile result]

🌾 CROP RECOMMENDATION
[Top 1-3 crops based on soil + water rules. State the rule applied.]

🗺️ SPATIAL LAYOUT
[Hex/row layout, spacing in cm, companion crop pairing]

📊 YIELD COMPARISON
[Optimized yield (tons/acre) vs Normal (tons/acre), % improvement, ₹ extra estimate]

💡 REASON
[Simple explanation of which data drove the decision]

✅ DO THIS TODAY: [one immediate action the farmer can take right now]"""


# ── Per-session memory store ──────────────────────────────────────────
# Key: farmer_id (int or None) → list of Ollama message dicts
_session_memory: dict[str, list] = {}

MAX_HISTORY = 20   # keep last 20 turns per farmer to avoid context overflow


def hf_agent_chat(message: str, farmer_id=None, language="en-IN") -> str:
    """
    Main entry point called by OrchestratorAgent.
    Runs a full agentic loop:
      1. Send message + tools to Ollama
      2. If model calls a tool → execute it → feed result back
      3. Repeat until model gives a final text answer
    Memory persists per farmer_id across requests.
    """
    session_key = str(farmer_id) if farmer_id else "anon"

    # Initialise session memory if first time
    if session_key not in _session_memory:
        _session_memory[session_key] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    history = _session_memory[session_key]

    # Append user message
    history.append({"role": "user", "content": message})

    try:
        # Agentic loop — up to 5 tool calls
        for _ in range(5):
            response = ollama.chat(
                model="qwen2.5:7b",
                messages=history,
                tools=TOOLS,
            )

            msg = response.message

            # If no tool call → final answer
            if not msg.tool_calls:
                final = msg.content or "I could not generate a response."
                history.append({"role": "assistant", "content": final})
                # Trim memory to MAX_HISTORY (keep system prompt)
                if len(history) > MAX_HISTORY + 1:
                    _session_memory[session_key] = [history[0]] + history[-(MAX_HISTORY):]
                return final

            # Execute all tool calls the model requested
            history.append(msg)   # add assistant's tool-call message to history
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_args = tc.function.arguments or {}
                tool_result = _execute_tool(tool_name, tool_args)
                history.append({
                    "role": "tool",
                    "content": tool_result,
                })

        # Max steps reached — ask model to summarise what it has
        history.append({
            "role": "user",
            "content": "Please give your final structured answer now based on the data you have collected."
        })
        response = ollama.chat(model="qwen2.5:7b", messages=history)
        final = response.message.content or "Could not generate final answer."
        history.append({"role": "assistant", "content": final})
        return final

    except Exception as e:
        # Graceful fallback to SuperFarmerChatAgent (powered by Fluxbase / GLM / Groq)
        err_msg = str(e)
        try:
            from agents.agents import SuperFarmerChatAgent
            return SuperFarmerChatAgent.chat(message, [], farmer_id=farmer_id, language=language)
        except Exception as e_fallback:
            return f"Chat error: {err_msg} | Fallback error: {e_fallback}"
