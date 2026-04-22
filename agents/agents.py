from config import execute_fluxbase_sql
import os
import re
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai
import PIL.Image
from openai import OpenAI

# ── Primary LLM: Groq llama-3.1-8b-instant ───────────────────────────────────
def _call_groq(system_prompt: str, user_message: str, history: list = None) -> str:
    """Primary LLM: Groq llama-3.1-8b-instant."""
    api_key = os.environ.get("GROK_API_KEY")
    if not api_key:
        raise ValueError("GROK_API_KEY missing from .env")
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for m in history:
            role = "user" if m.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": m.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
    )
    return response.choices[0].message.content

# ── Fallback LLM: Anthropic Claude Haiku ─────────────────────────────────────
def _call_claude(system_prompt: str, user_message: str, history: list = None) -> str:
    """Fallback LLM: Anthropic claude-haiku-4-5."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY missing from .env")
    client = anthropic.Anthropic(api_key=api_key)
    messages = []
    if history:
        for m in history:
            role = "user" if m.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": m.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text

# ── Unified call: Groq primary → Claude fallback ──────────────────────────────
def _call_llm(system_prompt: str, user_message: str, history: list = None,
              label: str = "LLM") -> str:
    """Call Groq first; fall back to Claude on any error."""
    try:
        print(f"   🤖 [{label}] Model : groq/llama-3.1-8b-instant")
        t0 = time.time()
        result = _call_groq(system_prompt, user_message, history)
        print(f"   ✅ [{label}] Response in {round(time.time()-t0,2)}s")
        return result
    except Exception as e_groq:
        print(f"   ⚠️  [{label}] Groq failed: {e_groq}")
        print(f"   🔄 [{label}] Fallback : anthropic/claude-haiku-4-5")
        try:
            t0 = time.time()
            result = _call_claude(system_prompt, user_message, history)
            print(f"   ✅ [{label}] Claude response in {round(time.time()-t0,2)}s")
            return result
        except Exception as e_claude:
            return f"Both primary (Groq) and fallback (Claude) failed.\nGroq: {e_groq}\nClaude: {e_claude}"

# Keep _call_gemini as a thin alias so existing non-critical callers don't break
def _call_gemini(system_prompt: str, user_message: str, history: list = None) -> str:
    return _call_llm(system_prompt, user_message, history, label="LLM")
# ─────────────────────────────────────────────────────────────────────────────


def safe_str(val):
    if val is None:
        return ""
    return str(val).replace("'", "''")

class WeatherAgent:
    @staticmethod
    def analyze_weather(location):
        api_key = os.environ.get("TOMORROW_API_KEY")
        if not api_key:
             return "Tomorrow.io API Key missing from .env."
        return WeatherAgent._fetch_tomorrow(location, api_key)

    @staticmethod
    def _fetch_tomorrow(location, api_key):
        try:
            # Geocode the location using Nominatim to ensure Tomorrow.io receives latitude,longitude
            try:
                geo_res = requests.get('https://nominatim.openstreetmap.org/search', 
                                       params={'q': location, 'format': 'json', 'limit': 1},
                                       headers={'User-Agent': 'SuperFarmerApp/1.0'})
                geo_data = geo_res.json()
                if geo_data:
                    location = f"{geo_data[0]['lat']},{geo_data[0]['lon']}"
            except Exception:
                pass # fallback to original string

            print("\n" + "━" * 60)
            print(f"🌦️  [WeatherAgent] Fetching forecast")
            print(f"   📍 Location : {location}")
            print(f"   🔌 Source   : Tomorrow.io REST API")
            print("━" * 60)
            t0 = time.time()
            url = "https://api.tomorrow.io/v4/weather/forecast"
            headers = {"accept": "application/json"}
            params = {"location": location, "apikey": api_key}
            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if 'timelines' not in data:
                print(f"   ❌ Failed: {data.get('message', 'Unknown error')}")
                print("━" * 60 + "\n")
                return f"Tomorrow.io Analysis failed: {data.get('message', 'Unknown error. Could not fetch weather data.')}"

            elapsed = round(time.time() - t0, 2)
            print(f"   ✅ Weather data received in {elapsed}s")
            print("━" * 60 + "\n")
            daily = data['timelines']['daily']
            
            # Aggregate next 3 days of data
            total_prob = 0
            max_temp = -100
            
            analysis = f"3-Day Hyper-Local Forecast for {location} (via Tomorrow.io):\n"
            
            # Using Tomorrow.io daily timelines
            for item in daily[:3]:
                time_str = item['time'].split('T')[0]
                values = item['values']
                
                temp_max = values.get('temperatureMax', 0)
                precip_prob = values.get('precipitationProbabilityMax', 0)
                
                if temp_max > max_temp:
                    max_temp = temp_max
                
                analysis += f"- {time_str}: Temp Max: {round(temp_max, 1)}°C, Rain Probability: {precip_prob}%\n"
                
                # Check for high rain probability (proxy for rain volume)
                if precip_prob > 50:
                    total_prob += precip_prob
            
            analysis += "\n**Agent Suggestion:** "
            return WeatherAgent._generate_suggestion(analysis, total_prob, max_temp)
            
        except Exception as e:
            return f"Weather analysis failed: {str(e)}"

    @staticmethod
    def _generate_suggestion(analysis, high_prob_days, max_temp):
        # high_prob_days is sum of probabilities > 50. If there are 2 days of > 50% rain (e.g. 150 total score):
        if high_prob_days > 100:
            analysis += f"High probability of heavy, sustained rain. If your crop is near maturity, **Harvest Early** to prevent water logging and rot."
        elif high_prob_days > 50:
            analysis += "Moderate/Brief rain expected. Let the crop grow, but hold off on any manual irrigation."
        elif max_temp > 38:
            analysis += "Extreme heat expected. Ensure adequate irrigation; **Let crop grow** but monitor for heat stress."
        else:
            analysis += "Clear weather ahead. **Let crop grow** normally."
        return analysis

class EmailAgent:
    @staticmethod
    def send_email(to_email, subject, body):
        sender_email = os.environ.get('EMAIL_ADDRESS')
        sender_password = os.environ.get('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("Email credentials not found in environment variables.")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            # Using Gmail's SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, to_email, text)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

from werkzeug.security import generate_password_hash, check_password_hash

class UserAuthAgent:
    @staticmethod
    def signup_user(email, password):
        try:
            hashed_pw = generate_password_hash(password)
            safe_email = safe_str(email)
            query = f"INSERT INTO users (email, password_hash) VALUES ('{safe_email}', '{hashed_pw}');"
            execute_fluxbase_sql(query)
            
            # Fetch the inserted user_id
            sel_query = f"SELECT user_id FROM users WHERE email = '{safe_email}'"
            sel_res = execute_fluxbase_sql(sel_query)
            # res['rows'] usually looks like: [{'user_id': 1}]
            user_id = sel_res['rows'][0]['user_id']
            return {"success": True, "user_id": user_id}
        except Exception as err:
            return {"success": False, "error": str(err)}

    @staticmethod
    def login_user(email, password):
        safe_email = safe_str(email)
        query = f"SELECT user_id, password_hash FROM users WHERE email = '{safe_email}'"
        res = execute_fluxbase_sql(query)
        if res.get('rows'):
            user_record = res['rows'][0]
            if check_password_hash(user_record['password_hash'], password):
                return {"success": True, "user_id": user_record['user_id']}
        return {"success": False, "error": "Invalid email or password."}

    @staticmethod
    def get_farmer_profile_by_user(user_id):
        query = f"SELECT farmer_id FROM farmer_profile WHERE user_id = {int(user_id)} LIMIT 1"
        res = execute_fluxbase_sql(query)
        if res.get('rows'):
            return res['rows'][0]['farmer_id']
        return None

class IntakeAgent:
    @staticmethod
    def process_intake(user_id, name, land_size, location, water, goals):
        print("\n" + "━" * 60)
        print("👤 [IntakeAgent] Saving farmer profile")
        print(f"   Name     : {name}")
        print(f"   Location : {location}")
        print(f"   Land     : {land_size} acres | Water: {water}")
        print("━" * 60)
        try:
            acres = float(land_size)
        except ValueError:
            acres = 0.0

        query = f"""INSERT INTO farmer_profile 
                   (user_id, name, land_size, location, water_availability, farming_goals) 
                   VALUES ({int(user_id)}, '{safe_str(name)}', {acres}, '{safe_str(location)}', '{safe_str(water)}', '{safe_str(goals)}');"""
        
        execute_fluxbase_sql(query)
        
        # Fetch the inserted farmer_id
        sel_query = f"SELECT farmer_id FROM farmer_profile WHERE user_id = {int(user_id)} ORDER BY farmer_id DESC LIMIT 1"
        sel_res = execute_fluxbase_sql(sel_query)
        farmer_id = sel_res['rows'][0]['farmer_id']
        return farmer_id

class CropRecommendationAgent:
    @staticmethod
    def recommend(farmer_id, soil_type, n, p, k, temp, rain, water_const):
        print("\n" + "━" * 60)
        print("🌾 [CropRecommendation] Analysing soil parameters")
        print(f"   Soil     : {soil_type} | Water: {water_const}")
        print(f"   NPK      : N={n} P={p} K={k} | Temp={temp}°C | Rain={rain}mm")
        print("━" * 60)

        rec_str = None
        prompt = f"Analyze these soil parameters for Indian farming: N:{n}, P:{p}, K:{k}, Temp:{temp}C, Rain:{rain}mm, Soil:{soil_type}, Water:{water_const}. Recommend the top 3 most suitable crops. Return ONLY the crop names, comma-separated."

        try:
            from dotenv import dotenv_values
            env_vars = dotenv_values(".env")
            api_key = env_vars.get("GROK_API_KEY") or os.environ.get("GROK_API_KEY")
            if api_key:
                print("   🤖 Model    : groq/llama-3.1-8b-instant")
                t0 = time.time()
                client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}]
                )
                rec_str = response.choices[0].message.content.strip().replace("'", "\'")
                print(f"   ✅ Response  : received in {round(time.time()-t0,2)}s → {rec_str}")
            else:
                print("   ❌ GROK_API_KEY missing")
        except Exception as e:
            print(f"   ⚠️  Groq inference error: {e}")

        # Fallback: rule-based deterministic logic
        if not rec_str:
            rec_str = CropRecommendationAgent._fallback_recommend(soil_type, n, p, k, temp, rain, water_const)
            print(f"   🔄 Fallback  : rule-based → {rec_str}")

        print("━" * 60 + "\n")
        query = f"INSERT INTO crop_recommendations (farmer_id, recommended_crops) VALUES ({int(farmer_id)}, '{safe_str(rec_str)}');"
        execute_fluxbase_sql(query)
        return rec_str

    @staticmethod
    def _fallback_recommend(soil_type, n, p, k, temp, rain, water_const):
        import random
        # Fallback recommendations if API fails
        recommendations = []
        soil = soil_type.lower()
        water = water_const.lower()
        if water == 'low':
            recommendations = ['Pearl Millet', 'Chickpea', 'Moth Beans'] if soil in ('red', 'laterite', 'sandy') else ['Sorghum', 'Chickpea', 'Lentil']
        elif soil == 'black':
            if n > 40 and temp > 22: recommendations.append('Cotton')
            if rain > 600 or water == 'high': recommendations.append('Wheat')
            recommendations.append('Soybean')
        elif soil == 'alluvial':
            if water == 'high': recommendations.append('Rice')
            if n > 30: recommendations.append('Sugarcane')
            recommendations.append('Maize')
        elif soil in ('red', 'laterite'):
            recommendations += ['Groundnut', 'Finger Millet']
        elif soil == 'sandy':
            recommendations = ['Pearl Millet', 'Watermelon', 'Sesame']
        else:
            recommendations = ['Maize', 'Sorghum', 'Pigeon Peas']
        
        if not recommendations:
            recommendations = ["Wheat", "Rice", "Corn"]
            
        return ", ".join(recommendations[:3])

class CropPlannerAgent:
    @staticmethod
    def generate_plan(farmer_id, crop_name):
        print("\n" + "━" * 60)
        print("📋 [CropPlanner] Generating crop management plan")
        print(f"   Crop     : {crop_name}")
        print(f"   Farmer ID: {farmer_id}")
        print("━" * 60)
        plan = {}
        prompt = f"""You are an expert Indian agronomist. Generate a detailed crop management plan for {crop_name} farming in India.
