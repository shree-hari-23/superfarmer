#!/usr/bin/env python3
"""
SuperFarmer — Full End-to-End System Documentation & Interview Q&A PDF Generator
=================================================================================
Generates a detailed, professional PDF document covering:
  1. Executive Summary
  2. System Architecture (Multi-Agent Orchestration)
  3. Technology Stack
  4. LLM Tier System (Flux Models via Fluxbase Gateway)
  5. All 12 Agent Deep-Dives (with code-level detail)
  6. Database Schema (Fluxbase Cloud MySQL)
  7. API Routes & Frontend Templates
  8. MCP Server (Model Context Protocol)
  9. Spatial Digital Twin — Neuro-Symbolic Architecture
  10. Evaluation & Benchmarking Suite
  11. Docker & AWS EC2 Deployment
  12. Interview Questions & Answers (30+ Q&A)

Usage:
    python generate_superfarmer_pdf.py
"""

from fpdf import FPDF
import os
import datetime


class SuperFarmerPDF(FPDF):
    """Custom PDF class with professional header/footer and utility methods."""

    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=20)
        self.chapter_num = 0

    # ── Header / Footer ──────────────────────────────────────────────
    def header(self):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, 'SuperFarmer - AI Agricultural Intelligence Platform | System Documentation', align='C')
        self.ln(4)
        self.set_draw_color(34, 139, 34)
        self.set_line_width(0.6)
        self.line(10, 12, 200, 12)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    # ── Utility Methods ──────────────────────────────────────────────
    def chapter_title(self, title):
        self.chapter_num += 1
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(22, 101, 52)  # Dark green
        self.ln(6)
        self.cell(0, 10, self._safe(f'{self.chapter_num}. {title}'), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(34, 139, 34)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(30, 41, 59)
        self.ln(3)
        self.cell(0, 8, self._safe(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_section(self, title):
        self.set_font('Helvetica', 'BI', 11)
        self.set_text_color(71, 85, 105)
        self.cell(0, 7, self._safe(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5.5, self._safe(text))
        self.ln(2)

    def bullet(self, text, indent=15):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 41, 59)
        x = self.get_x()
        self.set_x(x + indent)
        self.cell(4, 5.5, '-')
        self.multi_cell(0, 5.5, self._safe(text))
        self.ln(0.5)

    @staticmethod
    def _safe(text):
        """Strip non-latin1 characters for built-in fonts."""
        if not text:
            return ''
        out = []
        for ch in str(text):
            try:
                ch.encode('latin-1')
                out.append(ch)
            except UnicodeEncodeError:
                out.append('?')
        return ''.join(out)

    def code_block(self, text, width=180):
        self.set_font('Courier', '', 8)
        self.set_fill_color(248, 250, 252)
        self.set_text_color(51, 65, 85)
        self.set_draw_color(226, 232, 240)
        x = self.get_x()
        y = self.get_y()
        text = self._safe(text)
        lines = text.split('\n')
        line_h = 4
        block_h = len(lines) * line_h + 4
        # Check if we need a page break
        if y + block_h > self.h - 25:
            self.add_page()
            y = self.get_y()
        self.rect(x, y, width, block_h, 'DF')
        self.set_xy(x + 3, y + 2)
        for line in lines:
            self.cell(0, line_h, self._safe(line[:95]))  # truncate long lines
            self.ln(line_h)
            self.set_x(x + 3)
        self.ln(3)

    def table_row(self, cols, widths, bold=False, fill=False):
        self.set_font('Helvetica', 'B' if bold else '', 9)
        if fill:
            self.set_fill_color(220, 252, 231)
        self.set_text_color(30, 41, 59)
        for i, (col, w) in enumerate(zip(cols, widths)):
            self.cell(w, 7, self._safe(str(col)[:int(w/1.8)]), border=1, fill=fill)
        self.ln()

    def qa_block(self, q_num, question, answer):
        """Render an interview Q&A pair."""
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(22, 101, 52)
        self.multi_cell(0, 5.5, self._safe(f'Q{q_num}: {question}'))
        self.ln(1)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5.5, self._safe(f'A: {answer}'))
        self.ln(4)


def build_pdf():
    pdf = SuperFarmerPDF()
    pdf.alias_nb_pages()
    pdf.set_margins(12, 18, 12)

    # ═══════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(22, 101, 52)
    pdf.ln(40)
    pdf.cell(0, 15, 'SuperFarmer', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 10, 'AI Agricultural Intelligence Platform', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_draw_color(34, 139, 34)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(12)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, 'Full End-to-End System Documentation', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, 'with Interview Questions & Answers', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 7, 'Multi-Agent AI System | Neuro-Symbolic Architecture', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, 'Fluxbase AI Gateway | Cloud MySQL | FastAPI | Docker | AWS EC2', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.cell(0, 7, f'Generated: {datetime.datetime.now().strftime("%d %B %Y, %I:%M %p")}', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, 'Author: Hari Vishnu | Built for Indian Farmers', align='C', new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(0, 12, 'Table of Contents', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    toc = [
        ('1.', 'Executive Summary'),
        ('2.', 'System Architecture'),
        ('3.', 'Technology Stack'),
        ('4.', 'LLM Tier System (Flux Models)'),
        ('5.', 'Agent Deep-Dives (All 12 Agents)'),
        ('6.', 'Database Schema (Fluxbase Cloud MySQL)'),
        ('7.', 'API Routes & Frontend'),
        ('8.', 'MCP Server (Model Context Protocol)'),
        ('9.', 'Spatial Digital Twin Architecture'),
        ('10.', 'Evaluation & Benchmarking Suite'),
        ('11.', 'Docker & AWS EC2 Deployment'),
        ('12.', 'Interview Questions & Answers (30+)'),
    ]
    for num, title in toc:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(12, 8, num)
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 1: EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Executive Summary')

    pdf.body_text(
        'SuperFarmer is a production-grade, AI-powered agricultural intelligence platform built specifically '
        'for Indian farmers. It combines multi-agent AI orchestration, cloud-native database services, '
        'real-time weather APIs, computer vision for disease diagnosis, and a neuro-symbolic spatial '
        'digital twin to deliver comprehensive, hyper-local farming intelligence.'
    )
    pdf.body_text(
        'The system is designed around a Multi-Agent Architecture where 12 specialized agents handle '
        'distinct agricultural domains: user authentication, farmer intake, crop recommendation, crop '
        'planning, disease diagnosis, weather analysis, spatial farm layout, yield comparison, '
        'multilingual chat, report generation, email automation, and MCP data exposure.'
    )

    pdf.section_title('Key Highlights')
    highlights = [
        '12 specialized AI agents orchestrated by a central OrchestratorAgent',
        '4-tier LLM model system: flux-flash, flux-pro, flux-omni, flux-ultra',
        'Fluxbase AI Gateway for unified model dispatch (OpenAI-compatible API)',
        'Fluxbase Cloud MySQL database accessed via REST API (zero local DB)',
        'Computer vision disease diagnosis using Gemini 2.5 Flash native vision',
        'Neuro-symbolic Spatial Digital Twin with deterministic hex-grid + AI rationale',
        '200-case ICAR-aligned crop recommendation benchmark (76.7% Top-3 accuracy)',
        'Multilingual support: 10 Indian languages + English',
        'MCP (Model Context Protocol) server for external AI agent integration',
        'Production-ready Docker deployment for AWS EC2',
    ]
    for h in highlights:
        pdf.bullet(h)

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 2: SYSTEM ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('System Architecture')

    pdf.body_text(
        'SuperFarmer follows a Multi-Agent Orchestration pattern. The browser sends HTTP requests to '
        'a FastAPI backend (app.py). The OrchestratorAgent receives intent-tagged requests and routes '
        'them to the appropriate specialized agent. Each agent is a self-contained Python class with '
        'static methods, ensuring stateless, horizontally-scalable request handling.'
    )

    pdf.section_title('Architecture Flow')
    pdf.code_block(
        'Browser (HTML/JS/CSS)\n'
        '  |\n'
        '  v\n'
        'FastAPI (app.py) -- SessionMiddleware (Starlette)\n'
        '  |\n'
        '  +-- OrchestratorAgent.route_request(intent, data)\n'
        '  |     |\n'
        '  |     +-- UserAuthAgent        --> Fluxbase Cloud DB (users)\n'
        '  |     +-- IntakeAgent          --> Fluxbase Cloud DB (farmer_profile)\n'
        '  |     +-- CropRecAgent         --> flux-pro (Structured Output)\n'
        '  |     +-- CropPlannerAgent     --> flux-pro (Structured Output)\n'
        '  |     +-- DiseaseDiagAgent     --> flux-omni (Vision) / Gemini 2.5\n'
        '  |     +-- WeatherAgent         --> Tomorrow.io REST API\n'
        '  |     +-- SpatialPlannerAgent  --> Rule Engine + flux-ultra\n'
        '  |     +-- YieldCompAgent       --> Deterministic Rule Engine\n'
        '  |     +-- ChatAgent            --> flux-flash / flux-turbo\n'
        '  |     +-- ReportAgent          --> flux-ultra (Deep Reasoning)\n'
        '  |     +-- EmailAgent           --> Gmail SMTP (async thread)\n'
        '  |\n'
        '  +-- Fluxbase Cloud MySQL (REST API) <-- All DB operations\n'
        '  +-- Tomorrow.io Weather API\n'
        '  +-- Nominatim Geocoder (OpenStreetMap)'
    )

    pdf.section_title('Design Principles')
    principles = [
        'Separation of Concerns: Each agent handles one domain (SRP).',
        'Graceful Degradation: Every AI call has multi-layer fallbacks (Flux -> GLM -> Groq -> Claude -> Rule-based).',
        'Cloud-Native Database: No local MySQL; Fluxbase REST API handles all SQL.',
        'Stateless Agents: All agents use static methods; session state lives in Starlette middleware.',
        'Intent-Based Routing: OrchestratorAgent maps string intents to agent calls.',
    ]
    for p in principles:
        pdf.bullet(p)

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 3: TECHNOLOGY STACK
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Technology Stack')

    pdf.section_title('Backend')
    stack_items = [
        ('Python 3.12', 'Core application language'),
        ('FastAPI', 'ASGI web framework with async support'),
        ('Uvicorn', 'Lightning-fast ASGI server'),
        ('Jinja2', 'Server-side HTML template rendering'),
        ('Starlette SessionMiddleware', 'Cookie-based session management'),
        ('Werkzeug', 'Password hashing (scrypt/pbkdf2)'),
    ]
    for name, desc in stack_items:
        pdf.bullet(f'{name}: {desc}')

    pdf.section_title('AI / LLM')
    ai_items = [
        ('Fluxbase AI Gateway', 'Unified OpenAI-compatible API proxy for multiple models'),
        ('Google Gemini 2.5 Flash', 'Native vision model for disease diagnosis (fallback)'),
        ('Zhipu AI GLM-4 (Air/Flash/Plus)', 'Text generation, structured output, deep reasoning'),
        ('Groq (Qwen 3.8-27B)', 'Ultra-fast inference at 300+ tok/s'),
        ('Anthropic Claude Haiku 4.5', 'Final fallback tier'),
    ]
    for name, desc in ai_items:
        pdf.bullet(f'{name}: {desc}')

    pdf.section_title('Database & APIs')
    db_items = [
        ('Fluxbase Cloud MySQL', 'Cloud-hosted MySQL accessed via REST POST /api/execute-sql'),
        ('Tomorrow.io v4', 'Hyper-local 3-day weather forecasts'),
        ('OpenStreetMap Nominatim', 'Geocoding (location name to lat/lon)'),
        ('Gmail SMTP', 'Transactional email delivery (welcome/login alerts)'),
    ]
    for name, desc in db_items:
        pdf.bullet(f'{name}: {desc}')

    pdf.section_title('Frontend')
    fe_items = [
        ('HTML5 / CSS3 / JavaScript', 'Custom responsive UI'),
        ('Three.js', '3D spatial twin visualization (client-side)'),
        ('Chart.js', 'Data visualization for yield comparison'),
    ]
    for name, desc in fe_items:
        pdf.bullet(f'{name}: {desc}')

    pdf.section_title('DevOps')
    devops_items = [
        ('Docker', 'Containerized production builds'),
        ('docker-compose', 'Multi-service orchestration'),
        ('AWS EC2', 'Cloud compute deployment target'),
    ]
    for name, desc in devops_items:
        pdf.bullet(f'{name}: {desc}')

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 4: LLM TIER SYSTEM
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('LLM Tier System (Flux Models via Fluxbase Gateway)')

    pdf.body_text(
        'SuperFarmer dispatches all AI inference through a unified function _call_flux() which targets '
        'the Fluxbase AI Gateway. This gateway exposes an OpenAI-compatible /chat/completions endpoint '
        'that transparently routes to the appropriate underlying model. The system organizes models into '
        'functional tiers based on capability requirements.'
    )

    pdf.section_title('Tier Architecture')

    tiers = [
        ('Tier 1: Fast Chat (flux-flash / flux-turbo)',
         'Models: glm-4-flash (Zhipu AI, <100ms) / llama-3.3-70b (Groq, 300+ tok/s)',
         'Use: Multilingual conversational AI chat, quick Q&A',
         'Agent: SuperFarmerChatAgent'),
        ('Tier 2: Structured Output (flux-pro)',
         'Model: glm-4-air (Zhipu AI)',
         'Use: Crop recommendation (JSON array), crop plan generation (JSON object)',
         'Agents: CropRecommendationAgent, CropPlannerAgent'),
        ('Tier 3: Vision Pathology (flux-omni / flux-max)',
         'Models: gemini-2.0-flash (Google Vision) / gpt-4o-mini (OpenAI)',
         'Use: Plant disease diagnosis from leaf photos + text symptoms',
         'Agent: DiseaseDiagnosisAgent'),
        ('Tier 4: Deep Reasoning (flux-ultra / flux-5.2)',
         'Model: glm-4-plus (Zhipu AI)',
         'Use: Spatial twin rationale, field advisory report synthesis',
         'Agents: SpatialPlannerAgent (narrative), ReportAgent'),
    ]

    for title, model, use, agent in tiers:
        pdf.sub_section(title)
        pdf.bullet(model)
        pdf.bullet(use)
        pdf.bullet(agent)
        pdf.ln(2)

    pdf.section_title('Fallback Chain')
    pdf.body_text(
        'The _call_llm() unified dispatcher implements a 4-level fallback chain:\n'
        '1. Primary: Flux model via Fluxbase Gateway (flux-pro/ultra/omni/flash)\n'
        '2. Secondary: Zhipu AI GLM-4-flash (direct API)\n'
        '3. Tertiary: Groq Qwen 3.8-27B (direct API)\n'
        '4. Final: Anthropic Claude Haiku 4.5 (direct API)\n\n'
        'If ALL AI models fail, deterministic rule-based fallbacks produce valid output, '
        'ensuring the system never returns an empty response to the user.'
    )

    pdf.section_title('_call_flux() Implementation')
    pdf.code_block(
        'def _call_flux(model, system_prompt, user_message,\n'
        '               image_b64=None, history=None, timeout=50.0):\n'
        '    url = f"{FLUXBASE_AI_BASE_URL}/chat/completions"\n'
        '    headers = {\n'
        '        "Authorization": f"Bearer {api_key}",\n'
        '        "Content-Type": "application/json"\n'
        '    }\n'
        '    messages = [{role: "system", content: system_prompt}]\n'
        '    if image_b64:\n'
        '        messages.append({role: "user", content: [\n'
        '            {type: "text", text: user_message},\n'
        '            {type: "image_url", image_url: {url: image_b64}}\n'
        '        ]})\n'
        '    payload = {model, messages, temperature: 0.2}\n'
        '    resp = requests.post(url, json=payload, ...)\n'
        '    return choices[0]["message"]["content"]'
    )

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 5: ALL 12 AGENT DEEP-DIVES
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Agent Deep-Dives (All 12 Agents)')

    agents_data = [
        {
            'name': 'OrchestratorAgent',
            'file': 'agents/agents.py (line 2782)',
            'intent': 'All intents',
            'llm': 'None (routing only)',
            'desc': (
                'Central dispatcher that receives (intent, data) tuples from FastAPI routes '
                'and delegates to the appropriate specialized agent. Implements a simple '
                'if/elif chain mapping intent strings (signup, login, intake, recommendation, '
                'plan, diagnose, weather, spatial_plan, yield_comparison, chat, report, send_email) '
                'to static method calls on specialized agents. Stateless design with an '
                'active_sessions dict for future session tracking.'
            ),
        },
        {
            'name': 'UserAuthAgent',
            'file': 'agents/agents.py (line 416)',
            'intent': 'signup, login',
            'llm': 'None',
            'desc': (
                'Handles user registration and login. signup_user() hashes the password using '
                'Werkzeug generate_password_hash() (scrypt/pbkdf2) and INSERTs into the users '
                'table in Fluxbase. login_user() SELECTs the user by email and verifies the '
                'password using a multi-format _verify_password() function that supports: '
                'bcrypt ($2a$/$2b$), Werkzeug scrypt/pbkdf2, and legacy plaintext fallback. '
                'Also provides get_farmer_profile_by_user() and get_user_email() helpers.'
            ),
        },
        {
            'name': 'IntakeAgent',
            'file': 'agents/agents.py (line 478)',
            'intent': 'intake',
            'llm': 'None',
            'desc': (
                'Captures farmer profile data (name, land_size, location, water_availability, '
                'farming_goals) and INSERTs into the farmer_profile table. Converts land_size '
                'to float, sanitizes all string inputs via safe_str() to prevent SQL injection. '
                'Returns the newly created farmer_id by querying with ORDER BY farmer_id DESC LIMIT 1.'
            ),
        },
        {
            'name': 'CropRecommendationAgent',
            'file': 'agents/agents.py (line 504)',
            'intent': 'recommendation',
            'llm': 'flux-pro (Structured Output Tier)',
            'desc': (
                'Analyzes soil parameters (soil_type, NPK, temperature, rainfall, water_availability) '
                'and recommends the Top 3 most suitable crops. The primary path calls flux-pro '
                'with a structured JSON prompt asking for crop name, suitability_score, '
                'why_recommended, key_features, nutritional_importance, growing_tips, ideal_season, '
                'expected_yield, and water_need. The response is parsed with regex JSON extraction. '
                'If flux-pro fails, it cascades through flux-turbo -> flux-flash -> _call_llm() -> '
                'rule-based fallback. The rule-based fallback uses hardcoded agronomy logic based '
                'on soil type, water availability, and NPK thresholds. Auto-heals missing '
                'farmer_profile rows (INSERT before crop_recommendations to satisfy FK constraint). '
                'Also logs soil records to soil_records table.'
            ),
        },
        {
            'name': 'CropPlannerAgent',
            'file': 'agents/agents.py (line 725)',
            'intent': 'plan',
            'llm': 'flux-pro (Structured Output Tier)',
            'desc': (
                'Generates a full crop management plan for a given crop. Calls flux-pro with a '
                'prompt requesting JSON with 5 fields: sowing_schedule, irrigation_plan, '
                'fertilizer_schedule, pest_alerts, harvest_timeline. Includes a _sanitize_crop_name() '
                'method that handles long AI-generated text by scanning for known crop names. '
                'Stores the plan in crop_plans table. Falls back to static default plans if AI fails.'
            ),
        },
        {
            'name': 'DiseaseDiagnosisAgent',
            'file': 'agents/agents.py (line 851)',
            'intent': 'diagnose',
            'llm': 'flux-omni / flux-max (Vision Tier)',
            'desc': (
                'Diagnoses plant diseases from text symptoms AND/OR uploaded leaf images. '
                'The image path: reads the uploaded file, base64-encodes it, and sends it as '
                'an image_url in the OpenAI-compatible multimodal message format. Tries '
                'flux-omni first (Google Gemini vision via Fluxbase), then flux-max (GPT-4o-mini). '
                'Falls back to Gemini 2.5 Flash native Python SDK vision, then Groq/Claude '
                'text-only mode. Returns structured JSON with diagnosis, confidence, treatment, '
                'prevention, and product recommendations with Amazon/Flipkart buy links.'
            ),
        },
        {
            'name': 'WeatherAgent',
            'file': 'agents/agents.py (line 216)',
            'intent': 'weather',
            'llm': 'None (API-driven)',
            'desc': (
                'Fetches 3-day hyper-local weather forecasts using Tomorrow.io v4 API. '
                'Auto-geocodes location names to lat/lon using OpenStreetMap Nominatim. '
                'Processes daily timelines for temperatureMax and precipitationProbabilityMax. '
                'Generates rule-based suggestions: heavy rain -> harvest early, moderate rain -> '
                'hold irrigation, extreme heat (>38C) -> increase irrigation, clear -> grow normally.'
            ),
        },
        {
            'name': 'SpatialPlannerAgent',
            'file': 'agents/agents.py (line 1685)',
            'intent': 'spatial_plan',
            'llm': 'flux-ultra (Deep Reasoning) for narrative; Rule Engine for geometry',
            'desc': (
                'Generates a personalized 2D/3D hexagonal farm layout (Digital Twin). This is a '
                'NEURO-SYMBOLIC system: geometry (hex placement, zone division, border crops, '
                'sunlight orientation) is 100% deterministic via Python rule engine. AI (flux-ultra) '
                'generates only the narrative rationale text. Includes CROP_DB (16 crops with '
                'spacing, height, water, nitrogen, companion_score), COMPANION_MATRIX (compatibility), '
                'Memory Fetch (queries Fluxbase for prev crop, nitrogen level, water), Decision Rules '
                '(crop rotation, nitrogen fixing, water matching), Zone Division (strip/row/grid), '
                'Hex Layout (staggered hex placement), Border Crops (Marigold pest barrier ring), '
                'Quality Score, and Yield Estimation. Logs to spatial_twin_log table.'
            ),
        },
        {
            'name': 'YieldComparisonAgent',
            'file': 'agents/agents.py (line 2690)',
            'intent': 'yield_comparison',
            'llm': 'None (Deterministic Rule Engine)',
            'desc': (
                'Compares optimized intercropping yield vs normal monoculture yield. Uses hardcoded '
                'BASE_YIELDS (tons/acre) for 23 Indian crops and COMPANION_BONUS (5-8% synergy) '
                'for nitrogen-fixing and pest-suppressing companions. Calculates intercrop boost '
                '(15% base + companion bonus, capped at 30%), normal penalty (10%), and generates '
                'a detailed yield report with total tons, improvement %, and estimated income delta '
                'at Rs 15,000/ton market rate.'
            ),
        },
        {
            'name': 'SuperFarmerChatAgent',
            'file': 'agents/agents.py (line ~2500)',
            'intent': 'chat',
            'llm': 'flux-flash / flux-turbo (Fast Chat Tier)',
            'desc': (
                'Multilingual conversational advisor supporting 10 Indian languages (Hindi, Bengali, '
                'Telugu, Marathi, Tamil, Gujarati, Kannada, Punjabi, Odia, Malayalam) plus English. '
                'Builds a comprehensive farmer context by querying Fluxbase for farmer profile, '
                'latest soil records, active crop plan, nutrient risk log, and past crop '
                'recommendations. Injects a MANDATORY LANGUAGE DIRECTIVE into the system prompt '
                'to force the LLM to respond in the selected language and script.'
            ),
        },
        {
            'name': 'ReportAgent',
            'file': 'agents/agents.py (line 996)',
            'intent': 'report',
            'llm': 'flux-ultra (Deep Reasoning)',
            'desc': (
                'Generates a structured 7-section Field Advisory Report by pulling authentic data '
                'from Fluxbase: (1) Farmer & Farm Details from farmer_profile, (2) Soil NPK from '
                'soil_records, (3) Crop Recommendations from crop_recommendations, (4) Active Crop '
                'Plan from crop_plans, (5) Spatial Twin from spatial_twin_log, (6) Yield metrics '
                'from _calculate_yield_metrics(), (7) AI Insights from _generate_grounded_insights(). '
                'Also generates a professionally styled HTML email version via build_html_email(). '
                'Saves report text to reports table.'
            ),
        },
        {
            'name': 'EmailAgent',
            'file': 'agents/agents.py (line 302)',
            'intent': 'send_email',
            'llm': 'None',
            'desc': (
                'Sends transactional emails via Gmail SMTP (port 587, STARTTLS). Auto-discovers '
                'notification logo from images/ directory. Creates RFC 2387 multipart/related '
                'messages with inline logo (Content-ID: superfarmer_logo), HTML body, and plaintext '
                'fallback. Used for welcome emails on signup and security alerts on login. '
                'Called asynchronously via threading.Thread in app.py.'
            ),
        },
    ]

    for agent in agents_data:
        pdf.section_title(f'{agent["name"]}')
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, f'File: {agent["file"]}  |  Intent: {agent["intent"]}  |  LLM: {agent["llm"]}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.body_text(agent['desc'])

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 6: DATABASE SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Database Schema (Fluxbase Cloud MySQL)')

    pdf.body_text(
        'SuperFarmer uses Fluxbase Cloud MySQL accessed entirely via REST API. All SQL queries are '
        'sent as HTTP POST requests to https://fluxbase.vercel.app/api/execute-sql with the project ID '
        'and API key. This eliminates the need for any local MySQL installation.'
    )

    pdf.section_title('config.py - Database Connection')
    pdf.code_block(
        'FLUXBASE_URL = "https://fluxbase.vercel.app/api/execute-sql"\n'
        '\n'
        'def execute_fluxbase_sql(query):\n'
        '    headers = {"Authorization": f"Bearer {API_KEY}"}\n'
        '    payload = {"projectId": PROJECT_ID, "query": query}\n'
        '    resp = requests.post(URL, json=payload, headers=headers)\n'
        '    data = resp.json()\n'
        '    return data.get("result", {})'
    )

    tables = [
        ('users', 'user_id (PK), email (UNIQUE), password_hash, created_at', 'User authentication'),
        ('farmer_profile', 'farmer_id (PK), user_id (FK), name, land_size, location, water_availability, farming_goals, created_at', 'Farmer intake data'),
        ('soil_records', 'record_id (PK), farmer_id (FK), soil_type, nitrogen, phosphorus, potassium, soil_moisture, temperature, recorded_at', 'Historical soil NPK readings'),
        ('crop_recommendations', 'recommendation_id (PK), farmer_id (FK), recommended_crops, created_at', 'AI-generated crop suggestions'),
        ('crop_plans', 'plan_id (PK), farmer_id (FK), crop_name, sowing_schedule, irrigation_plan, fertilizer_schedule, pest_alerts, harvest_timeline, status, created_at', 'Crop management plans'),
        ('nutrient_risk_log', 'log_id (PK), farmer_id (FK), plan_id (FK), risk_probability, risk_level, suggested_action, logged_at', 'ML nutrient risk predictions'),
        ('reports', 'report_id (PK), farmer_id (FK), report_text, generated_at', 'Generated advisory reports'),
        ('session_logs', 'session_id (PK), farmer_id (FK), interaction_log, session_date', 'Chat interaction history'),
        ('spatial_twin_log', 'id (PK), farmer_id, main_crop, companion_crop, layout_mode, layout_score, soil_impact, total_yield_t, created_at', 'Spatial twin generation logs'),
    ]

    pdf.section_title('Tables')
    for tname, cols, purpose in tables:
        pdf.sub_section(f'{tname}')
        pdf.bullet(f'Purpose: {purpose}')
        pdf.bullet(f'Columns: {cols}')
        pdf.ln(2)

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 7: API ROUTES
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('API Routes & Frontend')

    pdf.body_text(
        'All routes are defined in app.py using FastAPI decorators. Each route renders a Jinja2 '
        'template on GET and processes form submissions on POST, delegating to the OrchestratorAgent.'
    )

    routes = [
        ('GET', '/', 'Home page (landing)'),
        ('GET/POST', '/signup', 'User registration with password hashing + welcome email'),
        ('GET/POST', '/login', 'User login with session creation + login alert email'),
        ('GET', '/logout', 'Clear session cookies'),
        ('GET/POST', '/intake', 'Farmer profile setup form'),
        ('GET/POST', '/recommendation', 'Crop recommendation with soil parameters'),
        ('GET/POST', '/plan', 'Crop management plan generation'),
        ('GET/POST', '/disease', 'Disease diagnosis (text + image upload)'),
        ('GET/POST', '/weather', 'Weather forecast with location geocoding'),
        ('GET/POST', '/spatial-planner', 'Digital twin spatial layout (JSON API)'),
        ('GET/POST', '/yield-comparison', 'Yield comparison report'),
        ('GET', '/report', 'Field advisory report generation'),
        ('GET', '/benchmarks', 'Evaluation benchmark results dashboard'),
        ('POST', '/api/chat', 'Multilingual chat API endpoint'),
    ]

    widths = [25, 40, 120]
    pdf.table_row(['Method', 'Path', 'Description'], widths, bold=True, fill=True)
    for method, path, desc in routes:
        pdf.table_row([method, path, desc], widths)

    pdf.section_title('Frontend Templates')
    pdf.body_text(
        'All templates extend base.html and use Jinja2 template inheritance. Each template uses '
        'a url_for() helper mapped in app.py that mimics Flask routing. The CSS is loaded from '
        'static/css/style.css. Three.js is loaded via CDN for 3D spatial twin visualization.'
    )

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 8: MCP SERVER
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('MCP Server (Model Context Protocol)')

    pdf.body_text(
        'farmer_mcp_server.py exposes a FastMCP stdio server that allows external AI agents '
        '(such as Claude Desktop or VS Code Copilot) to query farmer profile data from Fluxbase. '
        'This follows the Model Context Protocol standard.'
    )

    pdf.section_title('Implementation')
    pdf.code_block(
        'from mcp.server.fastmcp import FastMCP\n'
        'from config import execute_fluxbase_sql\n'
        '\n'
        'mcp = FastMCP("FarmerProfile")\n'
        '\n'
        '@mcp.tool()\n'
        'def get_farmer_profile(farmer_id: int) -> str:\n'
        '    """Fetch farmer profile from Fluxbase."""\n'
        '    res = execute_fluxbase_sql(\n'
        '        f"SELECT * FROM farmer_profile "\n'
        '        f"WHERE farmer_id={farmer_id}"\n'
        '    )\n'
        '    return json.dumps(res["rows"][0])\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    mcp.run(transport="stdio")'
    )

    pdf.section_title('Use Cases')
    pdf.bullet('SpatialPlannerAgent uses MCP to fetch farmer context for personalized layouts')
    pdf.bullet('External AI assistants can query farmer data as a tool call')
    pdf.bullet('Enables composable AI agent pipelines (A2A interoperability)')

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 9: SPATIAL DIGITAL TWIN
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Spatial Digital Twin Architecture')

    pdf.body_text(
        'The Spatial Digital Twin is the most architecturally complex agent in SuperFarmer. '
        'It implements a NEURO-SYMBOLIC architecture where:'
    )
    pdf.bullet('SYMBOLIC (Deterministic): Hex-grid geometry, zone division, border crops, spacing, sunlight orientation, quality scoring, yield estimation are ALL computed by Python rule engine.')
    pdf.bullet('NEURAL (AI-Generated): Narrative rationale text explaining WHY the layout was chosen is synthesized by flux-ultra LLM.')
    pdf.ln(2)

    pdf.section_title('Rule Engine Components')

    pdf.sub_section('A. CROP_DB (16 Crops)')
    pdf.body_text(
        'Each crop has: name, color (hex), emoji, spacing (cm), height_m, water requirement, '
        'nitrogen role (Consumer/Fixer/Neutral), shade tolerance, profit_score, companion_score, '
        'and yield_t_per_acre. Example: Corn = {spacing: 60cm, height: 2.5m, water: Medium, '
        'nitrogen: Consumer, companion_score: 8, yield: 2.8 t/acre}.'
    )

    pdf.sub_section('B. COMPANION_MATRIX')
    pdf.body_text(
        'Defines compatible companion crops for each main crop. Example: Corn -> [Soybean, '
        'Groundnut, Marigold, Pumpkin]. Used for automatic companion selection based on '
        'companion_score ranking.'
    )

    pdf.sub_section('C. Memory Fetch (_fetch_farmer_memory)')
    pdf.body_text(
        'Queries Fluxbase for: previous season crop (crop_plans), inferred nitrogen level '
        '(crop_recommendations), water availability (farmer_profile), and past yield '
        '(spatial_twin_log). Returns a memory dict used by decision rules.'
    )

    pdf.sub_section('D. Decision Rules (_run_decision_rules)')
    pdf.body_text(
        'Step 1: Analyze memory (prev crop, nitrogen, water). '
        'Step 2A: Crop rotation rule - if same crop repeated, force N-fixing companion. '
        'Step 2B: Nitrogen rule - if soil N is Low, select N-fixing companion. '
        'Step 2C: Water matching rule - if farm has Low water but crop needs High, '
        'override to drought-tolerant alternative. '
        'Step 3: Soil impact assessment (improves/degrades/neutral).'
    )

    pdf.sub_section('E. Hex Layout Generation')
    pdf.body_text(
        'hex_layout() places plant nodes in a staggered hexagonal pattern within each zone. '
        'Odd rows are offset by half the spacing value. Node attributes include x, y, type, '
        'color, radius, row, col, height_m, and zone index. Supports Strip, Row, Grid, '
        'and Auto layout modes.'
    )

    pdf.sub_section('F. Border Crop Ring (Marigold)')
    pdf.body_text(
        'Automatically adds a Marigold pest barrier ring around the entire field perimeter '
        '(top, bottom, left, right edges) unless Marigold is already the main or companion crop.'
    )

    pdf.sub_section('G. Quality Score')
    pdf.body_text(
        'Calculated from: base 50 + companion_score * 2 + spacing efficiency + nitrogen synergy '
        '+ height difference bonus + water match bonus. Capped at 100.'
    )

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 10: EVALUATION & BENCHMARKING
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Evaluation & Benchmarking Suite')

    pdf.body_text(
        'SuperFarmer includes a reproducible evaluation harness in evaluation/ with ICAR-aligned '
        'test cases covering crop recommendation and disease diagnosis accuracy.'
    )

    pdf.section_title('Crop Recommendation Benchmark')
    pdf.bullet('Test Set: 200 diverse Indian farming scenarios across 5 major soil types')
    pdf.bullet('Soil Types: Black (44), Alluvial (33), Red (39), Sandy (54), Laterite (30)')
    pdf.bullet('Engine: flux-pro via Fluxbase AI Gateway')
    pdf.bullet('Top-1 Accuracy: 20.0% (40/200)')
    pdf.bullet('Top-3 Accuracy: 76.7% (153/200)')
    pdf.bullet('100% Top-3 on: Cotton, Groundnut, Rice, Soybean, Sunflower, Wheat')
    pdf.ln(2)

    pdf.section_title('Disease Diagnosis Benchmark')
    pdf.bullet('Test Set: 20 symptom cases across 14 Indian crops')
    pdf.bullet('Engine: DiseaseDiagnosisAgent via flux-omni / flux-max')
    pdf.bullet('Match Accuracy: 80.0% (16/20)')
    pdf.bullet('Metric: difflib SequenceMatcher similarity with threshold = 0.40')
    pdf.ln(2)

    pdf.section_title('How to Run')
    pdf.code_block(
        '# Crop Recommendation Benchmark\n'
        'python evaluation/evaluate_crop_recommendation.py\n'
        '\n'
        '# With rule-engine comparison\n'
        'python evaluation/evaluate_crop_recommendation.py --engine=rules\n'
        '\n'
        '# Disease Diagnosis Benchmark\n'
        'python evaluation/evaluate_disease_diagnosis.py'
    )

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 11: DEPLOYMENT
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Docker & AWS EC2 Deployment')

    pdf.section_title('Dockerfile')
    pdf.code_block(
        'FROM python:3.12-slim\n'
        'WORKDIR /app\n'
        'COPY requirements.txt .\n'
        'RUN pip install --no-cache-dir -r requirements.txt\n'
        'COPY . .\n'
        'EXPOSE 5000\n'
        'CMD ["uvicorn", "app:app", "--host", "0.0.0.0",\n'
        '     "--port", "5000"]'
    )

    pdf.section_title('docker-compose.yml')
    pdf.code_block(
        'version: "3.8"\n'
        'services:\n'
        '  web:\n'
        '    build: .\n'
        '    ports: ["5000:5000"]\n'
        '    env_file: .env\n'
        '    restart: unless-stopped'
    )

    pdf.section_title('AWS EC2 Deployment Steps')
    steps = [
        'Launch EC2 instance (Ubuntu 22.04 LTS, t3.medium recommended)',
        'SSH into instance and install Docker + Docker Compose',
        'Clone the repository or SCP the project files',
        'Create .env file with all API keys',
        'Run: docker-compose up -d --build',
        'Configure Security Group: open port 5000 (or 80 with nginx proxy)',
        'Access at http://<EC2-PUBLIC-IP>:5000',
    ]
    for i, step in enumerate(steps, 1):
        pdf.bullet(f'Step {i}: {step}')

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 12: INTERVIEW QUESTIONS & ANSWERS
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Interview Questions & Answers')

    pdf.body_text(
        'This section contains 35+ technical interview questions and answers covering all aspects '
        'of the SuperFarmer system. Use these to prepare for portfolio defense, technical interviews, '
        'and system design discussions.'
    )

    qa_pairs = [
        # Architecture & Design
        (
            'What is the overall architecture of SuperFarmer?',
            'SuperFarmer uses a Multi-Agent Orchestration architecture. A FastAPI backend receives HTTP requests and routes them via an OrchestratorAgent to 12 specialized agents. Each agent handles a specific domain (auth, crop recommendation, disease diagnosis, etc.) using static methods for stateless, scalable processing. The database is Fluxbase Cloud MySQL accessed via REST API, and all LLM inference goes through the Fluxbase AI Gateway.'
        ),
        (
            'Why did you choose a multi-agent pattern instead of a monolithic AI approach?',
            'Multi-agent separation enables: (1) Each agent can use a different LLM tier optimized for its task (fast chat vs. vision vs. deep reasoning), (2) Independent testing and debugging per agent, (3) Graceful degradation - if one agent fails, others continue working, (4) Rule-based fallbacks per agent rather than system-wide failure, (5) Cleaner code organization with single responsibility per agent class.'
        ),
        (
            'How does the OrchestratorAgent work?',
            'The OrchestratorAgent receives an (intent, data) tuple from each FastAPI route. It uses a simple if/elif chain to map intent strings (e.g., "recommendation", "diagnose", "spatial_plan") to static method calls on the appropriate agent class. This is a lightweight dispatcher - no ML model or NLU is used for routing since intents are determined by which URL the user visits.'
        ),
        # LLM & AI
        (
            'Explain the 4-tier LLM model system.',
            'Tier 1 (flux-flash/turbo): Fast chat models (GLM-4-flash <100ms, LLaMA 3.3 300+ tok/s) for multilingual conversational AI. Tier 2 (flux-pro): Structured output models (GLM-4-air) for crop recommendation and crop planning requiring JSON responses. Tier 3 (flux-omni/max): Vision-capable models (Gemini 2.0 Flash, GPT-4o-mini) for plant disease diagnosis from leaf photos. Tier 4 (flux-ultra): Deep reasoning models (GLM-4-plus) for spatial twin rationale and field advisory reports.'
        ),
        (
            'How does the fallback chain work when an LLM fails?',
            'The _call_llm() function implements a 4-level cascade: (1) Try the primary Flux model via Fluxbase Gateway, (2) Try GLM-4-flash directly via Zhipu AI API, (3) Try Groq Qwen 3.8-27B, (4) Try Anthropic Claude Haiku 4.5. If ALL LLM calls fail, each agent has its own deterministic rule-based fallback that produces valid output. For example, CropRecommendationAgent falls back to hardcoded agronomy rules based on soil type, NPK values, and water availability.'
        ),
        (
            'What is the Fluxbase AI Gateway and why use it?',
            'Fluxbase AI Gateway is a unified API proxy that exposes an OpenAI-compatible /chat/completions endpoint. It routes requests to different underlying models (GLM-4, Gemini, GPT-4o-mini) based on the model parameter. Benefits: (1) Single API key for all models, (2) Consistent request/response format, (3) Easy model switching without code changes, (4) Centralized rate limiting and monitoring.'
        ),
        # Disease Diagnosis
        (
            'How does the DiseaseDiagnosisAgent handle image uploads?',
            'When a user uploads a leaf photo, the agent: (1) Reads the file bytes from the UploadFile object, (2) Base64-encodes the image, (3) Constructs an OpenAI-compatible multimodal message with type:image_url containing the base64 data URI, (4) Sends it to flux-omni (Gemini vision) via the Fluxbase Gateway. If flux-omni fails, it falls back to native Gemini 2.5 Flash Python SDK with PIL.Image, then to text-only Groq/Claude modes.'
        ),
        (
            'What does the disease diagnosis JSON output include?',
            'The structured JSON includes: diagnosis (disease name), confidence (High/Medium/Low or percentage), treatment (organic-first action steps), prevention (next-season measures), and products array with name, type (Fungicide/Pesticide/Bio-stimulant), dose, and auto-generated Amazon.in and Flipkart.com search URLs for direct purchase links.'
        ),
        # Spatial Twin
        (
            'Is the Spatial Digital Twin rule-based or AI-generated?',
            'It is a NEURO-SYMBOLIC hybrid. The geometry and layout are 100% deterministic: hex-grid placement, zone division, border crops, spacing calculations, quality scoring, and yield estimation are all computed by Python rule engine classes. Only the narrative rationale text (explaining WHY the layout was chosen) is generated by flux-ultra LLM. This ensures reproducible, consistent layouts while still providing human-readable AI explanations.'
        ),
        (
            'Explain the crop rotation decision rule in the Spatial Twin.',
            'The _run_decision_rules() method checks if the users selected crop matches their previous seasons crop (from Fluxbase crop_plans table). If so, it triggers a Crop Rotation Risk warning and forces a nitrogen-fixing companion (from COMPANION_MATRIX filtered by N_FIXERS set) to counteract soil depletion from monoculture. The companion is selected by highest companion_score.'
        ),
        (
            'How does the water matching rule work?',
            'If the farmers water_availability is "Low" but the selected crop is in _HIGH_WATER_CROPS (Rice, Sugarcane, Tomato), the system overrides the crop selection to a drought-tolerant alternative from _DRY_FALLBACKS (Wheat, Chickpea, Groundnut, Mustard, Soybean). The user sees a warning explaining the override reason.'
        ),
        (
            'How is the hex layout generated?',
            'The hex_layout() method places plant nodes in a staggered hexagonal grid within a rectangular zone. For each row, if the row index is odd, nodes are offset by half the spacing value horizontally (creating the hex pattern). Each node stores x, y coordinates, crop type, color, radius (spacing * 0.32), row/col indices, and height_m for 3D rendering.'
        ),
        (
            'What is the Marigold border ring?',
            'If neither the main crop nor the companion is Marigold, the system automatically generates a ring of Marigold nodes around the entire field perimeter (top, bottom, left, right edges at 8px margin). Marigolds serve as a biological pest barrier, and this demonstrates the systems integrated pest management approach.'
        ),
        # Database
        (
            'Why Fluxbase instead of a local MySQL database?',
            'Fluxbase provides cloud-hosted MySQL accessible via a simple REST API (POST /api/execute-sql). Benefits: (1) Zero local database installation or management, (2) Works identically in development and production, (3) Built-in caching (SELECT queries cached 15 seconds), (4) Rate limiting (30 requests/10 seconds), (5) Single source of truth accessible from any deployment. The only dependency is an API key and project ID.'
        ),
        (
            'How do you prevent SQL injection?',
            'The safe_str() utility function escapes single quotes by replacing them with doubled single quotes. Additionally, numeric values are cast to int/float before interpolation. While parameterized queries would be ideal, the REST API interface requires string SQL, so input sanitization is the primary defense.'
        ),
        (
            'How does the auto-profile healing work?',
            'Before inserting into crop_recommendations or crop_plans (which have FK to farmer_profile), the agent checks if the farmer_id exists in farmer_profile. If not, it auto-creates a minimal profile with default values (name: "Farmer N", land: 1.0 acre, location: "India", water: "Medium"). This prevents FK constraint violations when a farmer_id is used before intake.'
        ),
        # Weather
        (
            'How does the WeatherAgent generate actionable advice?',
            'After fetching 3-day forecasts from Tomorrow.io, the agent applies rule-based thresholds: if total rain probability > 100 across 3 days, recommend early harvest. If > 50, hold off manual irrigation. If max temperature > 38C, increase irrigation for heat stress. Otherwise, let crop grow normally. The advice is deterministic and does not use any LLM.'
        ),
        # Chat
        (
            'How does multilingual support work in the chat agent?',
            'The SuperFarmerChatAgent supports 10 Indian languages via a LANGUAGE_MAP. When a user selects a language (e.g., "hi-IN" for Hindi), the agent injects a MANDATORY LANGUAGE DIRECTIVE into both the system prompt and user message, forcing the LLM to respond entirely in Hindi Devanagari script. The directive is repeated at both start and end of the system prompt to ensure compliance.'
        ),
        (
            'What farmer context does the chat agent use?',
            '_build_farmer_context() queries Fluxbase for: farmer profile (name, location, land, water), latest soil records (NPK, temperature), active crop plan (sowing, irrigation, fertilizer, harvest), nutrient risk log, and past crop recommendations. This context is injected into the system prompt so the LLM gives personalized, farm-specific advice.'
        ),
        # Report
        (
            'What are the 7 sections of the Field Advisory Report?',
            'Section 1: Farmer & Farm Details (from farmer_profile). Section 2: Crop Recommendations (from crop_recommendations). Section 3: Active Crop Plan (from crop_plans). Section 4: Spatial Twin Layout (from spatial_twin_log). Section 5: Yield & Farm Efficiency (calculated metrics). Section 6: AI Insights & Grounded Recommendations (rule-based + context-aware). Section 7: System Limitations & Advisory Notes (transparency disclosures).'
        ),
        (
            'How are the AI insights in the report generated?',
            'The _generate_grounded_insights() method uses only real farmer data (NO hallucinated weather or external data). It analyzes: (1) Soil NPK levels to recommend nitrogen management, (2) Crop plan sowing/irrigation schedules, (3) Spatial twin intercropping synergy, and (4) Recent disease diagnoses. All insights reference actual stored values, ensuring factual grounding.'
        ),
        # Email
        (
            'How does the email system work?',
            'EmailAgent uses Gmail SMTP (port 587, STARTTLS) with app passwords. It creates RFC 2387 multipart/related messages with: inline logo image (Content-ID: superfarmer_logo), HTML body with styled sections, and plaintext fallback. Emails are sent asynchronously via threading.Thread so they dont block the HTTP response.'
        ),
        # MCP
        (
            'What is MCP and how is it used?',
            'MCP (Model Context Protocol) is a standard for exposing data tools to AI agents. farmer_mcp_server.py uses FastMCP to create a stdio server that exposes a get_farmer_profile(farmer_id) tool. External AI agents (like Claude Desktop) can call this tool to fetch farmer data from Fluxbase. SpatialPlannerAgent uses it internally to get farmer context for personalized layouts.'
        ),
        # Evaluation
        (
            'How did you achieve 76.7% Top-3 accuracy?',
            'The 200-case test set covers 5 soil types with realistic NPK, rainfall, and water parameters aligned to ICAR (Indian Council of Agricultural Research) data. We measure Top-3 accuracy because recommending 3 complementary crops (for rotation/intercropping) is standard agronomic practice. The model achieves 100% on staple crops (Cotton, Groundnut, Rice, Soybean, Sunflower, Wheat) and struggles mainly on edge cases where multiple crops are equally suitable.'
        ),
        (
            'Why use Top-3 instead of Top-1 accuracy?',
            'In real agriculture, farmers dont plant a single crop. They need 2-3 options for: (1) Crop rotation across seasons, (2) Intercropping for soil health, (3) Risk diversification against price volatility. A recommendation system that gives 3 good options is more valuable than one that picks a single "best" crop, which is why agronomic benchmarks use Top-3.'
        ),
        (
            'How is disease diagnosis accuracy measured?',
            'We use difflib.SequenceMatcher similarity between the predicted diagnosis and ground truth. A prediction counts as a match if similarity >= 0.40 OR if the ground truth appears as a substring of the prediction. This accounts for variations in how diseases are named (e.g., "Late Blight of Tomato" vs "Phytophthora infestans (Late Blight)").'
        ),
        # Deployment
        (
            'What are the key Docker considerations?',
            'The Dockerfile uses python:3.12-slim for minimal image size. Requirements are installed first (layer caching). The .dockerignore excludes .venv, .git, __pycache__, .env (secrets via env_file), sqlite databases, and evaluation data. The container exposes port 5000 and runs uvicorn directly without reload for production stability.'
        ),
        (
            'How would you scale this for more users?',
            'Horizontal scaling: (1) Stateless agents enable multiple container replicas behind a load balancer. (2) Session data in cookies (not server memory). (3) Fluxbase handles DB scaling. (4) LLM calls are external API-based. Vertical scaling: increase EC2 instance size. For high traffic: add Redis for session/cache, nginx reverse proxy, and potentially move to ECS/Fargate for auto-scaling.'
        ),
        # Advanced
        (
            'What are the system limitations you would discuss in an interview?',
            'Yield estimates are algorithmic, not satellite-validated. Spatial layout assumes flat terrain. Soil data depends on user input (no IoT integration yet). No real-time weather integration in reports. The SQL uses string interpolation (not parameterized queries). Fluxbase rate limits (30 req/10s) could bottleneck under high concurrency. The LLM fallback chain adds latency when primary models are down.'
        ),
        (
            'What would you improve in v2?',
            'IoT sensor integration for real-time soil data. Satellite imagery (Sentinel-2) for crop health monitoring. Parameterized queries or ORM for SQL safety. WebSocket-based real-time chat. Redis caching layer. User-trainable crop models using transfer learning. Mobile app (React Native). Push notifications for weather alerts. A2A (Agent-to-Agent) protocol for inter-agent communication.'
        ),
        (
            'How do you handle the cold start problem for new farmers?',
            'When a new farmer signs up and uses crop recommendation before completing intake, the auto-profile healing creates a minimal farmer_profile record. The recommendation uses only the soil parameters submitted in the form (NPK, temp, rainfall, water) without relying on historical data. The spatial twin defaults to Medium water, Medium nitrogen, and no previous crop context.'
        ),
        (
            'Explain the difference between _call_flux() and _call_llm().',
            '_call_flux() is the low-level function that directly calls the Fluxbase AI Gateway REST API for a specific model. _call_llm() is the high-level unified dispatcher that: (1) Auto-selects the appropriate Flux model based on the label/context, (2) Implements the full fallback chain (Flux -> GLM -> Groq -> Claude), (3) Adds logging and timing. Individual agents can call either function depending on whether they need explicit model control or prefer automatic selection.'
        ),
        (
            'How does the companion crop scoring work?',
            'Each crop in CROP_DB has a companion_score (1-10). When selecting a companion for a main crop, the system: (1) Looks up valid companions from COMPANION_MATRIX, (2) Filters to only crops that exist in CROP_DB, (3) Selects the companion with the highest companion_score. Special overrides apply: crop rotation forces N-fixing companions, low nitrogen forces legume companions, and water mismatch triggers full crop override.'
        ),
        (
            'How do you ensure the LLM returns valid JSON?',
            'Three strategies: (1) The system prompt explicitly states "Output valid JSON only", (2) The user prompt includes the exact JSON schema to follow, (3) Post-processing strips markdown code fences (```json), regex-extracts JSON arrays/objects, and validates structure. If JSON parsing fails, the agent falls back to deterministic rule-based output that is guaranteed to be well-formed.'
        ),
        (
            'What is the role of temperature=0.2 in _call_flux()?',
            'Temperature 0.2 is intentionally low to ensure deterministic, consistent outputs. In agricultural advisory, we want reliable, reproducible recommendations rather than creative/varied responses. Low temperature reduces randomness in crop selections, treatment recommendations, and plan details. For the chat agent, a slightly higher temperature could be used for more natural conversation, but we keep it consistent for simplicity.'
        ),
    ]

    for i, (q, a) in enumerate(qa_pairs, 1):
        pdf.qa_block(i, q, a)

    # ═══════════════════════════════════════════════════════════════════
    # FINAL PAGE
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(0, 12, 'End of Documentation', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 8, 'SuperFarmer - AI Agricultural Intelligence Platform', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, 'Built for Indian Farmers with Agentic AI', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 7, f'Document generated on {datetime.datetime.now().strftime("%d %B %Y at %I:%M %p")}', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, 'Total Pages: {nb}', align='C', new_x="LMARGIN", new_y="NEXT")

    # ── Output ──────────────────────────────────────────────────────
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SuperFarmer_EndToEnd_Documentation.pdf')
    pdf.output(output_path)
    print(f"\n{'='*60}")
    print(f"  PDF Generated Successfully!")
    print(f"  Output: {output_path}")
    print(f"  Pages:  {pdf.page_no()}")
    print(f"{'='*60}\n")
    return output_path


if __name__ == '__main__':
    build_pdf()
