"""
SuperFarmer – Project Documentation PDF Generator
Run:  python generate_doc.py
Output: SuperFarmer_Project_Documentation.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, ListFlowable, ListItem
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.colors import HexColor
import datetime

# ── Colour palette ─────────────────────────────────────────────────────────────
C_GREEN_DARK   = HexColor("#1B5E20")
C_GREEN        = HexColor("#2E7D32")
C_GREEN_LIGHT  = HexColor("#4CAF50")
C_GREEN_BG     = HexColor("#E8F5E9")
C_GREEN_ACCENT = HexColor("#A5D6A7")
C_TEAL         = HexColor("#00695C")
C_AMBER        = HexColor("#FF8F00")
C_AMBER_LIGHT  = HexColor("#FFF8E1")
C_BLUE         = HexColor("#1565C0")
C_BLUE_LIGHT   = HexColor("#E3F2FD")
C_GREY_DARK    = HexColor("#212121")
C_GREY         = HexColor("#424242")
C_GREY_MID     = HexColor("#757575")
C_GREY_LIGHT   = HexColor("#F5F5F5")
C_WHITE        = colors.white
C_DIVIDER      = HexColor("#BDBDBD")
C_HEADER_BG    = HexColor("#1B5E20")
C_ROW_ALT      = HexColor("#F1F8E9")

W, H = A4  # 595.27, 841.89

# ── Styles ─────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def _style(name, **kw):
    return ParagraphStyle(name, **kw)

styles = {
    "cover_title": _style("cover_title",
        fontName="Helvetica-Bold", fontSize=36, textColor=C_WHITE,
        alignment=TA_CENTER, leading=44, spaceAfter=8),
    "cover_subtitle": _style("cover_subtitle",
        fontName="Helvetica", fontSize=16, textColor=HexColor("#C8E6C9"),
        alignment=TA_CENTER, leading=22, spaceAfter=4),
    "cover_meta": _style("cover_meta",
        fontName="Helvetica", fontSize=11, textColor=HexColor("#A5D6A7"),
        alignment=TA_CENTER, leading=16),

    "h1": _style("h1",
        fontName="Helvetica-Bold", fontSize=20, textColor=C_GREEN_DARK,
        spaceBefore=18, spaceAfter=8, leading=26, borderPadding=(0,0,4,0)),
    "h2": _style("h2",
        fontName="Helvetica-Bold", fontSize=14, textColor=C_GREEN,
        spaceBefore=14, spaceAfter=6, leading=20),
    "h3": _style("h3",
        fontName="Helvetica-Bold", fontSize=12, textColor=C_TEAL,
        spaceBefore=10, spaceAfter=4, leading=16),
    "body": _style("body",
        fontName="Helvetica", fontSize=10.5, textColor=C_GREY,
        leading=16, spaceAfter=6, alignment=TA_JUSTIFY),
    "body_sm": _style("body_sm",
        fontName="Helvetica", fontSize=9.5, textColor=C_GREY,
        leading=14, spaceAfter=4),
    "bullet": _style("bullet",
        fontName="Helvetica", fontSize=10.5, textColor=C_GREY,
        leading=16, spaceAfter=4, leftIndent=16, bulletIndent=4),
    "code": _style("code",
        fontName="Courier", fontSize=9, textColor=HexColor("#263238"),
        backColor=HexColor("#ECEFF1"), leading=13,
        leftIndent=12, rightIndent=12, spaceAfter=6,
        borderPadding=4),
    "caption": _style("caption",
        fontName="Helvetica-Oblique", fontSize=9, textColor=C_GREY_MID,
        alignment=TA_CENTER, spaceAfter=4),
    "footer_txt": _style("footer_txt",
        fontName="Helvetica", fontSize=8, textColor=C_GREY_MID,
        alignment=TA_CENTER),
    "badge": _style("badge",
        fontName="Helvetica-Bold", fontSize=9, textColor=C_WHITE,
        alignment=TA_CENTER),
    "toc_h1": _style("toc_h1",
        fontName="Helvetica-Bold", fontSize=12, textColor=C_GREEN_DARK,
        spaceBefore=4, spaceAfter=2, leading=16),
    "toc_h2": _style("toc_h2",
        fontName="Helvetica", fontSize=10.5, textColor=C_GREY,
        spaceBefore=2, spaceAfter=2, leading=14, leftIndent=16),
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def divider(color=C_DIVIDER, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=8, spaceBefore=4)

def section_heading(text, level=1):
    return Paragraph(text, styles[f"h{level}"])

def para(text, style="body"):
    return Paragraph(text, styles[style])

def bullet_list(items, bullet_char="•"):
    return [Paragraph(f"{bullet_char}  {item}", styles["bullet"]) for item in items]

def colored_table(headers, rows, col_widths, header_color=C_GREEN, alt_row=C_ROW_ALT):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND",   (0,0), (-1,0), header_color),
        ("TEXTCOLOR",    (0,0), (-1,0), C_WHITE),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 10),
        ("ALIGN",        (0,0), (-1,-1), "LEFT"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("FONTNAME",     (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",     (0,1), (-1,-1), 9.5),
        ("TEXTCOLOR",    (0,1), (-1,-1), C_GREY),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, alt_row]),
        ("GRID",         (0,0), (-1,-1), 0.4, C_DIVIDER),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("ROUNDEDCORNERS", [4]),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t

def info_box(title, body_text, bg=C_GREEN_BG, border=C_GREEN_LIGHT):
    data = [[Paragraph(f"<b>{title}</b>", styles["h3"]),
             Paragraph(body_text, styles["body_sm"])]]
    t = Table(data, colWidths=[3.5*cm, 12.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX",        (0,0), (-1,-1), 0.8, border),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING",(0,0),(-1,-1), 10),
        ("RIGHTPADDING",(0,0),(-1,-1), 10),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
    ]))
    return t

# ── Page decorators ────────────────────────────────────────────────────────────

def _on_page(canvas, doc):
    canvas.saveState()
    # Header strip
    canvas.setFillColor(C_GREEN_DARK)
    canvas.rect(0, H - 1.1*cm, W, 1.1*cm, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.5*cm, H - 0.72*cm, "🌱  SuperFarmer – AI Agricultural Intelligence Platform")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(W - 1.5*cm, H - 0.72*cm, "Project Documentation 2026")

    # Footer strip
    canvas.setFillColor(C_GREY_LIGHT)
    canvas.rect(0, 0, W, 1.0*cm, fill=1, stroke=0)
    canvas.setFillColor(C_GREY_MID)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(W/2, 0.38*cm, f"Page {doc.page}  |  Confidential — SuperFarmer Project 2026")

    # Green left accent bar
    canvas.setFillColor(C_GREEN_LIGHT)
    canvas.rect(0, 1.0*cm, 0.25*cm, H - 2.1*cm, fill=1, stroke=0)

    canvas.restoreState()

def _on_cover_page(canvas, doc):
    # Full green gradient background
    canvas.saveState()
    canvas.setFillColor(C_GREEN_DARK)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # Decorative circle top-right
    canvas.setFillColor(HexColor("#2E7D32"))
    canvas.circle(W + 30, H + 30, 160, fill=1, stroke=0)
    canvas.setFillColor(HexColor("#388E3C"))
    canvas.circle(-30, -30, 120, fill=1, stroke=0)
    # Bottom white band
    canvas.setFillColor(C_WHITE)
    canvas.rect(0, 0, W, 2.2*cm, fill=1, stroke=0)
    canvas.setFillColor(C_GREY_MID)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(W/2, 0.75*cm, f"Generated on {datetime.datetime.now().strftime('%B %d, %Y')}  |  SuperFarmer AI Platform")
    canvas.restoreState()

# ── Content builder ────────────────────────────────────────────────────────────

def build_story():
    story = []

    # ── COVER (spacers push content down visually, page break at end) ──────────
    story.append(Spacer(1, 5.5*cm))
    story.append(Paragraph("🌱  SuperFarmer", styles["cover_title"]))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("AI Agricultural Intelligence Platform", styles["cover_subtitle"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Comprehensive Project Documentation", styles["cover_subtitle"]))
    story.append(Spacer(1, 1.5*cm))

    # Tag pills (fake badges via table)
    pill_data = [["Multi-Agent AI", "FastAPI", "Gemini 2.5 Flash",
                  "Groq LLaMA", "Fluxbase Cloud DB"]]
    pill_t = Table(pill_data, colWidths=[3.2*cm]*5)
    pill_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), HexColor("#2E7D32")),
        ("TEXTCOLOR",     (0,0), (-1,-1), C_WHITE),
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("BOX",           (0,0), (-1,-1), 1, C_WHITE),
        ("INNERGRID",     (0,0), (-1,-1), 0.5, HexColor("#A5D6A7")),
    ]))
    story.append(pill_t)
    story.append(Spacer(1, 2.5*cm))

    meta_data = [
        ["Project",   "SuperFarmer — AI Agricultural Intelligence"],
        ["Version",   "1.0  (2026)"],
        ["Author",    "Harivardhan"],
        ["Built with","Python 3.12 · FastAPI · Gemini 2.5 Flash · Groq LLaMA"],
        ["Database",  "Fluxbase Cloud MySQL (REST API)"],
        ["Target",    "Indian Farmers 🇮🇳"],
    ]
    meta_t = Table(meta_data, colWidths=[4*cm, 12*cm])
    meta_t.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",      (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("TEXTCOLOR",     (0,0), (0,-1), HexColor("#A5D6A7")),
        ("TEXTCOLOR",     (1,0), (1,-1), C_WHITE),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    story.append(meta_t)
    story.append(PageBreak())

    # ── SECTION 1: OVERVIEW ─────────────────────────────────────────────────────
    story.append(section_heading("1.  Project Overview", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))
    story.append(para(
        "SuperFarmer is a full-stack, AI-powered agricultural advisory web application "
        "designed specifically for Indian farmers. It combines <b>multi-agent AI orchestration</b>, "
        "real-time weather intelligence, plant disease diagnosis (text &amp; image), "
        "hyper-local crop recommendations, and an interactive digital farm twin — all behind "
        "a clean web interface with multilingual support in 10+ Indian languages."
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(para(
        "The platform eliminates the need for local infrastructure: the database runs on "
        "<b>Fluxbase</b> (cloud MySQL accessed via a REST API), LLM inference is provided "
        "by <b>Google Gemini 2.5 Flash</b> and <b>Groq (LLaMA 3.3-70B)</b>, weather data "
        "comes from <b>Tomorrow.io</b>, and geocoding is handled by <b>OpenStreetMap Nominatim</b>."
    ))

    story.append(Spacer(1, 0.4*cm))
    story.append(section_heading("Key Problems Solved", 2))
    story += bullet_list([
        "Farmers lack real-time, hyper-local crop recommendations tailored to their exact soil chemistry.",
        "Disease diagnosis is expensive and slow — SuperFarmer provides instant AI diagnosis from a photo.",
        "Crop planning is non-existent for small farmers — the platform generates complete sowing-to-harvest plans.",
        "Language barriers prevent adoption — multilingual AI chat supports Hindi, Tamil, Telugu, Bengali, and more.",
        "Small farms need spatial layout advice — the Digital Farm Twin generates optimised hexagonal field layouts.",
        "Fragmented tools — SuperFarmer brings weather, soil, disease, planning, and chat into one platform.",
    ])

    story.append(PageBreak())

    # ── SECTION 2: FEATURES ─────────────────────────────────────────────────────
    story.append(section_heading("2.  Feature Set", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))

    features = [
        ["Feature", "Description", "Functional AI Tier & Engine"],
        ["🔐 Auth", "Signup/Login with bcrypt hashing + session cookies. Welcome & login alert emails auto-sent.", "Werkzeug + Gmail SMTP"],
        ["🌾 Crop Recommendation", "Analyses soil NPK, temperature, rainfall, water availability → top 3 crops with explanations, tips, expected yield.", "Structured-Output Tier (flux-pro / GLM-4-Air)"],
        ["📅 Crop Planner", "Full crop management plan: sowing schedule, irrigation, fertilizers, pest alerts, harvest timeline stored in Fluxbase.", "Structured-Output Tier (flux-pro / GLM-4-Air)"],
        ["🔬 Disease Diagnosis", "Diagnoses diseases from text descriptions AND uploaded leaf photos. Returns treatment + Amazon/Flipkart product links.", "Vision-Capable Tier (flux-omni Native Vision / flux-max)"],
        ["🌦️ Weather Analysis", "3-day hyper-local forecast via Tomorrow.io. Auto-geocodes locations. Provides actionable harvest/irrigation advice.", "Tomorrow.io + Nominatim OSM"],
        ["🗺️ Spatial Planner", "Generates personalised 2D hexagonal farm layout with companion planting, zone division, yield estimation, crop rotation memory.", "Deep-Reasoning Tier (flux-ultra / GLM-4-Plus)"],
        ["📊 Yield Comparison", "Compares intercropping vs monoculture yield in tons/acre + ₹ income delta.", "Deterministic Rule Engine"],
        ["💬 AI Chat", "Multilingual conversational agent (10+ Indian languages), agentic tool-calling, Fluxbase memory integration.", "Fast Chat-Tier Model (flux-flash <100ms / flux-turbo speed)"],
        ["📄 Report Generator", "Comprehensive advisory report pulling all agent data from Fluxbase into one professional view.", "Deep-Reasoning Tier (flux-ultra / GLM-4-Plus) + SQL"],
        ["📧 Email Automation", "HTML welcome & login-alert emails sent asynchronously via Gmail SMTP.", "smtplib (async thread)"],
        ["🔌 MCP Server", "FastMCP stdio server exposes farmer profile as an AI tool for external agent pipelines.", "FastMCP + Fluxbase"],
    ]
    story.append(colored_table(
        features[0], features[1:],
        col_widths=[3.8*cm, 8.2*cm, 4.4*cm],
        header_color=C_GREEN
    ))
    story.append(PageBreak())

    # ── SECTION 3: ARCHITECTURE ─────────────────────────────────────────────────
    story.append(section_heading("3.  System Architecture", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))

    story.append(para(
        "SuperFarmer follows a <b>multi-agent orchestration architecture</b>. A single "
        "<code>OrchestratorAgent</code> sits at the centre, receiving intent strings from "
        "FastAPI route handlers and dispatching to the correct specialised agent class. "
        "Each agent is independently testable, has its own fallback chain, and communicates "
        "with Fluxbase for persistence."
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(section_heading("Architecture Diagram", 2))

    arch_text = (
        "Browser / Frontend (Jinja2 HTML)\n"
        "         │\n"
        "         ▼\n"
        "  FastAPI  app.py   (Routes: /, /signup, /login, /intake, /recommendation,\n"
        "                              /plan, /disease, /chat, /spatial-planner, /report)\n"
        "         │\n"
        "         ▼\n"
        "  OrchestratorAgent  ──────────────────────────────────────┐\n"
        "         │                                                  │\n"
        "  ┌──────┴───────────────────────────────────────────┐     │\n"
        "  │  UserAuthAgent          (Werkzeug + Fluxbase)    │     │\n"
        "  │  IntakeAgent            (Fluxbase SQL INSERT)     │     │\n"
        "  │  CropRecommendationAgent(Ollama → Rule Fallback)  │     │\n"
        "  │  CropPlannerAgent       (Groq LLaMA → Fallback)   │     │\n"
        "  │  DiseaseDiagnosisAgent  (Gemini Vision → Groq)    │     │\n"
        "  │  WeatherAgent           (Tomorrow.io REST API)    │     │\n"
        "  │  SpatialPlannerAgent    (Rule engine + Ollama)    │     │\n"
        "  │  YieldComparisonAgent   (Deterministic Rules)     │     │\n"
        "  │  SuperFarmerChatAgent   (Ollama + Tool-calling)   │     │\n"
        "  │  ReportAgent            (Fluxbase SQL Aggregate)  │     │\n"
        "  │  EmailAgent             (Gmail SMTP async)        │     │\n"
        "  └──────────────────────────────────────────────────┘     │\n"
        "                                                            │\n"
        "  Fluxbase Cloud MySQL  ◄──────────────────────────────────┘\n"
        "  POST https://fluxbase.vercel.app/api/execute-sql\n"
        "  Tables: users, farmer_profile, soil_records,\n"
        "          crop_recommendations, crop_plans,\n"
        "          nutrient_risk_log, reports, session_logs\n"
    )
    story.append(Paragraph(arch_text.replace("\n", "<br/>"), styles["code"]))

    story.append(Spacer(1, 0.4*cm))
    story.append(section_heading("Data Flow", 2))
    story.append(para(
        "1. <b>User Request</b> → FastAPI route handler validates session → extracts form/JSON data.<br/>"
        "2. <b>Orchestrator</b> maps intent string (e.g. <code>'recommendation'</code>) → agent class method.<br/>"
        "3. <b>Agent</b> calls external AI API (Ollama / Gemini / Groq / Tomorrow.io) or executes SQL via <code>execute_fluxbase_sql()</code>.<br/>"
        "4. <b>Result</b> returned as Python dict → session stored or rendered via Jinja2 template.<br/>"
        "5. <b>Side effects</b> (emails, DB inserts) may run in background threads."
    ))
    story.append(PageBreak())

    # ── SECTION 4: TECH STACK ───────────────────────────────────────────────────
    story.append(section_heading("4.  Technology Stack", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))

    tech = [
        ["Layer", "Technology", "Purpose"],
        ["Backend Framework", "Python 3.12 + FastAPI + Uvicorn", "Async web framework with hot-reload"],
        ["Frontend", "Jinja2 Templates + HTML/CSS/JS", "Server-side rendered pages"],
        ["Primary LLM", "Google Gemini 2.5 Flash", "Vision diagnosis, spatial planning, chat"],
        ["Secondary LLM", "Groq API — LLaMA 3.1-8b-instant", "Crop planning, text diagnosis"],
        ["Local LLM", "Ollama qwen2.5:7b", "Crop recommendation, agentic chat"],
        ["Fallback LLM", "Anthropic Claude Haiku 4.5", "Fallback when primary LLMs fail"],
        ["Database", "Fluxbase (Cloud MySQL via REST)", "All persistent data storage"],
        ["Weather API", "Tomorrow.io v4", "3-day hyper-local forecasts"],
        ["Geocoding", "OpenStreetMap Nominatim", "Location → lat/lon conversion"],
        ["Authentication", "Werkzeug + Starlette Sessions", "Password hashing + session cookies"],
        ["Email", "Gmail SMTP (smtplib)", "Welcome & security alert emails"],
        ["ML (optional)", "scikit-learn, numpy, joblib", "Nutrient risk models"],
        ["MCP Protocol", "FastMCP (stdio transport)", "Exposes farmer profile as AI tool"],
        ["Image Processing", "Pillow (PIL)", "Leaf image handling for disease AI"],
    ]
    story.append(colored_table(
        tech[0], tech[1:],
        col_widths=[4.5*cm, 6.5*cm, 5.4*cm],
        header_color=C_TEAL
    ))
    story.append(PageBreak())

    # ── SECTION 5: PROJECT STRUCTURE ────────────────────────────────────────────
    story.append(section_heading("5.  Project Structure", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))

    struct = (
        "superfarmer/\n"
        "├── app.py                    # FastAPI application — all HTTP routes\n"
        "├── config.py                 # Fluxbase connection + execute_fluxbase_sql()\n"
        "├── requirements.txt          # Python package dependencies\n"
        "├── farmer_mcp_server.py      # FastMCP stdio server (AI tool interface)\n"
        "├── .env                      # API keys (not committed to git)\n"
        "│\n"
        "├── agents/\n"
        "│   ├── agents.py             # All 12 agent classes + OrchestratorAgent\n"
        "│   └── hf_agent.py           # HuggingFace agent experiments\n"
        "│\n"
        "├── database/\n"
        "│   └── init_db.py            # Creates all Fluxbase tables\n"
        "│\n"
        "├── templates/                # Jinja2 HTML templates\n"
        "│   ├── base.html             # Shared layout (nav, footer)\n"
        "│   ├── home.html             # Landing page\n"
        "│   ├── login.html / signup.html\n"
        "│   ├── intake.html           # Farmer onboarding form\n"
        "│   ├── recommendation.html   # Crop recommendation results\n"
        "│   ├── plan.html             # Crop management plan\n"
        "│   ├── disease.html          # Disease diagnosis + image upload\n"
        "│   ├── chat.html             # AI chat interface\n"
        "│   ├── spatial_planner.html  # Digital farm twin (hex grid)\n"
        "│   └── report.html           # Advisory report viewer\n"
        "│\n"
        "└── static/\n"
        "    └── css/\n"
        "        └── style.css         # Application styles\n"
    )
    story.append(Paragraph(struct.replace("\n", "<br/>"), styles["code"]))
    story.append(PageBreak())

    # ── SECTION 6: AGENT SYSTEM ─────────────────────────────────────────────────
    story.append(section_heading("6.  Multi-Agent System", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))
    story.append(para(
        "All agents reside in <code>agents/agents.py</code> and are dispatched by "
        "<code>OrchestratorAgent.route_request(intent, data)</code>. The orchestrator acts "
        "as a pure router with zero business logic — it simply maps intent strings to agent "
        "class static methods, enabling agents to be developed and tested independently."
    ))
    story.append(Spacer(1, 0.3*cm))

    agent_rows = [
        ["OrchestratorAgent", "Central Router", "Deterministic Python", "Routes all intents to correct agent. Zero business logic.", "—"],
        ["UserAuthAgent", "Auth & User Mgmt", "Werkzeug + Fluxbase", "Handles signup/login with bcrypt-hashed passwords in Fluxbase.", "signup, login"],
        ["IntakeAgent", "Farmer Onboarding", "Fluxbase SQL", "Persists farmer name, land, location, water availability, goals.", "intake"],
        ["CropRecommendationAgent", "AI Crop Advisor", "Structured-Output Tier (flux-pro)", "Top-3 crop picks based on NPK + climate.", "recommendation"],
        ["CropPlannerAgent", "Plan Generator", "Structured-Output Tier (flux-pro)", "Full sowing→harvest plan stored in crop_plans table.", "plan"],
        ["DiseaseDiagnosisAgent", "Plant Pathologist", "Vision-Capable Tier (flux-omni / flux-max)", "Multimodal leaf photo diagnosis + treatment & buy links.", "diagnose"],
        ["WeatherAgent", "Weather Analyst", "Tomorrow.io + Nominatim OSM", "3-day forecast + actionable harvest/irrigation advice.", "weather"],
        ["SpatialPlannerAgent", "Digital Farm Twin", "Deep-Reasoning Tier (flux-ultra)", "Optimised 2D hexagonal field layout + companion planting.", "spatial_plan"],
        ["YieldComparisonAgent", "Yield Optimizer", "Deterministic Rules", "Intercropping vs monoculture: tons/acre + ₹ income delta.", "yield_comparison"],
        ["SuperFarmerChatAgent", "Multilingual AI", "Fast Chat-Tier (flux-flash / flux-turbo)", "10+ Indian language conversational advisor.", "chat"],
        ["ReportAgent", "Report Builder", "Deep-Reasoning Tier (flux-ultra) + SQL", "Aggregates authentic farm data into structured advisory report.", "report"],
        ["EmailAgent", "Email Dispatcher", "Gmail SMTP (async thread)", "HTML welcome & login-alert emails sent in background threads.", "send_email"],
    ]

    story.append(colored_table(
        ["Agent", "Role", "Functional AI Tier", "Responsibility", "Intent Key"],
        agent_rows,
        col_widths=[4*cm, 2.8*cm, 4.2*cm, 3.8*cm, 1.6*cm],
        header_color=C_GREEN
    ))

    story.append(Spacer(1, 0.5*cm))
    story.append(section_heading("Functional AI Tiers & Gateway Architecture", 2))
    story.append(para(
        "SuperFarmer organizes models into four functional capability tiers, decoupling agent requirements from specific gateway model names:"
    ))
    fallback_data = [
        ["Functional Tier", "Gateway Model", "Real Upstream Model", "Provider", "Assigned Agents"],
        ["Fast Chat-Tier", "flux-flash", "glm-4-flash (<100ms)", "Zhipu AI", "SuperFarmerChatAgent (Chat Advisor)"],
        ["Raw Speed Tier", "flux-turbo", "llama-3.3-70b-versatile", "Groq (300+ tok/s)", "SuperFarmerChatAgent (Speed Fallback)"],
        ["Structured-Output Tier", "flux-pro", "glm-4-air", "Zhipu AI", "CropRecommendationAgent & CropPlannerAgent"],
        ["Vision-Capable Tier", "flux-omni", "gemini-2.0-flash Native Vision", "Google Gemini", "DiseaseDiagnosisAgent (Leaf Photo Vision)"],
        ["Vision-Capable Tier", "flux-max", "gpt-4o-mini Vision", "OpenAI", "DiseaseDiagnosisAgent (Diagnostic Benchmark)"],
        ["Deep-Reasoning Tier", "flux-ultra", "glm-4-plus", "Zhipu AI", "SpatialPlannerAgent & ReportAgent"],
        ["Deep-Reasoning Tier", "flux-5.2", "glm-4-plus (technical alias)", "Zhipu AI", "Digital Farm Twin & Synthesis Alias"],
    ]
    story.append(colored_table(
        fallback_data[0], fallback_data[1:],
        col_widths=[3.5*cm, 2.8*cm, 4.2*cm, 2.8*cm, 4.5*cm],
        header_color=C_AMBER
    ))
    story.append(PageBreak())

    # ── SECTION 7: API ROUTES ───────────────────────────────────────────────────
    story.append(section_heading("7.  API Routes", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))
    story.append(para(
        "All routes are defined in <code>app.py</code>. Session authentication is enforced "
        "on protected routes. The application uses Starlette <code>SessionMiddleware</code> "
        "with a configurable <code>SECRET_KEY</code>."
    ))
    story.append(Spacer(1, 0.3*cm))

    routes = [
        ["Method", "Path", "Auth Required", "Description"],
        ["GET", "/", "No", "Home / landing page"],
        ["GET / POST", "/signup", "No", "User registration; triggers welcome email"],
        ["GET / POST", "/login", "No", "User login; triggers security alert email"],
        ["GET", "/logout", "Yes", "Clears session and redirects to home"],
        ["GET / POST", "/intake", "Yes", "Farmer profile onboarding form"],
        ["GET / POST", "/recommendation", "Yes", "Crop recommendation — soil NPK form + AI result"],
        ["GET / POST", "/plan", "Yes", "Crop management plan generator"],
        ["GET / POST", "/disease", "Yes", "Plant disease diagnosis (text + image upload)"],
        ["GET / POST", "/chat", "Yes", "JSON API endpoint for AI conversational chat"],
        ["GET / POST", "/spatial-planner", "Yes", "Digital farm twin — hexagonal field layout (JSON API)"],
        ["GET", "/report", "Yes", "Advisory report viewer"],
        ["POST", "/generate-report", "Yes", "JSON API that pulls all Fluxbase data for report"],
    ]
    story.append(colored_table(
        routes[0], routes[1:],
        col_widths=[2.5*cm, 4.5*cm, 3*cm, 6.4*cm],
        header_color=C_BLUE
    ))
    story.append(PageBreak())

    # ── SECTION 8: DATABASE SCHEMA ──────────────────────────────────────────────
    story.append(section_heading("8.  Database Schema (Fluxbase)", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))
    story.append(para(
        "The database layer uses <b>Fluxbase</b> — a cloud MySQL service accessed entirely "
        "via a single REST endpoint (<code>POST /api/execute-sql</code>). No local MySQL "
        "installation is required. All SQL queries are sent as JSON payloads with the "
        "project ID and an API key for authentication."
    ))
    story.append(Spacer(1, 0.3*cm))

    tables = [
        ["Table", "Primary Key", "Key Columns", "Purpose"],
        ["users", "user_id", "email, password_hash, created_at", "Stores registered user credentials"],
        ["farmer_profile", "farmer_id", "user_id, name, land_size, location, water_availability, farming_goals", "Farmer onboarding profile"],
        ["soil_records", "record_id", "farmer_id, n, p, k, moisture, recorded_at", "Historical soil NPK sensor readings"],
        ["crop_recommendations", "rec_id", "farmer_id, recommended_crops, created_at", "AI-generated crop suggestions"],
        ["crop_plans", "plan_id", "farmer_id, crop_name, sowing_schedule, irrigation_plan, fertilizer_schedule, pest_alerts, harvest_timeline", "Full crop management plan"],
        ["nutrient_risk_log", "log_id", "farmer_id, risk_level, suggested_action, predicted_at", "ML nutrient risk predictions"],
        ["reports", "report_id", "farmer_id, content, created_at", "Generated advisory reports"],
        ["session_logs", "session_id", "user_id, activity, timestamp", "User interaction history"],
    ]
    story.append(colored_table(
        tables[0], tables[1:],
        col_widths=[3.5*cm, 2.5*cm, 6.5*cm, 3.9*cm],
        header_color=C_TEAL
    ))

    story.append(Spacer(1, 0.4*cm))
    story.append(section_heading("Fluxbase Connection (config.py)", 2))
    db_code = (
        "FLUXBASE_URL = 'https://fluxbase.vercel.app/api/execute-sql'\n\n"
        "def execute_fluxbase_sql(query):\n"
        "    headers = {'Authorization': f'Bearer {FLUXBASE_API_KEY}',\n"
        "               'Content-Type': 'application/json'}\n"
        "    payload = {'projectId': FLUXBASE_PROJECT_ID, 'query': query}\n"
        "    resp = requests.post(FLUXBASE_URL, json=payload, headers=headers)\n"
        "    data = resp.json()\n"
        "    if not data.get('success'):\n"
        "        raise Exception(f\"Fluxbase error: {data['error']['message']}\")\n"
        "    return data.get('result', {})"
    )
    story.append(Paragraph(db_code.replace("\n", "<br/>"), styles["code"]))
    story.append(PageBreak())

    # ── SECTION 9: ENVIRONMENT VARIABLES ────────────────────────────────────────
    story.append(section_heading("9.  Environment Variables & Setup", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))

    env_rows = [
        ["GEMINI_API_KEY", "Google AI Studio", "Gemini 2.5 Flash (vision, chat, spatial)"],
        ["GROK_API_KEY", "GroqCloud Console", "LLaMA 3.1-8b-instant (planning, diagnosis)"],
        ["ANTHROPIC_API_KEY", "Anthropic Console", "Claude Haiku 4.5 (fallback LLM)"],
        ["TOMORROW_API_KEY", "Tomorrow.io Dashboard", "3-day hyper-local weather forecast"],
        ["FLUXBASE_API_KEY", "Fluxbase Dashboard → Settings", "Cloud MySQL authentication"],
        ["FLUXBASE_PROJECT_ID", "Fluxbase Dashboard → Settings", "Identifies the Fluxbase project"],
        ["EMAIL_ADDRESS", "Gmail account", "Sender email for SMTP notifications"],
        ["EMAIL_PASSWORD", "Gmail → Security → App Passwords", "Gmail app password for SMTP"],
        ["SECRET_KEY", "Any random string", "Starlette session cookie signing"],
    ]
    story.append(colored_table(
        ["Variable", "Where to Get", "Used For"],
        env_rows,
        col_widths=[4.5*cm, 5.5*cm, 6.4*cm],
        header_color=C_AMBER
    ))

    story.append(Spacer(1, 0.5*cm))
    story.append(section_heading("Installation Steps", 2))
    install_steps = [
        "Clone or download the project: <code>cd C:\\Users\\hariv\\Downloads\\superfarmer</code>",
        "Create virtual environment: <code>python -m venv .venv</code> then <code>.venv\\Scripts\\activate</code>",
        "Install dependencies: <code>pip install -r requirements.txt</code>",
        "Create <code>.env</code> file and fill in all API keys listed above.",
        "Initialise database (once): <code>python database/init_db.py</code>",
        "Start the server: <code>python app.py</code>  — app runs at <b>http://127.0.0.1:5000</b>",
        "(Optional) Start MCP server: <code>python farmer_mcp_server.py</code>",
    ]
    for i, step in enumerate(install_steps, 1):
        story.append(para(f"<b>{i}.</b>  {step}"))
    story.append(PageBreak())

    # ── SECTION 10: MCP SERVER ──────────────────────────────────────────────────
    story.append(section_heading("10.  MCP Server (farmer_mcp_server.py)", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))
    story.append(para(
        "The <b>Model Context Protocol (MCP) Server</b> is a <code>FastMCP</code>-based "
        "stdio server that exposes farmer profile data as a callable AI tool. "
        "This allows external AI agent pipelines (e.g. Claude, GPT, other agents) to "
        "fetch real farmer data from Fluxbase and use it as grounded context."
    ))
    story.append(Spacer(1, 0.2*cm))
    mcp_code = (
        "from mcp.server.fastmcp import FastMCP\n"
        "mcp = FastMCP('FarmerProfile')\n\n"
        "@mcp.tool()\n"
        "def get_farmer_profile(farmer_id: int) -> str:\n"
        "    \"\"\"Fetch farmer's profile from Fluxbase.\"\"\"\n"
        "    p_res = execute_fluxbase_sql(\n"
        "        f'SELECT * FROM farmer_profile WHERE farmer_id={farmer_id}')\n"
        "    return json.dumps(p_res['rows'][0]) if p_res.get('rows') else '{}'\n\n"
        "if __name__ == '__main__':\n"
        "    mcp.run(transport='stdio')"
    )
    story.append(Paragraph(mcp_code.replace("\n", "<br/>"), styles["code"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(para(
        "The <b>SpatialPlannerAgent</b> uses this MCP tool internally to give Gemini real "
        "farmer context (water availability, farming goals, land size) when generating "
        "personalised field layouts."
    ))
    story.append(PageBreak())

    # ── SECTION 11: KEY AGENT DEEP DIVES ────────────────────────────────────────
    story.append(section_heading("11.  Agent Deep Dives", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))

    # 11.1 Crop Recommendation
    story.append(section_heading("11.1  CropRecommendationAgent", 2))
    story.append(para(
        "The crop recommendation engine uses <b>Ollama qwen2.5:7b</b> running locally "
        "as its primary inference engine. It receives a structured prompt containing:"
    ))
    story += bullet_list([
        "Soil type (Black, Alluvial, Red, Sandy, Laterite)",
        "Nitrogen (N), Phosphorus (P), Potassium (K) levels in mg/kg",
        "Average temperature (°C) and rainfall (mm)",
        "Water supply availability (Low / Medium / High)",
    ])
    story.append(para(
        "Ollama returns a <b>JSON array of 3 crop objects</b>, each containing: crop name, "
        "suitability score (70–99), why recommended, key features, nutritional importance, "
        "growing tips, ideal season, expected yield, and water need. If Ollama is offline or "
        "parsing fails, a deterministic rule-based fallback kicks in automatically."
    ))
    story.append(para(
        "Crops are restricted to a <b>curated whitelist</b> of 20 Indian crops to prevent "
        "hallucinations: Corn, Maize, Wheat, Rice, Tomato, Potato, Onion, Garlic, "
        "Sugarcane, Cotton, Sunflower, Mustard, Soybean, Groundnut, Chickpea, and Marigold."
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(section_heading("11.2  DiseaseDiagnosisAgent", 2))
    story.append(para(
        "The disease diagnosis agent implements a <b>3-path inference strategy</b>:"
    ))
    story += bullet_list([
        "<b>Path A (Image + Text):</b> Gemini 2.5 Flash Vision API analyses the uploaded leaf photo alongside the text symptom description. Returns JSON with diagnosis, confidence, treatment, prevention, and 2-4 product recommendations.",
        "<b>Path B (Text-only):</b> If no image is attached or Gemini fails, Groq LLaMA 3.1-8b-instant analyses the text description and returns the same JSON structure.",
        "<b>Path C (Claude fallback):</b> If both Gemini and Groq fail, Anthropic Claude Haiku 4.5 is used as a last resort.",
    ])
    story.append(para(
        "Product recommendations include <b>direct purchase links</b> to Amazon India and "
        "Flipkart, generated by URL-encoding the product search query."
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(section_heading("11.3  SpatialPlannerAgent (Digital Farm Twin)", 2))
    story.append(para(
        "The Digital Farm Twin generates an <b>optimised 2D hexagonal field layout</b> "
        "personalised to the farmer's soil, water, and location profile. Key features:"
    ))
    story += bullet_list([
        "Fetches farmer's Fluxbase profile (water availability, goals, land size) via the MCP tool",
        "Reads crop rotation history and nitrogen levels from previous plans",
        "Applies agricultural decision rules: nitrogen-fixing companion crops, water requirement matching, sunlight orientation",
        "Generates a hexagonal node placement map with zone divisions (main crop, companion, border, water point)",
        "Ollama qwen2.5:7b explains the layout rationale in plain language",
        "Returns JSON with hex coordinates, colours, zone labels, and yield estimates",
    ])

    story.append(Spacer(1, 0.3*cm))
    story.append(section_heading("11.4  SuperFarmerChatAgent (Multilingual AI)", 2))
    story.append(para(
        "The chat agent is a <b>decision-making agentic AI</b> with tool-calling capability. "
        "It operates in three tiers:"
    ))
    story += bullet_list([
        "<b>Tier 1 (Ollama agentic loop):</b> qwen2.5:7b can call tools like get_farmer_profile, get_crop_plan, get_weather, get_nutrient_risk, get_yield_comparison to fetch real Fluxbase data",
        "<b>Tier 2 (Groq fallback):</b> If Ollama is offline, Groq LLaMA 3.1-8b-instant responds with farmer context injected into the prompt",
        "<b>Tier 3 (Claude fallback):</b> Anthropic Claude Haiku used as final fallback",
        "<b>Languages supported:</b> Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Gujarati, Marathi, Punjabi, Odia, and English",
    ])

    story.append(PageBreak())

    # ── SECTION 12: EMAIL AUTOMATION ────────────────────────────────────────────
    story.append(section_heading("12.  Email Automation", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))
    story.append(para(
        "The <b>EmailAgent</b> uses Python's built-in <code>smtplib</code> with Gmail SMTP "
        "(TLS on port 587) to send HTML-formatted emails. All email operations run in "
        "<b>background threads</b> via <code>threading.Thread</code> to avoid blocking the "
        "HTTP response. Two types of emails are sent automatically:"
    ))
    story += bullet_list([
        "<b>Welcome Email:</b> Triggered on successful signup. Contains a personalised greeting, SuperFarmer branding, and a call-to-action button to explore the dashboard.",
        "<b>Login Alert Email:</b> Triggered on every successful login. Contains a security notice with instructions to change password if the login was unauthorised.",
    ])

    story.append(PageBreak())

    # ── SECTION 13: SECURITY ────────────────────────────────────────────────────
    story.append(section_heading("13.  Security & Authentication", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))

    sec_rows = [
        ["Password Storage", "Werkzeug generate_password_hash / check_password_hash (bcrypt)", "Passwords never stored in plaintext"],
        ["Session Management", "Starlette SessionMiddleware with itsdangerous signing", "Sessions are server-side signed cookies"],
        ["API Key Protection", "All keys stored in .env, loaded via python-dotenv", ".env is in .gitignore, never committed"],
        ["SQL Injection", "All user inputs sanitised via safe_str() escaping single quotes", "Prevents basic SQL injection"],
        ["Authorisation", "_logged_in() check on all protected routes", "Redirects to login if session missing"],
        ["Email Security", "Gmail App Password (not main account password)", "Limited-scope credential for SMTP"],
    ]
    story.append(colored_table(
        ["Security Aspect", "Implementation", "Notes"],
        sec_rows,
        col_widths=[4*cm, 7*cm, 5.4*cm],
        header_color=C_GREEN_DARK
    ))
    story.append(PageBreak())

    # ── SECTION 14: DEPLOYMENT & NOTES ──────────────────────────────────────────
    story.append(section_heading("14.  Deployment Notes", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))
    story += bullet_list([
        "<b>No local MySQL required</b> — Fluxbase cloud DB is used exclusively via REST API.",
        "<b>Fluxbase rate limit:</b> 30 requests / 10 seconds per project; SELECT queries cached for 15 seconds.",
        "The Groq API key env variable is named <code>GROK_API_KEY</code> (no 'Q') — match exactly in .env.",
        "If Groq is unavailable, both CropRecommendationAgent and CropPlannerAgent fall back to rule-based logic automatically.",
        "If Ollama is offline, crop recommendations fall back to rule-based logic; chat falls back to Groq/Claude.",
        "If Gemini Vision fails for SpatialPlannerAgent, a classic hexagonal grid is generated instead.",
        "The MCP server (<code>farmer_mcp_server.py</code>) must be running separately if external agents need to call it.",
        "For production deployment, replace the default SECRET_KEY with a strong random value.",
    ])

    story.append(Spacer(1, 0.5*cm))
    story.append(section_heading("15.  Summary", 1))
    story.append(divider(C_GREEN_LIGHT, 1.2))
    story.append(para(
        "SuperFarmer represents a comprehensive demonstration of <b>multi-agent AI systems</b> "
        "applied to a real-world domain with high social impact. By combining local LLMs (Ollama), "
        "cloud LLMs (Gemini, Groq, Claude), a cloud-native database (Fluxbase), real-time weather "
        "data (Tomorrow.io), and an extensible agent framework, the platform delivers a complete "
        "agricultural intelligence solution that is:"
    ))
    story += bullet_list([
        "<b>Resilient</b> — multi-tier LLM fallback chain ensures high availability",
        "<b>Scalable</b> — cloud-first architecture, no local MySQL required",
        "<b>Inclusive</b> — 10+ Indian languages supported in AI chat",
        "<b>Practical</b> — disease diagnosis, crop planning, weather advice, and more in one app",
        "<b>Extensible</b> — new agents can be added by implementing a method and registering an intent",
        "<b>Open</b> — MCP server exposes data for integration with any AI agent pipeline",
    ])

    story.append(Spacer(1, 1*cm))
    story.append(divider(C_GREEN_DARK, 2))
    story.append(Spacer(1, 0.3*cm))
    story.append(para("© 2026 SuperFarmer — Built for Indian Farmers 🇮🇳   |   harivardhan1100-cyber/superfarmer", "caption"))

    return story

# ── Document setup ─────────────────────────────────────────────────────────────

def generate_pdf(output_path="SuperFarmer_Project_Documentation.pdf"):
    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.8*cm,
        leftMargin=2.0*cm,
        topMargin=1.8*cm,
        bottomMargin=1.6*cm,
        title="SuperFarmer Project Documentation",
        author="Harivardhan",
        subject="AI Agricultural Intelligence Platform",
        creator="SuperFarmer PDF Generator",
    )

    # Cover page template (no header/footer)
    cover_frame = Frame(0, 0, W, H, id="cover")
    cover_template = PageTemplate(id="cover", frames=[cover_frame], onPage=_on_cover_page)

    # Normal page template
    normal_frame = Frame(
        2.25*cm, 1.2*cm,
        W - 2.25*cm - 1.8*cm,
        H - 1.2*cm - 1.8*cm,
        id="normal"
    )
    normal_template = PageTemplate(id="normal", frames=[normal_frame], onPage=_on_page)

    doc.addPageTemplates([cover_template, normal_template])

    story = build_story()
    # First page uses cover template, rest use normal
    from reportlab.platypus import NextPageTemplate
    story.insert(0, NextPageTemplate("cover"))
    # After first page break (end of cover), switch to normal
    # Find the first PageBreak and insert template switch after it
    for i, elem in enumerate(story):
        if isinstance(elem, PageBreak):
            story.insert(i + 1, NextPageTemplate("normal"))
            break

    doc.build(story)
    print(f"\nPDF generated: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_pdf(r"c:\Users\hariv\Downloads\superfarmer\SuperFarmer_Project_Documentation.pdf")