Output EXACTLY this JSON structure:
{{
  "sowing_schedule": "...",
  "irrigation_plan": "...",
  "fertilizer_schedule": "...",
  "pest_alerts": "...",
  "harvest_timeline": "..."
}}"""

        try:
            from dotenv import dotenv_values
            env_vars = dotenv_values(".env")
            api_key = env_vars.get("GROK_API_KEY") or os.environ.get("GROK_API_KEY")
            if api_key:
                print("   🤖 [Planner] Model : groq/llama-3.1-8b-instant")
                t0 = time.time()
                client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                print(f"   ✅ [Planner] Response in {round(time.time()-t0,2)}s")
                import json
                text = response.choices[0].message.content.strip()
                if text.startswith("```json"):
                    text = text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
                elif text.startswith("```"):
                    text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()
                plan = json.loads(text)
        except Exception as e:
            print(f"[PlannerAgent] Groq error: {e}")

        if not plan or not all(k in plan for k in ['sowing_schedule', 'irrigation_plan', 'fertilizer_schedule', 'pest_alerts', 'harvest_timeline']):
            plan = CropPlannerAgent._fallback_plan(crop_name)

        query = f"""INSERT INTO crop_plans 
                   (farmer_id, crop_name, sowing_schedule, irrigation_plan, 
                    fertilizer_schedule, pest_alerts, harvest_timeline) 
                   VALUES ({int(farmer_id)}, '{safe_str(crop_name)}', '{safe_str(plan['sowing_schedule'])}', '{safe_str(plan['irrigation_plan'])}', 
                   '{safe_str(plan['fertilizer_schedule'])}', '{safe_str(plan['pest_alerts'])}', '{safe_str(plan['harvest_timeline'])}');"""

        execute_fluxbase_sql(query)

        sel_query = f"SELECT plan_id FROM crop_plans WHERE farmer_id = {int(farmer_id)} ORDER BY plan_id DESC LIMIT 1"
        sel_res = execute_fluxbase_sql(sel_query)
        if sel_res.get('rows'):
            plan['plan_id'] = sel_res['rows'][0]['plan_id']
        else:
            plan['plan_id'] = None
        return plan

    @staticmethod
    def _fallback_plan(crop_name):
        return {
            'sowing_schedule': 'Sow during the appropriate season according to local climate.',
            'irrigation_plan': 'Provide regular irrigation based on rainfall and soil moisture.',
            'fertilizer_schedule': 'Use balanced NPK fertilizers and organic compost.',
            'pest_alerts': 'Monitor regularly for pests and use necessary organic or chemical controls.',
            'harvest_timeline': 'Harvest when crop reaches maturity.',
        }

# (genai and PIL already imported at top of file)

class DiseaseDiagnosisAgent:
    _DIAGNOSIS_SYSTEM = (
        "You are an AI Plant Pathologist Agent.\n"
        "Analyze symptoms from images or text descriptions to diagnose crop diseases.\n"
        "Provide clear, organic-first treatment plans where possible.\n"
        "Be precise and cautionary about chemical usage.\n"
        "Return JSON only."
    )

    @staticmethod
    def diagnose(leaf_text, leaf_image=None):
        import json
        import time
        from urllib.parse import quote_plus
        has_image = bool(leaf_image and getattr(leaf_image, 'filename', None))

        print("\n" + "━" * 60)
        print("🔬 [DiseaseAI] New diagnosis request")
        print(f"   Symptom  : {leaf_text[:120]}{'...' if len(leaf_text) > 120 else ''}")
        print(f"   Image    : {'✅ Attached (' + leaf_image.filename + ')' if has_image else '❌ None (text-only)'}")
        print("━" * 60)

        prompt = (
            f"Symptoms: {leaf_text or 'Visual only'}\n\n"
            "Analyze the provided information (and image if applicable) to diagnose the disease.\n"
            "Return EXACTLY this JSON structure:\n"
            "{\n"
            '  "diagnosis": "Name of the disease",\n'
            '  "confidence": "High/Medium/Low or percentage like 85%",\n'
            '  "treatment": "Actionable treatment steps (organic & chemical), each step on a new line",\n'
            '  "prevention": "Preventative measures for next season, each point on a new line",\n'
            '  "products": [\n'
            '    { "name": "Product Name (e.g. Mancozeb 75 WP)", "type": "Fungicide/Pesticide/Fertilizer/Bio-stimulant", "dose": "Usage dose e.g. 2g/L water", "searchQuery": "short Amazon search query e.g. mancozeb fungicide india" }\n'
            "  ]\n"
            "}\n"
            "Provide 2-4 relevant products. Include at least one organic/bio option. Return ONLY VALID JSON."
        )

        raw_result = None

        # ── PATH A: Image attached ────────────────────────────────────────────
        if has_image:
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                try:
                    print("   🤖 Model    : gemini-2.5-flash  [Vision]")
                    print("   ⏳ Calling Gemini Vision API...")
                    t0 = time.time()
                    genai.configure(api_key=api_key)
                    gmodel = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
                    img = PIL.Image.open(leaf_image)
                    response = gmodel.generate_content([DiseaseDiagnosisAgent._DIAGNOSIS_SYSTEM + "\n\n" + prompt, img])
                    raw_result = response.text
                    elapsed = round(time.time() - t0, 2)
                    print(f"   ✅ Gemini Vision response in {elapsed}s")
                except Exception as e:
                    print(f"   ⚠️  Gemini Vision failed: {e}")
            else:
                print("   ❌ GEMINI_API_KEY missing")

            if raw_result is None:
                print("   🔄 Fallback : anthropic/claude-haiku-4-5  [text-based]")
                try:
                    t0 = time.time()
                    raw_result = _call_claude(
                        system_prompt=DiseaseDiagnosisAgent._DIAGNOSIS_SYSTEM,
                        user_message=prompt + "\n(Image could not be analysed — use text description only.)",
                    )
                    elapsed = round(time.time() - t0, 2)
                    print(f"   ✅ Claude response in {elapsed}s")
                except Exception as e2:
                    print(f"   ❌ Claude also failed: {e2}")

        # ── PATH B: Text-only (or Vision failed fallback) ─────────────────────
        if raw_result is None:
            try:
                print("   🤖 [DiseaseAI] Model : groq/llama-3.1-8b-instant")
                api_key = os.environ.get("GROK_API_KEY")
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
                t0 = time.time()
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": DiseaseDiagnosisAgent._DIAGNOSIS_SYSTEM},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                raw_result = response.choices[0].message.content
                print(f"   ✅ [DiseaseAI] Response in {round(time.time()-t0,2)}s")
            except Exception as e_groq:
                print(f"   ⚠️  Groq failed: {e_groq}")
                print("   🔄 Fallback : anthropic/claude-haiku-4-5")
                try:
                    t0 = time.time()
                    raw_result = _call_claude(
                        system_prompt=DiseaseDiagnosisAgent._DIAGNOSIS_SYSTEM,
                        user_message=prompt,
                    )
                    print(f"   ✅ Claude response in {round(time.time()-t0,2)}s")
                except Exception as e_claude:
                     print(f"   ❌ Claude also failed: {e_claude}")

        # Parse JSON
        if raw_result is None:
            print("━" * 60 + "\n")
            return {"error": "All AI models failed."}

        try:
             text = raw_result.strip()
             if text.startswith("```json"):
                 text = text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
             elif text.startswith("```"):
                 text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()
             
             data = json.loads(text)
             
             # enrich products with search URLs
             if "products" in data and isinstance(data["products"], list):
                 for prod in data["products"]:
                     q = quote_plus(prod.get("searchQuery", prod.get("name", "")))
                     prod["amazon"] = f"https://www.amazon.in/s?k={q}"
                     prod["flipkart"] = f"https://www.flipkart.com/search?q={q}"

             print(f"   ✅ Diagnosis parsed cleanly: {data.get('diagnosis')}")
             print("━" * 60 + "\n")
             return data
        except Exception as e:
             print(f"   ⚠️ JSON Parse failed: {e}")
             print(f"Raw Output: {raw_result}")
             print("━" * 60 + "\n")
             return {"error": "Failed to parse AI response as JSON.", "raw": raw_result}



class ReportAgent:
    @staticmethod
    def generate_report(farmer_id):
        profile_res = execute_fluxbase_sql(f"SELECT * FROM farmer_profile WHERE farmer_id={int(farmer_id)}")
        profile = profile_res['rows'][0] if profile_res.get('rows') else None

        plan_res = execute_fluxbase_sql(f"SELECT * FROM crop_plans WHERE farmer_id={int(farmer_id)} ORDER BY created_at DESC LIMIT 1")
        plan = plan_res['rows'][0] if plan_res.get('rows') else None

        report_text = "=== SUPERFARMER ADVISORY REPORT ===\n"
        if profile:
            report_text += f"Farmer: {profile.get('name')} | Location: {profile.get('location')}\n"

        if plan:
            report_text += f"\n-- Active Crop Plan: {plan.get('crop_name')} --\n"
            report_text += f"Status: {plan.get('status')}\n"
            report_text += f"Irrigation: {plan.get('irrigation_plan')}\n"
            report_text += f"Fertilizer: {plan.get('fertilizer_schedule')}\n"
            report_text += f"Sowing: {plan.get('sowing_schedule')}\n"
            report_text += f"Harvest: {plan.get('harvest_timeline')}\n"

        report_text += "\nNote: This is an AI-generated synthesis. Please consult local agronomic extensions for critical actions."

        execute_fluxbase_sql(f"INSERT INTO reports (farmer_id, report_text) VALUES ({int(farmer_id)}, '{safe_str(report_text)}')")
        return report_text

class SpatialPlannerAgent:
    CROP_DB = {
        'Corn':       {'name': 'Corn',       'color': '#16a34a', 'emoji': '🌽', 'spacing': 60, 'height_m': 2.5, 'water': 'Medium', 'nitrogen': 'Consumer', 'shade': 'Sensitive', 'profit_score': 7, 'companion_score': 8, 'yield_t_per_acre': 2.8},
        'Tomato':     {'name': 'Tomato',     'color': '#ef4444', 'emoji': '🍅', 'spacing': 50, 'height_m': 1.2, 'water': 'High',   'nitrogen': 'Consumer', 'shade': 'Tolerant', 'profit_score': 9, 'companion_score': 7, 'yield_t_per_acre': 8.0},
        'Wheat':      {'name': 'Wheat',      'color': '#fcd34d', 'emoji': '🌾', 'spacing': 20, 'height_m': 1.0, 'water': 'Low',    'nitrogen': 'Consumer', 'shade': 'Sensitive', 'profit_score': 6, 'companion_score': 6, 'yield_t_per_acre': 1.6},
        'Rice':       {'name': 'Rice',       'color': '#34d399', 'emoji': '🌾', 'spacing': 25, 'height_m': 1.2, 'water': 'High',   'nitrogen': 'Consumer', 'shade': 'Tolerant', 'profit_score': 7, 'companion_score': 5, 'yield_t_per_acre': 2.2},
        'Sugarcane':  {'name': 'Sugarcane',  'color': '#84cc16', 'emoji': '🎋', 'spacing': 90, 'height_m': 3.5, 'water': 'High',   'nitrogen': 'Consumer', 'shade': 'Sensitive', 'profit_score': 8, 'companion_score': 5, 'yield_t_per_acre': 35.0},
        'Cotton':     {'name': 'Cotton',     'color': '#f9fafb', 'emoji': '🪴', 'spacing': 75, 'height_m': 1.5, 'water': 'Medium', 'nitrogen': 'Consumer', 'shade': 'Sensitive', 'profit_score': 7, 'companion_score': 6, 'yield_t_per_acre': 0.5},
        'Soybean':    {'name': 'Soybean',    'color': '#a3e635', 'emoji': '🫘', 'spacing': 30, 'height_m': 0.8, 'water': 'Low',    'nitrogen': 'Fixer',    'shade': 'Tolerant', 'profit_score': 7, 'companion_score': 9, 'yield_t_per_acre': 0.9},
        'Maize':      {'name': 'Maize',      'color': '#facc15', 'emoji': '🌽', 'spacing': 65, 'height_m': 2.0, 'water': 'Medium', 'nitrogen': 'Consumer', 'shade': 'Sensitive', 'profit_score': 7, 'companion_score': 7, 'yield_t_per_acre': 3.2},
        'Onion':      {'name': 'Onion',      'color': '#c084fc', 'emoji': '🧅', 'spacing': 15, 'height_m': 0.5, 'water': 'Medium', 'nitrogen': 'Neutral',  'shade': 'Tolerant',  'profit_score': 8, 'companion_score': 9, 'yield_t_per_acre': 6.0},
        'Garlic':     {'name': 'Garlic',     'color': '#e2e8f0', 'emoji': '🧄', 'spacing': 12, 'height_m': 0.4, 'water': 'Low',    'nitrogen': 'Neutral',  'shade': 'Tolerant',  'profit_score': 9, 'companion_score': 9, 'yield_t_per_acre': 4.5},
        'Marigold':   {'name': 'Marigold',   'color': '#f97316', 'emoji': '🌼', 'spacing': 20, 'height_m': 0.6, 'water': 'Low',    'nitrogen': 'Neutral',  'shade': 'Tolerant',  'profit_score': 5, 'companion_score': 10,'yield_t_per_acre': 1.2},
        'Groundnut':  {'name': 'Groundnut',  'color': '#d97706', 'emoji': '🥜', 'spacing': 30, 'height_m': 0.5, 'water': 'Low',    'nitrogen': 'Fixer',    'shade': 'Tolerant',  'profit_score': 8, 'companion_score': 9, 'yield_t_per_acre': 1.0},
        'Mustard':    {'name': 'Mustard',    'color': '#fef08a', 'emoji': '🌿', 'spacing': 20, 'height_m': 1.2, 'water': 'Low',    'nitrogen': 'Neutral',  'shade': 'Sensitive', 'profit_score': 7, 'companion_score': 7, 'yield_t_per_acre': 0.7},
        'Chickpea':   {'name': 'Chickpea',   'color': '#fde68a', 'emoji': '🫘', 'spacing': 25, 'height_m': 0.6, 'water': 'Low',    'nitrogen': 'Fixer',    'shade': 'Tolerant',  'profit_score': 8, 'companion_score': 9, 'yield_t_per_acre': 0.8},
        'Potato':     {'name': 'Potato',     'color': '#a78bfa', 'emoji': '🥔', 'spacing': 35, 'height_m': 0.6, 'water': 'Medium', 'nitrogen': 'Consumer', 'shade': 'Tolerant', 'profit_score': 8, 'companion_score': 7, 'yield_t_per_acre': 8.0},
        'Sunflower':  {'name': 'Sunflower',  'color': '#fbbf24', 'emoji': '🌻', 'spacing': 45, 'height_m': 2.0, 'water': 'Low',    'nitrogen': 'Neutral',  'shade': 'Sensitive', 'profit_score': 7, 'companion_score': 7, 'yield_t_per_acre': 0.5},
    }

    COMPANION_MATRIX = {
        'Corn':      ['Soybean', 'Groundnut', 'Marigold', 'Pumpkin'],
        'Tomato':    ['Marigold', 'Onion', 'Garlic', 'Basil', 'Carrot'],
        'Wheat':     ['Chickpea', 'Mustard', 'Clover', 'Soybean'],
        'Rice':      ['Azolla', 'Groundnut', 'Sunflower'],
        'Cotton':    ['Marigold', 'Soybean', 'Groundnut', 'Onion'],
        'Sugarcane': ['Soybean', 'Groundnut', 'Garlic', 'Onion'],
        'Potato':    ['Marigold', 'Garlic', 'Corn'],
        'Onion':     ['Tomato', 'Corn', 'Marigold', 'Garlic'],
        'Maize':     ['Soybean', 'Groundnut', 'Marigold'],
    }

    @staticmethod
    def hex_layout(crop, zone, offset=0):
        import math
        nodes = []
        sp = crop['spacing']
        row = 0
        y = zone['y'] + sp * 0.5
        while y < zone['y'] + zone['h'] - sp * 0.4:
            x_shift = (row % 2) * (sp / 2.0) + offset
            col = 0
            x = zone['x'] + x_shift + sp * 0.5
            while x < zone['x'] + zone['w'] - sp * 0.4:
                nodes.append({
                    'x': round(x, 2),
                    'y': round(y, 2),
                    'type': crop['name'],
                    'color': crop['color'],
                    'radius': max(4.0, sp * 0.32),
                    'row': row,
                    'col': col,
                    'height_m': crop.get('height_m', 1.0)
                })
                col += 1
                x += sp
            row += 1
            y += math.floor(sp * 0.866)
        return nodes

    @staticmethod
    def generate_layout(farmer_id, width, height, main_crop, layout_preference="Auto", acres=None):
        """
        Intelligent Spatial Twin Agent:
        Generates optimized multi-crop layouts based on Hexagonal algorithmic design
        and database values.
        """
        try:
            w = float(width)
            h = float(height)
        except (TypeError, ValueError):
            w, h = 800.0, 500.0

        print(f"\n━" * 60)
        print(f"🗺️  [Spatial Twin] Generating Digital Layout")
        print(f"   Land Bounds  : {w}x{h} px")
        print(f"   Main Crop    : {main_crop}")

        # Fetch Farmer Context
        farmer_name, land_size_val = "Unknown", 1.0
        profile_data = {}
        try:
            p_res = execute_fluxbase_sql(f"SELECT * FROM farmer_profile WHERE farmer_id={int(farmer_id)}")
            if p_res.get('rows'):
                profile_data = p_res['rows'][0]
                farmer_name = profile_data.get('name', 'Unknown')
                try:
                    land_size_val = float(acres) if acres else float(profile_data.get('land_size', 1.0))
                except (ValueError, TypeError):
                    land_size_val = 1.0
            else:
                if acres:
                    try:
                        land_size_val = float(acres)
                    except (ValueError, TypeError):
                        pass
        except Exception:
            land_size_val = 1.0

        # Normalize incoming crop name → exact CROP_DB key
        CROP_ALIASES = {
            'tomatoes': 'Tomato', 'tomato': 'Tomato',
            'corn': 'Corn', 'maize': 'Maize',
            'wheat': 'Wheat', 'rice': 'Rice',
            'sugarcane': 'Sugarcane', 'cotton': 'Cotton',
            'soybean': 'Soybean', 'soybeans': 'Soybean',
            'onion': 'Onion', 'onions': 'Onion',
            'garlic': 'Garlic', 'potato': 'Potato', 'potatoes': 'Potato',
            'sunflower': 'Sunflower', 'sunflowers': 'Sunflower',
            'mustard': 'Mustard', 'chickpea': 'Chickpea', 'chickpeas': 'Chickpea',
            'groundnut': 'Groundnut', 'groundnuts': 'Groundnut', 'peanut': 'Groundnut',
            'marigold': 'Marigold', 'marigolds': 'Marigold',
        }
        raw = (main_crop or '').strip()
        if raw and raw != 'Auto':
            normalized = CROP_ALIASES.get(raw.lower(), raw)
            main_crop_key = normalized if normalized in SpatialPlannerAgent.CROP_DB else 'Corn'
        else:
            main_crop_key = 'Corn'

        print(f"   Crop Lookup  : '{raw}' → '{main_crop_key}'")
        main_data = SpatialPlannerAgent.CROP_DB[main_crop_key]
        
        # Determine optimal companion
        companions_list = SpatialPlannerAgent.COMPANION_MATRIX.get(main_crop_key, [])
        valid_companions = [c for c in companions_list if c in SpatialPlannerAgent.CROP_DB]
        companion_data = SpatialPlannerAgent.CROP_DB[valid_companions[0]] if valid_companions else SpatialPlannerAgent.CROP_DB['Marigold']
        
        all_crops = [main_data, companion_data]
        num_crops = len(all_crops)
        print(f"   Partnership  : {main_data['name']} + {companion_data['name']}")

        import math

        # Build zones — divide canvas horizontally by crop ratio
        total_weight = sum([1.0 / c['spacing'] for c in all_crops])
        zones = []
        x_cursor = 0.0
        for i, crop in enumerate(all_crops):
            weight = (1.0 / crop['spacing']) / total_weight
            zone_w = math.floor(w * weight)
            zones.append({
                'x': x_cursor, 'y': 0,
                'w': zone_w, 'h': h,
                'crop': crop['name'], 'color': crop['color'],
                'label': f"Zone {i + 1}: {crop['name']}"
            })
            x_cursor += zone_w
        if zones:
            zones[-1]['w'] = w - zones[-1]['x']

        # Generate plant nodes
        all_nodes = []
        for i, crop in enumerate(all_crops):
            zone = zones[i]
            all_nodes.extend(SpatialPlannerAgent.hex_layout(crop, zone))
            
        print(f"   Nodes Placed : {len(all_nodes)}")
        print(f"━" * 60 + "\n")

        # Insights logic
        fixer_count = sum(1 for c in all_crops if c['nitrogen'] == 'Fixer')
        nitrogen_balance = f"{fixer_count} nitrogen-fixing crop(s) reduce fertilizer needs" if fixer_count > 0 else "Add a legume to fix nitrogen"
        
        avg_water_map = {'Low': 1, 'Medium': 2, 'High': 3}
        total_water_score = sum(avg_water_map.get(c['water'], 2) for c in all_crops)
        water_efficiency = round((1 - (total_water_score / (num_crops * 3))) * 30) if num_crops > 1 else 0
        
        companion_score = sum(1 for c in all_crops[1:] if c['name'] in SpatialPlannerAgent.COMPANION_MATRIX.get(main_crop_key, []))
        
        total_yield = 0.0
        for i, c in enumerate(all_crops):
            zone = zones[i]
            zone_acres = (zone['w'] / w) * land_size_val
            total_yield += c['yield_t_per_acre'] * zone_acres

        warnings = []
        if companion_data['name'] not in SpatialPlannerAgent.COMPANION_MATRIX.get(main_crop_key, []):
             warnings.append(f"{companion_data['name']} is not a natural companion for {main_data['name']}.")
        if any(c['water'] == 'High' for c in all_crops) and any(c['water'] == 'Low' for c in all_crops):
             warnings.append("Mixed water needs — use drip irrigation to provide targeted watering per zone.")

        insights = {
            'total_plants': len(all_nodes),
            'land_efficiency': min(95, 70 + companion_score * 5 + (10 if num_crops > 1 else 0)),
            'water_saving_pct': water_efficiency,
            'yield_boost_pct': min(40, companion_score * 6 + (8 if fixer_count > 0 else 0)),
            'nitrogen_balance': nitrogen_balance,
            'best_combo': ", ".join(companions_list[:3]) if companions_list else "Marigold, Legumes",
            'warnings': warnings,
            'action_items': [
                f"Plant {main_data['name']} in the largest zone with {main_data['spacing']}cm spacing",
                "Companion zones provide micro-climate benefits" if len(all_crops)>1 else "Add a companion crop",
                "No synthetic nitrogen needed — legumes fix atmospheric N₂" if fixer_count > 0 else "Apply 40kg nitrogen fertilizer per acre",
                f"Estimated total yield: {round(total_yield, 1)} tonnes from {land_size_val} acre(s)",
            ]
        }

        analysis = (
            f"**Digital Twin Generated** — {len(all_nodes)} planting nodes across {num_crops} crop zone(s).\n\n"
            f"This layout uses **{main_data['name']}** as the primary crop, intercropped with **{companion_data['name']}**. "
            f"Land efficiency is **{insights['land_efficiency']}%** with an estimated **{insights['yield_boost_pct']}%** yield boost over monoculture."
        )

        return {
            "layout": all_nodes,
            "zones": zones,
            "insights": insights,
            "analysis": analysis,
            "main_crop": main_data['name'],
            "companion": companion_data['name'],
            "farmer_name": farmer_name,
            "land_size": str(land_size_val)
        }


class SuperFarmerChatAgent:
    """
    Decision-making agricultural agent.
    NOT a chatbot — fetches real farmer data from Fluxbase and applies
    deterministic rules before generating a structured response.
    """

    # ── Base agent persona ─────────────────────────────────────────────────────
    _BASE_PERSONA = """You are SuperFarmer AI — an expert multi-agent agricultural decision system built exclusively for Indian farmers.

