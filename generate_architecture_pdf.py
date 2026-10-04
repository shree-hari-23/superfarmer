#!/usr/bin/env python3
"""
SuperFarmer — Full System Architecture & Technical Explanation PDF
Generates a detailed, professional PDF for interview preparation.
"""

from fpdf import FPDF
import os
import datetime


class ArchPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=20)
        self.chapter_num = 0

    def header(self):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, 'SuperFarmer - Full System Architecture & Technical Explanation', align='C')
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

    def chapter_title(self, title):
        self.chapter_num += 1
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(22, 101, 52)
        self.ln(4)
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

    def code_block(self, text):
        self.set_font('Courier', '', 8.5)
        self.set_fill_color(245, 245, 245)
        self.set_text_color(30, 30, 30)
        self.set_draw_color(200, 200, 200)
        x = self.get_x()
        w = self.w - self.l_margin - self.r_margin
        self.rect(x, self.get_y(), w, 5, 'D')
        for line in text.split('\n'):
            safe_line = self._safe(line)
            self.cell(w, 4.5, '  ' + safe_line, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def table_row(self, cols, widths, bold=False, fill=False):
        self.set_font('Helvetica', 'B' if bold else '', 9)
        if fill:
            self.set_fill_color(230, 245, 230)
        self.set_text_color(30, 41, 59)
        max_h = 5
        for i, (col, w) in enumerate(zip(cols, widths)):
            self.cell(w, max_h, self._safe(col), border=1, fill=fill)
        self.ln(max_h)

    def interview_answer(self, question, answer):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(22, 101, 52)
        self.multi_cell(0, 5.5, self._safe(f'Q: {question}'))
        self.ln(1)
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5.5, self._safe(f'A: {answer}'))
        self.ln(3)

    @staticmethod
    def _safe(text):
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


