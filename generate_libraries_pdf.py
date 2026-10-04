#!/usr/bin/env python3
"""
SuperFarmer — Libraries & Dependencies PDF
Lists every library used in the project with purpose explanation.
"""

from fpdf import FPDF
import datetime
import os


class LibPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, 'SuperFarmer - Libraries & Dependencies Reference', align='C')
        self.ln(3)
        self.set_draw_color(34, 139, 34)
        self.set_line_width(0.5)
        self.line(10, 11, 200, 11)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    def section_heading(self, text):
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(22, 101, 52)
        self.ln(3)
        self.cell(0, 9, self._s(text), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(34, 139, 34)
        self.set_line_width(0.35)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def sub_heading(self, text):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(30, 41, 59)
        self.ln(2)
        self.cell(0, 7, self._s(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.2, self._s(text))
        self.ln(1.5)

    def lib_entry(self, num, name, version, used_in, why):
        # Number + Name
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(22, 101, 52)
        self.cell(8, 6, str(num) + '.')
        self.set_text_color(30, 41, 59)
        self.cell(50, 6, self._s(name))
        # Version badge
        if version:
            self.set_font('Helvetica', '', 8)
            self.set_text_color(100, 116, 139)
            self.cell(30, 6, self._s(version))
        self.ln(6)
        # Used in
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(100, 116, 139)
        self.set_x(18)
        self.cell(0, 5, self._s(f'Used in: {used_in}'), new_x="LMARGIN", new_y="NEXT")
        # Why
        self.set_font('Helvetica', '', 9.5)
        self.set_text_color(40, 40, 40)
        self.set_x(18)
        self.multi_cell(self.w - 28, 5, self._s(why))
        self.ln(3)

    def std_entry(self, num, name, used_in, why):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(22, 101, 52)
        self.cell(8, 5.5, str(num) + '.')
        self.set_text_color(30, 41, 59)
        self.cell(30, 5.5, self._s(name))
        self.set_font('Helvetica', '', 9)
        self.set_text_color(100, 116, 139)
        self.cell(40, 5.5, self._s(used_in))
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, self._s(why))
        self.ln(1.5)

    @staticmethod
    def _s(text):
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


def generate():
    pdf = LibPDF()
    pdf.alias_nb_pages()

    # ── COVER ──
    pdf.add_page()
    pdf.ln(35)
    pdf.set_font('Helvetica', 'B', 30)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(0, 14, 'SuperFarmer', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 13)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 8, 'Multi-Agent Agricultural Decision Support System', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(34, 139, 34)
    pdf.set_line_width(0.7)
    pdf.line(65, pdf.get_y(), 145, pdf.get_y())
    pdf.ln(8)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, 'Libraries & Dependencies Reference', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 7, '13 Third-Party Libraries  |  3 Additional  |  15 Standard Library Modules', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, 'Total: 31 Libraries & Modules', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f'Generated: {datetime.datetime.now().strftime("%d %B %Y, %I:%M %p")}', align='C', new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1: THIRD-PARTY LIBRARIES (requirements.txt)
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading('Section 1: Third-Party Libraries (requirements.txt)')
    pdf.body(
        'These are the 13 core dependencies listed in requirements.txt. They are installed via pip '
        'and form the backbone of the SuperFarmer application.'
    )

    libs = [
        {
            'name': 'fastapi',
            'version': '>= 0.109.0',
            'used_in': 'app.py (main backend)',
            'why': 'The web framework powering all 15 HTTP routes. Handles form data extraction (Form(...)), '
                   'file uploads (UploadFile for leaf images), JSON responses (JSONResponse), and static file '
                   'serving. Chosen over Flask because FastAPI has native async/await support for non-blocking '
                   'I/O (critical for image upload in /disease) and automatic OpenAPI documentation generation.',
        },
        {
            'name': 'uvicorn[standard]',
            'version': '>= 0.27.0',
            'used_in': 'app.py (entry point: uvicorn.run)',
            'why': 'The ASGI server that runs the FastAPI application. The [standard] extra includes httptools '
                   '(fast HTTP parsing) and uvloop (high-performance event loop). Runs on port 5000 with '
                   'hot-reload enabled in development mode.',
        },
        {
            'name': 'jinja2',
            'version': '>= 3.1.2',
            'used_in': 'app.py (Jinja2Templates)',
            'why': 'Server-side HTML templating engine. Renders all 11 .html pages with dynamic data — crop '
                   'recommendations, disease diagnosis results, spatial twin layouts, 7-section reports. Supports '
                   'template inheritance (base.html), conditional rendering, and loop constructs. Chosen over '
                   'React/Vue because target users are Indian farmers on low-bandwidth connections; SSR sends '
                   'fully rendered HTML with zero client-side framework overhead.',
        },
        {
            'name': 'python-multipart',
            'version': '>= 0.0.6',
            'used_in': 'app.py (Form data + file upload)',
            'why': 'Required dependency for FastAPI to parse multipart/form-data requests. Without this, '
                   'Form(...) fields and UploadFile (used in /disease for leaf image upload) would fail. '
                   'This is a mandatory FastAPI dependency for any form-based application.',
        },
        {
            'name': 'starlette',
            'version': '>= 0.36.0',
            'used_in': 'app.py (SessionMiddleware)',
            'why': 'Provides SessionMiddleware for cookie-based encrypted user sessions. When a user logs in, '
                   'their user_id and farmer_id are stored in request.session (a signed cookie). FastAPI is '
                   'built on top of Starlette, but we explicitly import SessionMiddleware from starlette.middleware.sessions.',
        },
        {
            'name': 'itsdangerous',
            'version': '>= 2.1.2',
            'used_in': 'Internal (used by SessionMiddleware)',
            'why': 'Used internally by Starlette SessionMiddleware to cryptographically sign and encrypt session '
                   'cookies using the SECRET_KEY. Prevents session tampering — if a user modifies their cookie, '
                   'the signature verification fails and the session is rejected. Not imported directly in our code.',
        },
        {
            'name': 'requests',
            'version': '>= 2.31.0',
            'used_in': 'agents.py, config.py',
            'why': 'HTTP client library used for 4 external API calls: (1) Fluxbase Cloud MySQL REST API '
                   '(execute_fluxbase_sql), (2) Fluxbase AI Gateway /chat/completions endpoint, '
                   '(3) Tomorrow.io v4 weather forecast API, (4) OpenStreetMap Nominatim geocoding API. '
                   'Chosen over httpx/aiohttp for simplicity since most LLM calls are synchronous blocking calls.',
        },
        {
            'name': 'python-dotenv',
            'version': '>= 1.0.0',
            'used_in': 'app.py, config.py',
            'why': 'Loads environment variables from the .env file into os.environ at startup. Keeps sensitive '
                   'API keys (FLUXBASE_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, ANTHROPIC_API_KEY, GMAIL credentials) '
                   'out of source code. Called with load_dotenv(override=True) to ensure .env values take precedence.',
        },
        {
            'name': 'openai',
            'version': '>= 1.12.0',
            'used_in': 'agents.py (_call_flux, _call_groq, _call_zhipu)',
            'why': 'OpenAI-compatible Python SDK used as a GENERIC CLIENT for 3 different providers — NOT for '
                   'OpenAI itself. (1) Fluxbase AI Gateway (base_url="https://fluxbasedb.me/api/v1"), '
                   '(2) Zhipu AI GLM-4 (base_url="https://open.bigmodel.cn/api/paas/v4"), '
                   '(3) Groq Qwen (base_url="https://api.groq.com/openai/v1"). '
                   'The OpenAI SDK works with any OpenAI-compatible API by changing the base_url parameter.',
        },
        {
            'name': 'anthropic',
            'version': '>= 0.18.0',
            'used_in': 'agents.py (_call_claude)',
            'why': 'Anthropic official Python SDK. Calls Claude Haiku 4.5 as the FINAL LLM fallback (Tier 4). '
                   'Only invoked when Fluxbase Gateway, Zhipu GLM-4, AND Groq Qwen have all failed. Uses '
                   'client.messages.create() with model="claude-sonnet-4-20250514". Ensures the system has a last '
                   'resort before falling back to deterministic rules.',
        },
        {
            'name': 'google-generativeai',
            'version': '>= 0.4.0',
            'used_in': 'agents.py (DiseaseDiagnosisAgent)',
            'why': 'Google Gemini Python SDK. Used as a VISION FALLBACK in DiseaseDiagnosisAgent. When Fluxbase '
                   'vision models (flux-omni, flux-max) fail, calls gemini-2.5-flash natively with PIL.Image '
                   'objects for multimodal leaf disease diagnosis. Configured with '
                   'response_mime_type="application/json" to force structured JSON output.',
        },
        {
            'name': 'Pillow',
            'version': '>= 10.0.0',
            'used_in': 'agents.py (DiseaseDiagnosisAgent)',
            'why': 'Python Imaging Library (PIL fork). Opens uploaded leaf images as PIL.Image objects, which is '
                   'the required input format for Google Gemini native vision API. The Gemini SDK accepts '
                   'PIL.Image objects directly in generate_content([prompt, img]) — it cannot accept raw bytes.',
        },
        {
            'name': 'werkzeug',
            'version': '>= 3.0.0',
            'used_in': 'agents.py (UserAuthAgent)',
            'why': 'Password security library. generate_password_hash() creates scrypt/pbkdf2 hashes on signup. '
                   'check_password_hash() verifies on login. The UserAuthAgent._verify_password() method supports '
                   'multi-format hash verification: bcrypt ($2a$/$2b$), Werkzeug scrypt/pbkdf2, and legacy '
                   'plaintext — ensuring backward compatibility regardless of which algorithm was used at signup.',
        },
    ]

    for i, lib in enumerate(libs, 1):
        pdf.lib_entry(i, lib['name'], lib['version'], lib['used_in'], lib['why'])

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2: ADDITIONAL LIBRARIES (not in requirements.txt)
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading('Section 2: Additional Libraries (Not in requirements.txt)')
    pdf.body(
        'These libraries are used in specific modules but are not listed in requirements.txt. '
        'They are installed separately or are optional dependencies.'
    )

    extra_libs = [
        {
            'name': 'mcp (FastMCP)',
            'version': 'Latest',
            'used_in': 'farmer_mcp_server.py',
            'why': 'Model Context Protocol server framework. Exposes the get_farmer_profile tool so external '
                   'AI agents (Claude Desktop, GPT, Cursor, etc.) can query farmer data from the Fluxbase '
                   'database. Runs on stdio transport. Installed via: pip install mcp[cli].',
        },
        {
            'name': 'bcrypt',
            'version': 'Optional',
            'used_in': 'agents.py (UserAuthAgent._verify_password)',
            'why': 'Optional import for backward compatibility. Handles bcrypt password hashes ($2a$/$2b$) for '
                   'users who signed up when bcrypt was the default hasher. If bcrypt is not installed, the '
                   'system gracefully falls back to Werkzeug-only verification.',
        },
        {
            'name': 'fpdf2',
            'version': 'Latest',
            'used_in': 'generate_superfarmer_pdf.py, generate_architecture_pdf.py',
            'why': 'PDF generation library. Creates the 40+ page documentation PDFs, architecture explanation '
                   'PDFs, and this libraries reference PDF. Supports tables, code blocks, multi-column layouts, '
                   'and automatic page breaks.',
        },
    ]

    for i, lib in enumerate(extra_libs, 14):
        pdf.lib_entry(i, lib['name'], lib['version'], lib['used_in'], lib['why'])

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3: STANDARD LIBRARY MODULES
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading('Section 3: Python Standard Library Modules')
    pdf.body(
        'These 15 modules are part of Python\'s standard library (no pip install needed). '
        'They handle I/O, math, security, encoding, email construction, and concurrency.'
    )

    std_libs = [
        ('os', 'Everywhere', 'Environment variable access (os.environ.get for API keys), file path manipulation (os.path.join, os.path.exists for template/image discovery)'),
        ('re', 'agents.py, app.py', 'Regex-based JSON extraction from LLM responses. Patterns: re.search(r\'\\[.*?\\]\', text) for crop arrays, re.search(r\'\\{.*\\}\', text, re.DOTALL) for plan objects. Also validates email format in /send-report-email.'),
        ('time', 'agents.py', 'Performance timing via time.time(). Measures LLM response latency for each agent call (e.g., "Plan ready in 2.3s"). Also used for time.strftime() in report generation timestamps.'),
        ('json', 'Everywhere', 'JSON serialization/deserialization. Parses LLM responses (json.loads), Fluxbase API results, test datasets (crop_recommendation_testset.json), and MCP tool responses.'),
        ('base64', 'agents.py', 'Base64-encodes uploaded leaf images for multimodal LLM vision requests. Creates data:image/jpeg;base64,... URIs for the OpenAI-compatible image_url message format.'),
        ('smtplib', 'agents.py (EmailAgent)', 'Establishes Gmail SMTP connection on port 587 with STARTTLS encryption. Authenticates with app-specific password. Sends transactional emails (welcome, login alerts, reports).'),
        ('email.mime.text', 'agents.py (EmailAgent)', 'Constructs MIMEText objects for HTML email body and plaintext fallback in multipart/alternative messages.'),
        ('email.mime.multipart', 'agents.py (EmailAgent)', 'Creates MIMEMultipart("related") container that bundles HTML body + inline logo image (RFC 2387) into a single email message.'),
        ('email.mime.image', 'agents.py (EmailAgent)', 'Attaches the SuperFarmer logo as an inline image with Content-ID: superfarmer_logo. The HTML references it via cid:superfarmer_logo.'),
        ('threading', 'app.py', 'Fire-and-forget async email sending. threading.Thread(target=send_async_email).start() dispatches emails without blocking the HTTP response to the user.'),
        ('math', 'agents.py (SpatialPlanner)', 'Hexagonal grid geometry: math.floor(spacing * 0.866) for hex row vertical offset (based on equilateral triangle height). math.sqrt() for converting acres to field dimensions in meters.'),
        ('builtins', 'agents.py', 'Monkey-patches the global print() function with safe_print() to prevent Windows terminal crashes when logging emojis/unicode characters (UnicodeEncodeError on cp1252 codepage).'),
        ('io', 'app.py', 'io.BytesIO wraps uploaded file bytes into a file-like object that DiseaseDiagnosisAgent can call .read() and .seek() on, simulating a real file handle.'),
        ('urllib.parse', 'agents.py (DiseaseAgent)', 'quote_plus() URL-encodes product names (e.g., "Mancozeb 75 WP") into safe query strings for auto-generated Amazon.in and Flipkart.com search URLs.'),
        ('difflib', 'evaluate_disease_diagnosis.py', 'SequenceMatcher for fuzzy string matching. Compares AI-diagnosed disease name against ground truth with threshold >= 0.40. Handles partial matches and spelling variations.'),
    ]

    for i, (name, used_in, why) in enumerate(std_libs, 17):
        pdf.lib_entry(i, name, '', used_in, why)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: LIBRARY ARCHITECTURE DIAGRAM
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading('Section 4: Library-to-Layer Mapping')
    pdf.body(
        'This section maps each library to its architectural layer, showing how the 31 libraries '
        'and modules work together across the 7-layer SuperFarmer architecture.'
    )

    layers = [
        ('FRONTEND LAYER', [
            'jinja2 - Server-side HTML rendering (11 templates)',
            'Three.js - 3D hex-grid rendering (loaded via CDN in spatial_planner.html)',
        ]),
        ('WEB SERVER LAYER', [
            'fastapi - Route handling, form parsing, JSON responses',
            'uvicorn[standard] - ASGI server (port 5000)',
            'python-multipart - Form + file upload parsing',
            'starlette - SessionMiddleware for encrypted cookies',
            'itsdangerous - Cookie signing/encryption (internal)',
        ]),
        ('AGENT LAYER (AI)', [
            'openai - Generic client for Fluxbase/Zhipu/Groq (OpenAI-compatible)',
            'anthropic - Claude Haiku 4.5 (Tier 4 fallback)',
            'google-generativeai - Gemini 2.5 Flash (vision fallback)',
            'Pillow - PIL.Image for Gemini native vision API',
        ]),
        ('AGENT LAYER (RULE-BASED)', [
            'math - Hex geometry (0.866 row offset, sqrt for field dims)',
            're - JSON extraction from LLM responses',
            'json - Parse/serialize all structured data',
        ]),
        ('AGENT LAYER (UTILITY)', [
            'werkzeug - Password hashing (scrypt/pbkdf2)',
            'bcrypt - Legacy password verification (optional)',
            'smtplib + email.mime.* - Gmail SMTP email construction',
            'requests - HTTP client for 4 external APIs',
        ]),
        ('DATABASE LAYER', [
            'requests - POST to Fluxbase Cloud MySQL REST API',
            'python-dotenv - Loads API keys from .env file',
        ]),
        ('MCP LAYER', [
            'mcp (FastMCP) - Model Context Protocol server',
        ]),
    ]

    for layer_name, items in layers:
        pdf.sub_heading(layer_name)
        for item in items:
            self_x = pdf.get_x()
            pdf.set_x(self_x + 10)
            pdf.set_font('Helvetica', '', 9.5)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(3, 5, '-')
            pdf.multi_cell(0, 5, pdf._s(item))
            pdf.ln(0.5)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5: SUMMARY TABLE
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading('Section 5: Quick Reference Summary')

    pdf.sub_heading('Total Count')
    pdf.body(
        'Third-party (requirements.txt): 13 libraries\n'
        'Additional (not in requirements.txt): 3 libraries\n'
        'Python Standard Library: 15 modules\n'
        'Grand Total: 31 libraries & modules'
    )

    pdf.sub_heading('Interview One-Liner')
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(22, 101, 52)
    pdf.multi_cell(0, 5.5, pdf._s(
        '"SuperFarmer uses 13 third-party libraries and 15 standard library modules. The core stack is '
        'FastAPI + Uvicorn for the async web server, Jinja2 for SSR templates, requests for 4 external '
        'REST APIs (Fluxbase SQL, Fluxbase AI, Tomorrow.io, Nominatim), the OpenAI SDK as a generic '
        'client for Zhipu AI and Groq (not for OpenAI itself), Anthropic SDK for Claude fallback, '
        'Google Generative AI + Pillow for Gemini vision fallback, Werkzeug for password hashing, '
        'python-dotenv for secrets management, and FastMCP for the Model Context Protocol server."'
    ))

    # ── SAVE ──
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SuperFarmer_Libraries_Reference.pdf')
    pdf.output(out)
    print(f"\n{'='*60}")
    print(f"PDF generated successfully!")
    print(f"Output: {out}")
    print(f"{'='*60}")


if __name__ == '__main__':
    generate()