═══════════════════════════════════════════
AGENT IDENTITY — READ CAREFULLY
═══════════════════════════════════════════
You are NOT a chatbot. You are a decision-making agent that uses farmer memory,
database records, and deterministic rules to produce structured agricultural decisions.

STRICT RULES:
❌ DO NOT guess or hallucinate any values.
❌ DO NOT give generic advice unrelated to the farmer's actual data.
❌ DO NOT repeat questions already answered in the FARMER CONTEXT block below.
✅ Always base decisions on the FARMER CONTEXT block provided.
✅ If data is missing, state clearly what is missing and why it matters.
✅ Use the farmer's language — detect it and respond in the SAME script.

═══════════════════════════════════════════
LANGUAGE RULE (CRITICAL)
═══════════════════════════════════════════
- Detect the language the user writes in.
- Always respond in the SAME language and script.
- Supported: हिंदी, বাংলা, తెలుగు, मराठी, தமிழ், ગુJರాతి, ಕನ್ನಡ, ਪੰਜਾਬੀ, ଓଡ଼ିଆ, മലയാളം, English.
- Use simple, village-level vocabulary — NO technical jargon.

═══════════════════════════════════════════
DECISION PIPELINE (FOLLOW IN ORDER)
═══════════════════════════════════════════
Step 1 — Understand the user intent from their message.
Step 2 — Retrieve relevant values from the FARMER CONTEXT block below.
Step 3 — Apply deterministic logic:
          • Soil + water + nutrients → CROP RECOMMENDATION
          • Crop + land size        → SPATIAL LAYOUT description
          • Optimized vs. normal   → YIELD COMPARISON