def generate_pdf():
    pdf = ArchPDF()
    pdf.alias_nb_pages()

    # ═══════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font('Helvetica', 'B', 32)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(0, 15, 'SuperFarmer', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 8, 'Multi-Agent Agricultural Decision Support System', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_draw_color(34, 139, 34)
    pdf.set_line_width(0.8)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, 'Full System Architecture & Technical Explanation', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, 'Interview Preparation Document', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 7, f'Generated: {datetime.datetime.now().strftime("%d %B %Y, %I:%M %p")}', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, 'Fluxbase AI Gateway | Cloud MySQL | FastAPI | Docker | AWS EC2', align='C', new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(0, 12, 'Table of Contents', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    toc = [
        ('1.', 'What Is SuperFarmer'),
        ('2.', 'System Architecture Overview'),
        ('3.', 'Technology Stack'),
        ('4.', '4-Tier LLM Model System'),
        ('5.', 'All 12 Agents - Deep Technical Explanation'),
        ('6.', 'Database Schema (Fluxbase Cloud MySQL)'),
        ('7.', 'MCP Server (Model Context Protocol)'),
        ('8.', 'API Routes (FastAPI)'),
        ('9.', 'Neuro-Symbolic Spatial Digital Twin Pipeline'),
        ('10.', 'Evaluation & Benchmarking'),
        ('11.', 'Deployment Architecture (Docker + AWS EC2)'),
        ('12.', 'Request Flow - End to End Example'),
        ('13.', 'Interview Questions & Answers'),
    ]
    for num, title in toc:
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(12, 7, num)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 1: WHAT IS SUPERFARMER
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('What Is SuperFarmer')
    pdf.body_text(
        'SuperFarmer is a Multi-Agent AI-powered Agricultural Decision Support System built for Indian farmers. '
        'It is a full-stack web application where 12 specialized agents collaborate to provide personalized crop '
        'recommendations, AI-powered plant disease diagnosis, automated crop management planning, a neuro-symbolic '
        'Spatial Digital Twin with optimized hex-grid farm layouts, yield comparison, 7-section Field Advisory Reports, '
        'multilingual conversational AI in 11 Indian languages, and real-time 3-day weather forecasting.'
    )

    pdf.section_title('Core Capabilities')
    capabilities = [
        'Personalized crop recommendations based on soil parameters (NPK, temperature, rainfall, water availability)',
        'AI-powered plant disease diagnosis from text symptoms AND/OR uploaded leaf images (multimodal)',
        'Automated 5-stage crop management plans (sowing -> irrigation -> fertilizer -> pest -> harvest)',
        'Neuro-symbolic Spatial Digital Twin with 2D/3D hex-grid farm layout generation',
        'Yield comparison: optimized intercropping vs normal monoculture (+25-30% improvement)',
        '7-section Field Advisory Reports with email delivery via Gmail SMTP',
        'Multilingual conversational AI supporting 11 Indian languages (Hindi, Bengali, Telugu, etc.)',
        'Real-time 3-day hyper-local weather forecasting via Tomorrow.io API',
        'MCP Server exposing farmer profile data to external AI agents',
        'Full containerized deployment on Docker + AWS EC2',
    ]
    for cap in capabilities:
        pdf.bullet(cap)

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 2: SYSTEM ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('System Architecture Overview')

    pdf.section_title('Layer 1: Frontend (Client)')
    pdf.body_text(
        'The frontend is server-side rendered using Jinja2 templates served by FastAPI. There are 11 HTML pages, '
        'each mapping to a specific agent workflow (signup, login, intake, recommendation, plan, disease, spatial '
        'planner, report, benchmarks). The Spatial Planner page uses Three.js for interactive 3D hex-grid rendering. '
        'All form submissions go to FastAPI as POST requests with Form(...) data.'
    )
    pdf.body_text(
        'Design Decision: Server-side rendering was chosen over React/Vue because the primary users are Indian '
        'farmers on low-bandwidth connections. SSR sends fully rendered HTML with no client-side framework overhead.'
    )

    pdf.section_title('Layer 2: FastAPI Backend (app.py)')
    pdf.body_text(
        'The backend is a FastAPI application running on Uvicorn (ASGI async server) on port 5000. It uses '
        'Starlette SessionMiddleware for cookie-based encrypted user sessions. There are 15 route handlers '
        '(GET/POST per feature). Each route is a thin controller that: (1) checks login status, (2) packages '
        'form data into a dict, (3) calls orchestrator.route_request(intent, data), and (4) renders the '
        'template with the result. Routes contain ZERO business logic.'
    )

    pdf.section_title('Layer 3: OrchestratorAgent (Dispatcher)')
    pdf.body_text(
        'The OrchestratorAgent receives an (intent, data) tuple from each FastAPI route. It uses a simple '
        'if/elif chain to map 12 intent strings (signup, login, intake, recommendation, plan, diagnose, '
        'weather, spatial_plan, yield_comparison, chat, report, send_email) to static method calls on the '
        'appropriate agent class. This is a lightweight, stateless dispatcher. No ML model or NLU is used '
        'for routing since intents are URL-determined (user clicks a page, intent is fixed).'
    )

    pdf.section_title('Layer 4: 12 Specialized Agents')
    pdf.body_text(
        'The agents are organized into 3 categories:\n\n'
        'AI-POWERED AGENTS (6 agents, use LLM models):\n'
        '- CropRecommendationAgent (flux-pro) - Structured JSON output for Top 3 crop recommendations\n'
        '- CropPlannerAgent (flux-pro) - 5-stage crop management plan generation\n'
        '- DiseaseDiagnosisAgent (flux-omni/max) - Multimodal vision + text disease diagnosis\n'
        '- SuperFarmerChatAgent (flux-flash) - Multilingual conversational AI in 11 languages\n'
        '- ReportAgent (flux-ultra) - 7-section Field Advisory Report synthesis\n'
        '- SpatialPlannerAgent narrative (flux-ultra) - AI-generated layout rationale explanation\n\n'
        'RULE-BASED AGENTS (3 agents, zero AI):\n'
        '- YieldComparisonAgent - Deterministic yield math with ICAR companion tables\n'
        '- SpatialPlannerAgent geometry - Hex layout, zone division, border crops, quality scoring\n'
        '- IntakeAgent - Data sanitization and profile persistence\n\n'
        'UTILITY AGENTS (3 agents, external APIs):\n'
        '- WeatherAgent - Tomorrow.io API + Nominatim geocoding\n'
        '- EmailAgent - Gmail SMTP (port 587, STARTTLS)\n'
        '- UserAuthAgent - Werkzeug scrypt/pbkdf2 + bcrypt password security'
    )

    pdf.section_title('Layer 5: 4-Tier LLM Fallback Chain')
    pdf.body_text(
        'Every AI agent calls _call_llm(), which implements a 4-level cascade:\n\n'
        'TIER 1: Fluxbase AI Gateway (flux-pro/ultra/omni/flash) - OpenAI-compatible endpoint\n'
        'TIER 2: Zhipu AI GLM-4-flash (direct API) - If Fluxbase fails\n'
        'TIER 3: Groq Qwen 3.8-27B (direct API) - If GLM fails\n'
        'TIER 4: Anthropic Claude Haiku 4.5 (direct API) - If Groq fails\n'
        'TIER 5: Deterministic Rule-Based Fallback (per agent) - If ALL AI fails\n\n'
        'The system has 5 layers of protection. Even if every AI provider goes down simultaneously, '
        'the farmer still gets a valid response from hardcoded agronomy rules. This is how we achieve 0% downtime.'
    )

    pdf.section_title('Layer 6: Database (Fluxbase Cloud MySQL)')
    pdf.body_text(
        'All SQL queries are executed via REST API to https://fluxbase.vercel.app/api/execute-sql. No local '
        'MySQL installation is required. The Docker container only needs API keys in the .env file. '
        'Authenticated with FLUXBASE_API_KEY + FLUXBASE_PROJECT_ID. Contains 9 tables: users, farmer_profile, '
        'soil_records, crop_recommendations, crop_plans, nutrient_risk_log, reports, session_logs, spatial_twin_log.'
    )

    pdf.section_title('Layer 7: External APIs')
    ext_apis = [
        ('Tomorrow.io v4', 'WeatherAgent', '3-day hyper-local weather forecast'),
        ('Nominatim (OpenStreetMap)', 'WeatherAgent', 'Geocodes location name to lat/lon'),
        ('Gmail SMTP (port 587)', 'EmailAgent', 'Welcome email, login alert, report delivery'),
        ('Fluxbase AI Gateway', 'All AI agents', 'Unified LLM inference (OpenAI-compatible)'),
        ('Google Gemini SDK', 'DiseaseDiagnosisAgent', 'Native vision fallback (PIL.Image)'),
    ]
    w = [45, 40, 95]
    pdf.table_row(['Service', 'Used By', 'Purpose'], w, bold=True, fill=True)
    for row in ext_apis:
        pdf.table_row(list(row), w)

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 3: TECHNOLOGY STACK
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Technology Stack')

    tech_stack = [
        ('Backend Framework', 'FastAPI + Uvicorn (ASGI)', 'Async HTTP server, form handling, JSON APIs'),
        ('Templating', 'Jinja2', 'Server-side rendered HTML pages'),
        ('Session Mgmt', 'Starlette SessionMiddleware', 'Cookie-based encrypted user sessions'),
        ('Database', 'Fluxbase Cloud MySQL (REST)', 'Zero-config cloud SQL, no local install'),
        ('Primary LLM', 'Fluxbase AI Gateway', 'OpenAI-compatible proxy to multiple providers'),
        ('Fallback LLMs', 'GLM-4 / Groq Qwen / Claude', '4-level cascade ensuring 0% downtime'),
        ('Vision AI', 'Gemini 2.5 Flash + GPT-4o-mini', 'Multimodal leaf image disease diagnosis'),
        ('Weather API', 'Tomorrow.io v4 + Nominatim', '3-day forecast + auto-geocoding'),
        ('Email', 'Gmail SMTP (587, STARTTLS)', 'Welcome, login alerts, report delivery'),
        ('Password Security', 'Werkzeug + bcrypt', 'Multi-format hash verification'),
        ('MCP Server', 'FastMCP', 'Exposes farmer profile to external AI agents'),
        ('Containerization', 'Docker + docker-compose', 'Production deployment on AWS EC2'),
        ('3D Rendering', 'Three.js', 'Interactive 3D hex-grid spatial twin'),
    ]
    w = [30, 50, 100]
    pdf.table_row(['Layer', 'Technology', 'Purpose'], w, bold=True, fill=True)
    for row in tech_stack:
        pdf.table_row(list(row), w)

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 4: 4-TIER LLM SYSTEM
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('4-Tier LLM Model System')

    pdf.section_title('How _call_llm() Works')
    pdf.body_text(
        'The unified dispatcher auto-selects the appropriate model tier based on the agent label:\n'
        '- "crop" or "plan" in label -> flux-pro (Structured Output Tier)\n'
        '- "disease" or "vision" in label -> flux-omni (Vision Pathology Tier)\n'
        '- "spatial" or "twin" or "report" in label -> flux-ultra (Deep Reasoning Tier)\n'
        '- "chat" in label -> flux-flash (Fast Chat Tier)\n\n'
        'Then tries the selected model, falling back through flux-turbo and flux-flash within Fluxbase, '
        'then to GLM-4-flash, Groq Qwen, Claude Haiku, and finally deterministic rules.'
    )

    pdf.section_title('Tier Mapping')
    tier_data = [
        ('Tier 1: Fast Chat', 'flux-flash/turbo', 'GLM-4-Flash / LLaMA 3.3', 'ChatAgent'),
        ('Tier 2: Structured', 'flux-pro', 'GLM-4-Air', 'CropRec, CropPlan'),
        ('Tier 3: Vision', 'flux-omni/max', 'Gemini 2.0 / GPT-4o-mini', 'DiseaseAgent'),
        ('Tier 4: Deep Reason', 'flux-ultra', 'GLM-4-Plus', 'Spatial, Report'),
    ]
    w = [32, 30, 52, 36]
    pdf.table_row(['Tier', 'Gateway Alias', 'Real Model', 'Agent'], w, bold=True, fill=True)
    for row in tier_data:
        pdf.table_row(list(row), w)

    pdf.ln(4)
    pdf.section_title('Why 4 Tiers?')
    pdf.body_text(
        'Different agents have fundamentally different LLM requirements. A chat response needs <100ms '
        'latency so we use a small fast model. Crop recommendation needs 100% valid JSON so we use a '
        'structured output model. Disease diagnosis needs visual understanding so we use a vision model. '
        'The Spatial Twin rationale needs complex multi-variable reasoning so we use a deep reasoning model. '
        'Using one model for everything would be either too slow, too expensive, or too inaccurate.'
    )

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 5: ALL 12 AGENTS
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('All 12 Agents - Deep Technical Explanation')

    agents = [
        {
            'name': 'OrchestratorAgent',
            'llm': 'None (routing only)',
            'desc': 'Central dispatcher receiving (intent, data) from FastAPI routes. Uses if/elif chain to map 12 intent strings to agent static methods. No ML/NLU for routing because intents are URL-determined. Stateless design with active_sessions dict for future session tracking.',
        },
        {
            'name': 'UserAuthAgent',
            'llm': 'None (security module)',
            'desc': 'Handles signup (Werkzeug generate_password_hash with scrypt/pbkdf2) and login (multi-format _verify_password supporting bcrypt $2a$/$2b$, Werkzeug scrypt/pbkdf2, and legacy plaintext fallback). Provides get_farmer_profile_by_user() and get_user_email() helpers.',
        },
        {
            'name': 'IntakeAgent',
            'llm': 'None (data sanitizer)',
            'desc': 'Captures farmer profile data (name, land_size, location, water_availability, farming_goals). Sanitizes all inputs through safe_str() which replaces single quotes to prevent SQL injection. Converts land_size to float. INSERTs into farmer_profile table.',
        },
        {
            'name': 'CropRecommendationAgent',
            'llm': 'flux-pro (Structured Output Tier)',
            'desc': 'Analyzes soil parameters and recommends Top 3 crops. Constructs agronomist prompt requesting JSON array. Calls flux-pro -> flux-turbo -> flux-flash -> _call_llm() fallback chain -> rule-based fallback. Parses JSON with regex extraction. Auto-heals missing farmer_profile FK. Logs soil records and recommendations to database. Rule-based fallback uses hardcoded ICAR agronomy logic based on soil type, NPK thresholds, and water availability.',
        },
        {
            'name': 'CropPlannerAgent',
            'llm': 'flux-pro (Structured Output Tier)',
            'desc': 'Generates 5-stage crop management plan (sowing_schedule, irrigation_plan, fertilizer_schedule, pest_alerts, harvest_timeline). Uses _sanitize_crop_name() to extract clean crop name from long AI text by scanning for known crop names. Falls back to static default plans. Stores plan in crop_plans table.',
        },
        {
            'name': 'DiseaseDiagnosisAgent',
            'llm': 'flux-omni/max (Vision Pathology Tier)',
            'desc': 'Diagnoses plant diseases from text AND/OR leaf images. Image path: reads bytes, base64-encodes, constructs OpenAI multimodal message with type:image_url. Primary: flux-omni (Gemini vision via Fluxbase), then flux-max (GPT-4o-mini). Fallback A: Native Gemini 2.5 Flash SDK with PIL.Image. Fallback B: Groq/Claude text-only. Enriches products with auto-generated Amazon.in and Flipkart.com search URLs.',
        },
        {
            'name': 'WeatherAgent',
            'llm': 'None (API-driven)',
            'desc': 'Fetches 3-day forecast using Tomorrow.io v4 API. Auto-geocodes location names to lat/lon using OpenStreetMap Nominatim. Processes daily timelines for temperatureMax and precipitationProbabilityMax. Generates rule-based suggestions: heavy rain -> harvest early, moderate rain -> hold irrigation, extreme heat (>38C) -> increase irrigation, clear -> grow normally.',
        },
        {
            'name': 'SpatialPlannerAgent',
            'llm': 'flux-ultra (narrative) + Rule Engine (geometry)',
            'desc': 'NEURO-SYMBOLIC hybrid. Geometry is 100% deterministic: CROP_DB (16 crops), COMPANION_MATRIX, Memory Fetch (queries Fluxbase for previous crop, nitrogen, water), Decision Rules (crop rotation, nitrogen fixing, water matching), Zone Division (strip/row/grid), Hex Layout (staggered placement), Border Crops (Marigold ring), Quality Score (0-100), Yield Estimation. Only the narrative rationale is generated by flux-ultra LLM. Logs to spatial_twin_log table.',
        },
        {
            'name': 'YieldComparisonAgent',
            'llm': 'None (deterministic rule engine)',
            'desc': 'Compares optimized intercropping vs normal monoculture yield. Uses BASE_YIELDS (tons/acre for 23 crops) and COMPANION_BONUS (5-8% synergy for N-fixing/pest-suppressing companions). Calculates intercrop boost (15% base + companion bonus, capped at 30%), normal penalty (10%), and income delta at Rs 15,000/ton market rate.',
        },
        {
            'name': 'SuperFarmerChatAgent',
            'llm': 'flux-flash/turbo (Fast Chat Tier)',
            'desc': 'Multilingual conversational advisor supporting 11 Indian languages (Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Kannada, Punjabi, Odia, Malayalam, English). Builds comprehensive farmer context by querying Fluxbase for profile, soil records, crop plan, nutrient risk log. Injects MANDATORY LANGUAGE DIRECTIVE into system prompt to force LLM to respond in the selected language and script.',
        },
        {
            'name': 'ReportAgent',
            'llm': 'flux-ultra (Deep Reasoning)',
            'desc': 'Generates 7-section Field Advisory Report by pulling authentic data from Fluxbase: (1) Farmer Profile, (2) Soil NPK, (3) Crop Recommendations, (4) Active Crop Plan, (5) Spatial Twin, (6) Yield Metrics (_calculate_yield_metrics), (7) AI Insights (_generate_grounded_insights). Also generates professionally styled HTML email via build_html_email(). Saves to reports table.',
        },
        {
            'name': 'EmailAgent',
            'llm': 'None (transactional engine)',
            'desc': 'Sends transactional emails via Gmail SMTP (port 587, STARTTLS). Auto-discovers notification logo from images/ directory. Creates RFC 2387 multipart/related messages with inline logo (Content-ID: superfarmer_logo), HTML body, and plaintext fallback. Used for welcome emails, login security alerts, and report delivery. Called asynchronously via threading.Thread.',
        },
    ]

    for agent in agents:
        pdf.section_title(agent['name'])
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, f'LLM: {agent["llm"]}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.body_text(agent['desc'])

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 6: DATABASE SCHEMA
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Database Schema (Fluxbase Cloud MySQL)')

    pdf.body_text(
        'All SQL queries are executed via REST API to https://fluxbase.vercel.app/api/execute-sql. '
        'No local MySQL installation required. Authenticated with FLUXBASE_API_KEY + FLUXBASE_PROJECT_ID.'
    )

    pdf.section_title('config.py - Database Connection')
    pdf.code_block(
        'FLUXBASE_URL = "https://fluxbase.vercel.app/api/execute-sql"\n'
        '\n'
        'def execute_fluxbase_sql(query):\n'
        '    headers = {"Authorization": f"Bearer {API_KEY}"}\n'
        '    payload = {"projectId": PROJECT_ID, "query": query}\n'
        '    resp = requests.post(URL, json=payload, headers=headers)\n'
        '    return data.get("result", {})'
    )

    tables = [
        ('users', 'user_id (PK), email, password_hash', 'User authentication'),
        ('farmer_profile', 'farmer_id (PK), user_id (FK), name, land_size, location, water, goals', 'Farmer intake data'),
        ('soil_records', 'record_id (PK), farmer_id (FK), soil_type, N, P, K, temp', 'Historical soil NPK readings'),
        ('crop_recommendations', 'rec_id (PK), farmer_id (FK), recommended_crops', 'AI crop suggestions'),
        ('crop_plans', 'plan_id (PK), farmer_id (FK), crop, sowing, irrigation, fertilizer, pest, harvest', 'Crop management plans'),
        ('nutrient_risk_log', 'log_id (PK), farmer_id (FK), risk_prob, risk_level, action', 'ML nutrient risk predictions'),
        ('reports', 'report_id (PK), farmer_id (FK), report_text', 'Generated advisory reports'),
        ('session_logs', 'session_id (PK), farmer_id (FK), interaction_log', 'Chat interaction history'),
        ('spatial_twin_log', 'log_id (PK), farmer_id (FK), main_crop, companion, yield, score', 'Spatial twin audit trail'),
    ]
    w = [35, 85, 60]
    pdf.table_row(['Table', 'Key Columns', 'Purpose'], w, bold=True, fill=True)
    for row in tables:
        pdf.table_row(list(row), w)

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 7: MCP SERVER
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('MCP Server (Model Context Protocol)')

    pdf.body_text(
        'SuperFarmer exposes a Model Context Protocol (MCP) server via FastMCP. This allows external AI agents '
        '(Claude, GPT, etc.) to call the get_farmer_profile tool to retrieve farmer data from the database. '
        'The MCP server runs on stdio transport and returns JSON with: name, land_size, location, water_availability, farming_goals.'
    )

    pdf.code_block(
        'from mcp.server.fastmcp import FastMCP\n'
        'mcp = FastMCP("FarmerProfile")\n'
        '\n'
        '@mcp.tool()\n'
        'def get_farmer_profile(farmer_id: int) -> str:\n'
        '    p_res = execute_fluxbase_sql(\n'
        '        f"SELECT * FROM farmer_profile WHERE farmer_id={farmer_id}"\n'
        '    )\n'
        '    return json.dumps(p_res["rows"][0])\n'
        '\n'
        'mcp.run(transport="stdio")'
    )

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 8: API ROUTES
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('API Routes (FastAPI)')

    routes = [
        ('GET/POST', '/signup', 'signup', 'UserAuthAgent'),
        ('GET/POST', '/login', 'login', 'UserAuthAgent'),
        ('GET', '/logout', '-', 'Session clear'),
        ('GET/POST', '/intake', 'intake', 'IntakeAgent'),
        ('GET/POST', '/recommendation', 'recommendation', 'CropRecAgent'),
        ('GET/POST', '/plan', 'plan', 'CropPlannerAgent'),
        ('GET/POST', '/disease', 'diagnose', 'DiseaseAgent'),
        ('GET/POST', '/spatial-planner', 'spatial_plan', 'SpatialPlannerAgent'),
        ('GET/POST', '/report', 'report', 'ReportAgent'),
        ('POST', '/generate-report', 'report', 'ReportAgent'),
        ('POST', '/send-report-email', 'send_email', 'Report + Email'),
        ('GET', '/benchmarks', '-', 'Static evaluation'),
    ]
    w = [25, 40, 35, 40]
    pdf.table_row(['Method', 'Route', 'Intent', 'Agent'], w, bold=True, fill=True)
    for row in routes:
        pdf.table_row(list(row), w)

    pdf.ln(4)
    pdf.section_title('Async Patterns')
    pdf.bullet('Image upload in /disease uses async def + await leaf_image.read() for non-blocking I/O')
    pdf.bullet('Email sending is dispatched via threading.Thread for fire-and-forget execution')

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 9: SPATIAL DIGITAL TWIN
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Neuro-Symbolic Spatial Digital Twin Pipeline')

    pdf.body_text(
        'The Spatial Digital Twin is the most complex component - a hybrid of deterministic rule engine + AI narrative. '
        'The geometry and layout are 100% deterministic Python. Only the narrative rationale text is AI-generated.'
    )

    steps = [
        ('Step 1: Crop Normalization', 'Alias table maps 30+ variations (e.g., "tomatoes" -> "Tomato", "peanut" -> "Groundnut")'),
        ('Step 2: Memory Fetch', '_fetch_farmer_memory() queries Fluxbase for: previous crop (crop_plans), nitrogen level (inferred from crop_recommendations), water availability (farmer_profile), past yield (spatial_twin_log)'),
        ('Step 3: Decision Rules', '3 deterministic rules applied in sequence: (a) Crop Rotation - if same crop as last season, force N-fixing companion, (b) Soil Nitrogen - if N is Low, force N-fixer companion, (c) Water Matching - if farm is Low-water but crop needs High, override to drought-tolerant crop'),
        ('Step 4: Companion Selection', 'Ranks valid companions from COMPANION_MATRIX by companion_score in CROP_DB (highest wins)'),
        ('Step 5: Zone Division', '4 layout modes: Strip (vertical), Row (horizontal), Grid (checkerboard interleaving), Auto (defaults to Strip)'),
        ('Step 6: Sunlight Orientation', 'If companion is taller than main crop, swap zone placement so taller crop goes north/west to avoid shading'),
        ('Step 7: Hex Layout Generation', 'Staggered hexagonal grid: for odd rows, nodes offset by spacing/2 horizontally. Each node stores: x, y, crop type, color, radius (spacing x 0.32), row/col, height_m'),
        ('Step 8: Border Crops', 'Marigold pest-barrier ring placed around all 4 perimeter edges'),
        ('Step 9: Quality Score (0-100)', 'companion_score x 5 (0-50) + N-fixer present (+20) + no water mismatch (+15) + border crops (+15)'),
        ('Step 10: Yield Estimation', 'Per-zone: yield_t_per_acre x zone_acres. Summed across all zones + border Marigold yield'),
        ('Step 11: Real Field Population', 'Converts visual 3D nodes to actual plant counts (e.g., "1 3D Node = ~847 Real Plants")'),
        ('Step 12: AI Narrative', 'Calls flux-ultra LLM to generate 9-section structured explanation of the layout logic'),
    ]
    for title, desc in steps:
        pdf.sub_section(title)
        pdf.body_text(desc)

    pdf.section_title('CROP_DB Schema (16 Crops)')
    pdf.body_text(
        'Each crop entry contains: name, color (hex), emoji, spacing (cm), height_m, water (Low/Medium/High), '
        'nitrogen (Fixer/Consumer/Neutral), shade (Sensitive/Tolerant), profit_score (0-10), companion_score (0-10), '
        'yield_t_per_acre. Example: Corn = {spacing: 60cm, height: 2.5m, water: Medium, nitrogen: Consumer, '
        'companion_score: 8, yield: 2.8 t/acre}'
    )

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 10: EVALUATION
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Evaluation & Benchmarking')

    pdf.section_title('Crop Recommendation Benchmark (200 Cases)')
    pdf.body_text(
        'Dataset: 200 synthetic Indian farming scenarios across 5 soil types (Black, Alluvial, Red, Sandy, Laterite) '
        'with ICAR-calibrated ground truth crop portfolios. Each case has: soil_type, N, P, K, temperature, rainfall, '
        'water_availability, expected_top1, expected_top3.'
    )

    eval_metrics = [
        ('Top-1 Accuracy', '20% (40/200)', 'Expected crop ranked first'),
        ('Top-3 Accuracy', '76.7% (153/200)', 'Expected crop in top 3'),
        ('100% Crops (Top-3)', 'Cotton, Groundnut, Rice, Soybean, Sunflower, Wheat', '6 staple crops never missed'),
    ]
    w = [35, 45, 100]
    pdf.table_row(['Metric', 'Result', 'Meaning'], w, bold=True, fill=True)
    for row in eval_metrics:
        pdf.table_row(list(row), w)

    pdf.ln(4)
    pdf.section_title('Disease Diagnosis Benchmark (20 Cases)')
    pdf.body_text(
        'Dataset: 20 text-based symptom cases covering 14 Indian crops and 20 diseases. '
        'Matching uses fuzzy SequenceMatcher (threshold >= 0.40) + substring normalization. '
        'Result: 80% match accuracy (16/20 correct diagnoses).'
    )

    pdf.section_title('Why Top-1 Is Low but Top-3 Is High')
    pdf.body_text(
        'Top-1 is 20% because agriculture is inherently multi-crop viable. A Black soil with high nitrogen '
        'and moderate rainfall genuinely supports Cotton, Soybean, AND Wheat equally well. The agent might rank '
        'Soybean #1 while ICAR reference says Cotton, but BOTH are agronomically correct. Top-3 at 76.7% is '
        'the meaningful metric because we present 3 options to the farmer. For 6 staple crops with very distinct '
        'soil-parameter signatures, we achieved 100% - the system never missed.'
    )

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 11: DEPLOYMENT
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Deployment Architecture (Docker + AWS EC2)')

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
    ec2_steps = [
        'Launch EC2 instance (Ubuntu 22.04 LTS, t3.medium recommended)',
        'SSH into instance and install Docker + Docker Compose',
        'Clone the repository or SCP the project files',
        'Create .env file with all API keys (FLUXBASE, GEMINI, GROQ, ANTHROPIC, etc.)',
        'Run: docker-compose up -d --build',
        'Configure Security Group: open port 5000 (or 80 with nginx proxy)',
        'Access at http://<EC2-PUBLIC-IP>:5000',
    ]
    for i, step in enumerate(ec2_steps, 1):
        pdf.bullet(f'Step {i}: {step}')

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 12: REQUEST FLOW
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Request Flow - End to End Example')

    pdf.section_title('Example: Crop Recommendation Request')
    flow_steps = [
        'Farmer fills form on /recommendation page (soil_type=Black, N=80, P=40, K=45, temp=27, rain=800, water=Medium)',
        'Browser sends POST /recommendation with Form data',
        'FastAPI route handler packages data into a dict',
        'Calls orchestrator.route_request("recommendation", data)',
        'Orchestrator dispatches to CropRecommendationAgent.recommend()',
        'Agent constructs agronomist prompt with soil parameters',
        '_call_flux("flux-pro", prompt) -> Fluxbase Gateway -> GLM-4-Air',
        'GLM-4-Air returns JSON: [{"crop": "Cotton", "suitability_score": 95, ...}, ...]',
        'Agent parses JSON with regex (\\[.*?\\]) + json.loads()',
        'Auto-heals farmer_profile FK if missing (INSERT minimal profile)',
        'INSERTs recommendation into crop_recommendations table (Fluxbase SQL)',
        'INSERTs soil readings into soil_records table',
        'Returns {crops_str, crops, crop_details} dict to route handler',
        'FastAPI stores result in session, renders recommendation.html with rich cards',
        'Farmer sees Top 3 crop recommendations with scores, tips, and growing advice',
    ]
    for i, step in enumerate(flow_steps, 1):
        pdf.bullet(f'{i}. {step}')

    pdf.ln(4)
    pdf.section_title('Fallback Chain (If flux-pro Fails)')
    fallback_steps = [
        'flux-pro fails -> try flux-turbo',
        'flux-turbo fails -> try flux-flash',
        'All Flux models fail -> try GLM-4-flash (Zhipu AI direct API)',
        'GLM fails -> try Groq Qwen 3.8-27B',
        'Groq fails -> try Claude Haiku 4.5',
        'ALL AI fails -> _rule_based_fallback(soil_type, n, p, k, temp, rain, water)',
        'Rule engine returns: Black soil + N>40 + temp>22 -> Cotton, Soybean, Wheat',
        'Farmer ALWAYS gets a response. Zero exceptions.',
    ]
    for i, step in enumerate(fallback_steps, 1):
        pdf.bullet(f'{i}. {step}')

    # ═══════════════════════════════════════════════════════════════
    # CHAPTER 13: INTERVIEW Q&A
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.chapter_title('Interview Questions & Answers')

    qa_pairs = [
        (
            'What is the overall architecture of SuperFarmer?',
            'SuperFarmer uses a Multi-Agent Orchestration architecture. A FastAPI backend receives HTTP requests and routes them via an OrchestratorAgent to 12 specialized agents. Each agent handles a specific domain (auth, crop recommendation, disease diagnosis, etc.) using static methods for stateless, scalable processing. The database is Fluxbase Cloud MySQL accessed via REST API, and all LLM inference goes through the Fluxbase AI Gateway with a 4-level fallback chain.'
        ),
        (
            'Why multi-agent instead of monolithic?',
            'Each agent uses a different LLM tier optimized for its task. CropRecommendation needs structured JSON -> I use a structured output model. Disease diagnosis needs vision -> I use a multimodal model. Chat needs <100ms latency -> I use a fast model. Independent agents enable graceful degradation - if one agent LLM fails, others keep working. Each agent has its own rule-based fallback, ensuring the system never returns an empty response.'
        ),
        (
            'Why is the Spatial Twin neuro-symbolic instead of pure AI?',
            'If I let the LLM generate hex coordinates and zone divisions, it would hallucinate - LLMs cannot do reliable math. The geometry (hex placement, zone ratios, spacing calculations, quality scoring, yield estimation) is 100% deterministic Python. The LLM only generates the narrative rationale text explaining WHY the layout was chosen. This gives us reproducible, consistent layouts with human-readable explanations.'
        ),
        (
            'How does the 4-level fallback ensure 0% downtime?',
            'The _call_llm() function tries 4 providers sequentially: Fluxbase Gateway -> GLM-4 (Zhipu AI) -> Qwen (Groq) -> Claude (Anthropic). If ALL 4 fail, each agent has a deterministic rule-based fallback that produces valid output. For example, CropRecommendationAgent falls back to hardcoded agronomy rules based on soil type, NPK values, and water availability. The system literally cannot return an empty response.'
        ),
        (
            'How does the memory system work in the Spatial Twin?',
            '_fetch_farmer_memory() queries Fluxbase for 4 data points: (1) previous crop from crop_plans, (2) nitrogen level inferred from crop_recommendations (if legume was top-recommended -> soil was N-depleted), (3) water availability from farmer_profile, (4) past yield from spatial_twin_log. Then _run_decision_rules() applies 3 deterministic rules: crop rotation (force N-fixer if repeating crop), soil nitrogen (force N-fixer if N is Low), and water matching (override to drought-tolerant crop if Low-water farm + High-water crop).'
        ),
        (
            'How does multilingual chat work?',
            'The user selects a language from 11 options. A MANDATORY LANGUAGE DIRECTIVE is injected into the system prompt: "You MUST generate your ENTIRE response in [language] using [script] script. Even if the farmer asks in English, do NOT respond in English." The directive is placed both at the start AND end of the system prompt to ensure the LLM does not ignore it. Supported scripts: Devanagari, Bengali, Telugu, Tamil, Gujarati, Kannada, Gurmukhi, Odia, Malayalam.'
        ),
        (
            'Why Fluxbase instead of direct MySQL?',
            'Fluxbase Cloud MySQL eliminates the need for local database installation, connection pooling, or managing MySQL on EC2. All SQL goes through a REST API (POST /api/execute-sql). It also provides the AI Gateway - a single API key for all LLM models through an OpenAI-compatible endpoint. This simplifies deployment: the Docker container only needs the .env file with API keys.'
        ),
        (
            'How does the disease diagnosis handle both text and images?',
            'When a user uploads a leaf photo, the agent: (1) reads the file bytes from the UploadFile object, (2) base64-encodes the image, (3) constructs an OpenAI-compatible multimodal message with type:image_url containing the base64 data URI, (4) sends it to flux-omni (Gemini vision via Fluxbase). If flux-omni fails, it falls back to native Gemini 2.5 Flash Python SDK with PIL.Image, then to text-only Groq/Claude modes. The output includes product recommendations with auto-generated Amazon and Flipkart search URLs.',
        ),
        (
            'What evaluation metrics did you use?',
            'For crop recommendation: 200 ICAR-calibrated test cases across 5 soil types. We measure Top-1 accuracy (20%, 40/200) and Top-3 accuracy (76.7%, 153/200). Top-3 is the primary metric because we recommend 3 crops. For 6 staple crops (Cotton, Groundnut, Rice, Soybean, Sunflower, Wheat) we achieved 100% Top-3 accuracy. For disease diagnosis: 20 text-based cases, 80% match accuracy (16/20) using fuzzy SequenceMatcher + substring normalization.'
        ),
        (
            'Explain the hex layout algorithm.',
            'The hex_layout() method places plant nodes in a staggered hexagonal grid within a rectangular zone. For each row, if the row index is odd, nodes are offset by half the spacing value horizontally (creating the hex pattern). Each node stores x, y coordinates, crop type, color, radius (spacing * 0.32), row/col indices, and height_m for 3D rendering. The grid layout mode interleaves crops by row parity (odd rows = main, even rows = companion).'
        ),
    ]

    for q, a in qa_pairs:
        pdf.interview_answer(q, a)

    # ═══════════════════════════════════════════════════════════════
    # SAVE
    # ═══════════════════════════════════════════════════════════════
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SuperFarmer_Architecture_Explained.pdf')
    pdf.output(output_path)
    print(f"\n{'='*60}")
    print(f"PDF generated successfully!")
    print(f"Output: {output_path}")
    print(f"{'='*60}")
    return output_path


if __name__ == '__main__':
    generate_pdf()