Step 4 — Generate output in the EXACT format below.
Step 5 — Use natural language ONLY in the REASON section.

═══════════════════════════════════════════
SOIL → CROP MAPPING (DETERMINISTIC)
═══════════════════════════════════════════
Black/Clay          → Cotton, Soybean, Wheat, Sorghum
Alluvial/Loamy      → Rice, Sugarcane, Wheat, Maize
Sandy/Laterite      → Groundnut, Pearl Millet, Sesame
Red/Acidic          → Finger Millet, Sunflower, Pigeon Peas
Clayey/Waterlogged  → Jute, Rice, Taro
Silty/River-bank    → Banana, Papaya, Vegetables

WATER AVAILABILITY OVERRIDE:
Low  → ONLY drought-tolerant crops (Pearl Millet, Chickpea, Groundnut)
High → Water-intensive crops allowed (Rice, Sugarcane, Banana)

═══════════════════════════════════════════
AGENT MODES — AUTO-ACTIVATE BY INTENT
═══════════════════════════════════════════
WEATHER intent  → give sowing/harvest timing advice for the farmer's location.
CROP intent     → apply soil+water rules, recommend top 3 crops with intercropping.
PEST/DISEASE    → identify from symptoms, give organic + chemical remedies, add purchase link.
MARKET intent   → share MSP rates, eNAM selling advice, seasonal price outlook.
SOIL/FERTILIZER → guide NPK correction, composting, Soil Health Card.
SCHEME intent   → list PM-KISAN, PMFBY, KCC steps with documents needed.

═══════════════════════════════════════════
MANDATORY OUTPUT FORMAT
═══════════════════════════════════════════
Always structure your response exactly like this:

📋 FARM SUMMARY
[Farmer name, location, land size, water availability, farming goals — from profile data]

🌾 CROP RECOMMENDATION
[Top 1-3 crops based on soil+water rules. State the rule applied.]

🗺️ SPATIAL LAYOUT
[Describe optimal layout: hexagonal/row-based, spacing in cm, companion crop pairing]

📊 YIELD COMPARISON
[Optimized yield (tons/acre) vs. Normal yield (tons/acre), improvement %, extra ₹ earning estimate]

💡 REASON
[Explain the decision in simple language. Mention which data fields drove the decision.]

✅ DO THIS TODAY: [one immediate action the farmer can take right now]

═══════════════════════════════════════════
GROUND REALITIES
═══════════════════════════════════════════
1. 85% of Indian farmers own < 2 hectares — never give large-farm advice.
2. Debt traps are real — always suggest free/cheap solutions first.
3. End every response with: ✅ DO THIS TODAY: [one immediate action]"""

    # ── Fetch farmer memory from Fluxbase ─────────────────────────────────────
    @staticmethod
    def _build_farmer_context(farmer_id) -> str:
        """Pull profile, latest crop plan, and risk log from Fluxbase."""
        if not farmer_id:
            return "\n[FARMER CONTEXT: No farmer_id available — ask the farmer to complete their profile first.]\n"

        lines = [
            "\n═══════════════════════════════════════════",
            "FARMER CONTEXT (live data from database — treat as ground truth)",
            "═══════════════════════════════════════════",
        ]

        # Profile
        try:
            p_res = execute_fluxbase_sql(
                f"SELECT * FROM farmer_profile WHERE farmer_id={int(farmer_id)} LIMIT 1"
            )
            if p_res.get('rows'):
                p = p_res['rows'][0]
                lines += [
                    f"Name              : {p.get('name', 'Unknown')}",
                    f"Location          : {p.get('location', 'Unknown')}",
                    f"Land Size         : {p.get('land_size', 'Unknown')} acres",
                    f"Water Availability: {p.get('water_availability', 'Unknown')}",
                    f"Farming Goals     : {p.get('farming_goals', 'Unknown')}",
                ]
            else:
                lines.append("Profile: NOT FOUND in database.")
        except Exception as e:
            lines.append(f"Profile fetch error: {e}")

        # Latest crop plan
        try:
            cp_res = execute_fluxbase_sql(
                f"SELECT * FROM crop_plans WHERE farmer_id={int(farmer_id)} ORDER BY created_at DESC LIMIT 1"
            )
            if cp_res.get('rows'):
                cp = cp_res['rows'][0]
                lines += [
                    "",
                    f"Active Crop       : {cp.get('crop_name', 'None')}",
                    f"Plan Status       : {cp.get('status', 'Unknown')}",
                    f"Sowing Schedule   : {cp.get('sowing_schedule', 'N/A')}",
                    f"Irrigation Plan   : {cp.get('irrigation_plan', 'N/A')}",
                    f"Fertilizer Sched. : {cp.get('fertilizer_schedule', 'N/A')}",
                    f"Harvest Timeline  : {cp.get('harvest_timeline', 'N/A')}",
                ]
            else:
                lines.append("\nActive Crop Plan  : None on record.")
        except Exception as e:
            lines.append(f"Crop plan fetch error: {e}")

        # Latest nutrient risk
        try:
            nr_res = execute_fluxbase_sql(
                f"SELECT * FROM nutrient_risk_log WHERE farmer_id={int(farmer_id)} ORDER BY logged_at DESC LIMIT 1"
            )
            if nr_res.get('rows'):
                nr = nr_res['rows'][0]
                lines += [
                    "",
                    f"Nutrient Risk     : {nr.get('risk_level', 'N/A')} ({nr.get('risk_probability', 'N/A')}%)",
                    f"Suggested Action  : {nr.get('suggested_action', 'N/A')}",
                ]
        except Exception:
            pass  # non-critical

        # Last recommendation
        try:
            cr_res = execute_fluxbase_sql(
                f"SELECT recommended_crops FROM crop_recommendations WHERE farmer_id={int(farmer_id)} ORDER BY created_at DESC LIMIT 1"
            )
            if cr_res.get('rows'):
                lines.append(f"\nPast AI Crop Rec. : {cr_res['rows'][0].get('recommended_crops', 'None')}")
        except Exception:
            pass

        lines.append("═══════════════════════════════════════════\n")
        return "\n".join(lines)

    @staticmethod
    def chat(message, history, farmer_id=None):
        # Build grounded system prompt with live farmer memory from Fluxbase
        farmer_context = SuperFarmerChatAgent._build_farmer_context(farmer_id)
        full_system_prompt = SuperFarmerChatAgent._BASE_PERSONA + "\n" + farmer_context

        # Call Gemini with fully-grounded context
        return _call_gemini(
            system_prompt=full_system_prompt,
            user_message=message,
            history=history,
        )

class YieldComparisonAgent:
    """
    Rule-based Yield Comparison Agent:
    Compares optimized intercropping layout vs. normal unplanned farming.
    """

    # Base yield (tons/acre) per crop — realistic Indian agricultural averages
    BASE_YIELDS = {
        'rice':         2.5, 'wheat':        1.9, 'maize':     2.2, 'cotton':      0.5,
        'sugarcane':   35.0, 'groundnut':    0.9, 'soybean':   1.0, 'chickpea':    0.7,
        'pigeon peas': 0.6,  'pearl millet': 1.2, 'sorghum':   1.1, 'lentil':      0.6,
        'tomatoes':    8.0,  'corn':         2.2, 'banana':   15.0, 'coconut':     5.0,
        'sunflower':   0.8,  'mustard':      0.8, 'jute':      2.0, 'finger millet':1.3,
        'vegetables':  5.0,  'papaya':      12.0, 'sesame':    0.5,
    }

    # Companion crop synergy bonus (additional % on top of intercropping boost)
    COMPANION_BONUS = {
        'soybean':      0.08,  # strong N-fixer
        'chickpea':     0.07,
        'pigeon peas':  0.07,
        'lentil':       0.06,
        'clover':       0.06,
        'marigolds':    0.05,  # pest suppression
        'coriander':    0.04,
        'beans':        0.06,
        'cover crop':   0.05,
    }

    @staticmethod
    def compare(land_size: float, main_crop: str, companion_crop: str) -> str:
        mc = main_crop.lower().strip()
        cc = companion_crop.lower().strip() if companion_crop and companion_crop.lower() != 'none' else ''

        # Lookup base yield
        base = YieldComparisonAgent.BASE_YIELDS.get(mc)
        if not base:
            # partial match
            for k, v in YieldComparisonAgent.BASE_YIELDS.items():
                if k in mc or mc in k:
                    base = v
                    break
        if not base:
            base = 1.5  # generic fallback

        # Intercropping improvement: 10–25% based on companion synergy
        companion_bonus = 0.0
        for k, bonus in YieldComparisonAgent.COMPANION_BONUS.items():
            if k in cc:
                companion_bonus = bonus
                break
        intercrop_boost = 0.15 + companion_bonus          # 15% base + companion bonus
        intercrop_boost = min(intercrop_boost, 0.30)       # cap at 30%

        # Normal layout penalty: 5–15%
        normal_penalty = 0.10

        optimized_yield_per_acre = round(base * (1 + intercrop_boost), 2)
        normal_yield_per_acre    = round(base * (1 - normal_penalty), 2)
        improvement_pct          = round(((optimized_yield_per_acre - normal_yield_per_acre) / normal_yield_per_acre) * 100, 1)

        optimized_total = round(optimized_yield_per_acre * land_size, 2)
        normal_total    = round(normal_yield_per_acre    * land_size, 2)
        extra_tons      = round(optimized_total - normal_total, 2)

        # Companion explanation
        if cc:
            companion_note = f"Companion crop ({companion_crop.title()}) adds soil health benefits and {'fixes nitrogen' if any(k in cc for k in ['soybean','chickpea','lentil','beans','pigeon','clover']) else 'repels pests or improves spacing efficiency'}."
        else:
            companion_note = "No companion crop selected. Adding a compatible companion crop can improve yield by an additional 5–8%."

        report = (
            f"📊 YIELD COMPARISON REPORT\n"
            f"{'─'*38}\n"
            f"Farmer Land Size   : {land_size} acres\n"
            f"Primary Crop       : {main_crop.title()}\n"
            f"Companion Crop     : {companion_crop.title() if cc else 'None'}\n"
            f"{'─'*38}\n\n"
            f"✅ Optimized Layout Yield : {optimized_yield_per_acre} tons/acre  ({optimized_total} tons total)\n"
            f"⚠️  Normal Layout Yield   : {normal_yield_per_acre} tons/acre  ({normal_total} tons total)\n\n"
            f"📈 Yield Improvement : +{improvement_pct}%\n"
            f"🌾 Extra Produce     : +{extra_tons} tons over your entire farm\n\n"
            f"{'─'*38}\n"
            f"💡 Why Optimized Layout Wins:\n"
            f"The hexagonal staggered planting reduces plant competition for sunlight and water, "
            f"improving air circulation and reducing disease spread. {companion_note}\n\n"
            f"👨‍🌾 Farmer Tip: Proper row spacing and intercropping alone can add ₹{int(extra_tons * 15000):,} "
            f"to your seasonal income (at ₹15,000/ton average market rate)."
        )
        return report


class OrchestratorAgent:
    # Orchestrator handles delegating the tasks using session context maps within Flask routing
    def __init__(self):
        self.active_sessions = {}
        
    def route_request(self, intent, data):
        if intent == 'signup':
            return UserAuthAgent.signup_user(data['email'], data['password'])
        elif intent == 'login':
            return UserAuthAgent.login_user(data['email'], data['password'])
        elif intent == 'intake':
            return IntakeAgent.process_intake(**data)
        elif intent == 'recommendation':
            return CropRecommendationAgent.recommend(**data)
        elif intent == 'plan':
            return CropPlannerAgent.generate_plan(**data)
        elif intent == 'spatial_plan':
            return SpatialPlannerAgent.generate_layout(
                data.get('farmer_id', 0), 
                data.get('width', 800), 
                data.get('height', 500), 
                data.get('main_crop', 'Auto'),
                data.get('layout_preference', 'Grid Layout'),
                data.get('acres', None)
            )
        elif intent == 'yield_comparison':
            return YieldComparisonAgent.compare(
                float(data.get('land_size', 1)),
                data.get('main_crop', 'Rice'),
                data.get('companion_crop', 'None')
            )
        elif intent == 'chat':
            from agents.hf_agent import hf_agent_chat
            return hf_agent_chat(data['message'], farmer_id=data.get('farmer_id'))
        elif intent == 'diagnose':
            return DiseaseDiagnosisAgent.diagnose(**data)
        elif intent == 'report':
            return ReportAgent.generate_report(**data)
        elif intent == 'weather':
            return WeatherAgent.analyze_weather(**data)
        elif intent == 'send_email':
            return EmailAgent.send_email(data['to_email'], data['subject'], data['body'])
        else:
            return {"error": "Unknown intent"}
