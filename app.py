from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from agents.agents import OrchestratorAgent
from dotenv import load_dotenv
import os
import threading
import re
import json

load_dotenv(override=True)


app = FastAPI(title="SuperFarmer - AI Agricultural Intelligence")

# --- Middleware ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'superfarmer-super-secret')
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# --- Static files & Templates ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Register a url_for helper for Jinja2 templates (maps route names → paths)
_ROUTE_MAP = {
    'home':             '/',
    'login':            '/login',
    'signup':           '/signup',
    'logout':           '/logout',
    'intake':           '/intake',
    'recommendation':   '/recommendation',
    'plan':             '/plan',
    'disease':          '/disease',
    'spatial_planner':  '/spatial-planner',
    'report':           '/report',
    'benchmarks':       '/benchmarks',
    'static':           '/static',
}

def _template_url_for(endpoint: str, filename: str = '', **kwargs) -> str:
    """Jinja2 helper that mimics Flask's url_for()."""
    if endpoint == 'static':
        return f'/static/{filename}'
    return _ROUTE_MAP.get(endpoint, '/')

templates.env.globals['url_for'] = _template_url_for

# --- Orchestrator ---
orchestrator = OrchestratorAgent()


# ── Helpers ─────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_NOTIFICATION_IMAGE = os.path.join(BASE_DIR, 'images', 'auth_logo.png')

def send_async_email(email_data):
    orchestrator.route_request('send_email', email_data)


def _render(request: Request, template: str, **ctx):
    """Shortcut: renders a Jinja2 template and passes session + extra ctx."""
    ctx.setdefault('session', request.session)
    ctx['request'] = request
    try:
        return templates.TemplateResponse(template, ctx)
    except TypeError:
        return templates.TemplateResponse(name=template, context=ctx, request=request)



def _redirect(route_name: str):
    return RedirectResponse(url=_ROUTE_MAP[route_name], status_code=303)


def _logged_in(request: Request) -> bool:
    return 'user_id' in request.session


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    return _render(request, 'home.html', logged_in=_logged_in(request))


# ── Signup ───────────────────────────────────────────────────────────────────

@app.get('/signup', response_class=HTMLResponse)
def signup_get(request: Request):
    return _render(request, 'signup.html')


@app.post('/signup', response_class=HTMLResponse)
def signup_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    data = {'email': email, 'password': password}
    res = orchestrator.route_request('signup', data)

    if res.get('success'):
        request.session['user_id'] = res['user_id']

        welcome_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Welcome to SuperFarmer</title>
</head>
<body style="margin: 0; padding: 20px; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; background-color: #f1f5f9; color: #1e293b;">
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 540px; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; margin: 0 auto;">
        <tr>
            <td align="center" style="background: linear-gradient(135deg, #166534 0%, #15803d 100%); padding: 28px 20px; text-align: center;">
                <img src="cid:superfarmer_logo" alt="SuperFarmer Logo" width="125" height="125" style="display: block; margin: 0 auto; width: 125px; height: 125px; border-radius: 50%; background: #ffffff; padding: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
                <h1 style="color: #ffffff; margin: 14px 0 0 0; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">SuperFarmer</h1>
                <p style="color: #bbf7d0; margin: 4px 0 0 0; font-size: 13px;">AI-Driven Precision Agriculture</p>
            </td>
        </tr>
        <tr>
            <td style="padding: 30px 28px;">
                <h2 style="color: #15803d; margin-top: 0; font-size: 19px; font-weight: 600;">Welcome to SuperFarmer! 🌱</h2>
                <p style="font-size: 15px; line-height: 1.6; color: #334155; margin-top: 12px;">Hello,</p>
                <p style="font-size: 15px; line-height: 1.6; color: #334155;">Thank you for registering with <b>SuperFarmer</b>. Your account has been created successfully (<code>{email}</code>).</p>
                <p style="font-size: 15px; line-height: 1.6; color: #334155;">You can now log in to explore personalized crop recommendations, real-time weather alerts, disease diagnosis, and spatial farm planning.</p>
                <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 14px 18px; border-radius: 6px; margin: 22px 0;">
                    <p style="margin: 0; font-size: 13px; color: #166534; line-height: 1.5;">
                        🚀 <strong>Next Step:</strong> Complete your farm intake profile to generate your customized soil & crop management strategy.
                    </p>
                </div>
                <p style="font-size: 14px; line-height: 1.6; color: #334155; margin-bottom: 0;">
                    Best regards,<br>
                    <strong style="color: #15803d;">The SuperFarmer Team</strong>
                </p>
            </td>
        </tr>
        <tr>
            <td style="background-color: #f8fafc; padding: 14px 28px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8;">
                © 2026 SuperFarmer • Empowering Farmers with Agentic AI
            </td>
        </tr>
    </table>
</body>
</html>"""
        threading.Thread(target=send_async_email, args=({
            'to_email': email,
            'subject': 'Welcome to SuperFarmer!',
            'body': welcome_html,
            'image_path': DEFAULT_NOTIFICATION_IMAGE
        },)).start()

        return _redirect('intake')
    else:
        return _render(request, 'signup.html', error=res.get('error'))


# ── Login ────────────────────────────────────────────────────────────────────

@app.get('/login', response_class=HTMLResponse)
def login_get(request: Request):
    return _render(request, 'login.html')


@app.post('/login', response_class=HTMLResponse)
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    data = {'email': email, 'password': password}
    res = orchestrator.route_request('login', data)

    if res.get('success'):
        request.session['user_id'] = res['user_id']

        login_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Security Alert - SuperFarmer</title>
</head>
<body style="margin: 0; padding: 20px; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; background-color: #f1f5f9; color: #1e293b;">
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 540px; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; margin: 0 auto;">
        <tr>
            <td align="center" style="background: linear-gradient(135deg, #166534 0%, #15803d 100%); padding: 28px 20px; text-align: center;">
                <img src="cid:superfarmer_logo" alt="SuperFarmer Logo" width="125" height="125" style="display: block; margin: 0 auto; width: 125px; height: 125px; border-radius: 50%; background: #ffffff; padding: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
                <h1 style="color: #ffffff; margin: 14px 0 0 0; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">SuperFarmer</h1>
                <p style="color: #bbf7d0; margin: 4px 0 0 0; font-size: 13px;">Account Security Center</p>
            </td>
        </tr>
        <tr>
            <td style="padding: 30px 28px;">
                <h2 style="color: #0369a1; margin-top: 0; font-size: 19px; font-weight: 600;">Security Alert: New Login to SuperFarmer</h2>
                <p style="font-size: 15px; line-height: 1.6; color: #334155; margin-top: 12px;">Hello,</p>
                <p style="font-size: 15px; line-height: 1.6; color: #334155;">We detected a new login to your <b>SuperFarmer</b> account (<code>{email}</code>).</p>
                <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 14px 18px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 13px; color: #92400e; line-height: 1.5;">
                        ⚠️ <strong>Security Notice:</strong> If you did not perform this login, please update your account password immediately to secure your profile.
                    </p>
                </div>
                <p style="font-size: 14px; line-height: 1.6; color: #334155; margin-bottom: 0;">
                    Best regards,<br>
                    <strong style="color: #0369a1;">SuperFarmer Security Team</strong>
                </p>
            </td>
        </tr>
        <tr>
            <td style="background-color: #f8fafc; padding: 14px 28px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8;">
                © 2026 SuperFarmer • Automated Security Notification
            </td>
        </tr>
    </table>
</body>
</html>"""
        threading.Thread(target=send_async_email, args=({
            'to_email': email,
            'subject': 'New Login Alert - SuperFarmer',
            'body': login_html,
            'image_path': DEFAULT_NOTIFICATION_IMAGE
        },)).start()

        # Try to grab existing farmer profile
        from agents.agents import UserAuthAgent
        farmer_id = UserAuthAgent.get_farmer_profile_by_user(res['user_id'])
        if farmer_id:
            request.session['farmer_id'] = farmer_id
            return _redirect('recommendation')
        else:
            return _redirect('intake')
    else:
        return _render(request, 'login.html', error=res.get('error'))


# ── Logout ───────────────────────────────────────────────────────────────────

@app.get('/logout')
def logout(request: Request):
    request.session.clear()
    return _redirect('home')


# ── Intake ───────────────────────────────────────────────────────────────────

@app.get('/intake', response_class=HTMLResponse)
def intake_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    return _render(request, 'intake.html')


@app.post('/intake', response_class=HTMLResponse)
def intake_post(
    request: Request,
    name: str = Form(...),
    land_size: str = Form(...),
    location: str = Form(...),
    water: str = Form(...),
    goals: str = Form(...)
):
    if not _logged_in(request):
        return _redirect('login')

    data = {
        'user_id': request.session['user_id'],
        'name': name,
        'land_size': land_size,
        'location': location,
        'water': water,
        'goals': goals
    }
    farmer_id = orchestrator.route_request('intake', data)
    request.session['farmer_id'] = farmer_id
    return _redirect('recommendation')


# ── Recommendation ───────────────────────────────────────────────────────────

@app.get('/recommendation', response_class=HTMLResponse)
def recommendation_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        from agents.agents import UserAuthAgent
        fid = UserAuthAgent.get_farmer_profile_by_user(request.session['user_id'])
        request.session['farmer_id'] = fid if fid else request.session['user_id']
        
    last_rec = request.session.get('last_rec')
    # Only pass recommendations through if it's a proper result dict (has crops_str key)
    if isinstance(last_rec, dict) and 'crops_str' not in last_rec:
        last_rec = None

    return _render(request, 'recommendation.html', recommendations=last_rec)


@app.post('/recommendation', response_class=HTMLResponse)
def recommendation_post(
    request: Request,
    soil_type: str = Form(...),
    n: float = Form(...),
    p: float = Form(...),
    k: float = Form(...),
    temp: float = Form(...),
    rain: float = Form(...),
    water_const: str = Form(...)
):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        from agents.agents import UserAuthAgent
        fid = UserAuthAgent.get_farmer_profile_by_user(request.session['user_id'])
        request.session['farmer_id'] = fid if fid else request.session['user_id']

    data = {
        'farmer_id': request.session['farmer_id'],
        'soil_type': soil_type,
        'n': n, 'p': p, 'k': k,
        'temp': temp, 'rain': rain,
        'water_const': water_const
    }
    rec = orchestrator.route_request('recommendation', data)
    # rec is now a dict: {crops_str, crops, crop_details}
    # Starlette sessions can't serialise custom objects, so convert to plain dict
    rec_plain = dict(rec) if isinstance(rec, dict) else {"crops_str": str(rec), "crops": [], "crop_details": []}
    request.session['last_rec'] = rec_plain
    request.session['soil_data'] = data
    return _render(request, 'recommendation.html', recommendations=rec_plain)


# ── AI Model Benchmarks & Accuracy Metrics ──────────────────────────────────

@app.get('/benchmarks', response_class=HTMLResponse)
def benchmarks_get(request: Request):
    crop_cases = []
    disease_cases = []
    try:
        crop_path = os.path.join(os.path.dirname(__file__), 'evaluation', 'test_data', 'crop_recommendation_testset.json')
        if os.path.exists(crop_path):
            with open(crop_path, 'r', encoding='utf-8') as f:
                crop_cases = json.load(f).get('cases', [])
    except Exception:
        pass

    try:
        disease_path = os.path.join(os.path.dirname(__file__), 'evaluation', 'test_data', 'disease_diagnosis_testset.json')
        if os.path.exists(disease_path):
            with open(disease_path, 'r', encoding='utf-8') as f:
                disease_cases = json.load(f).get('cases', [])
    except Exception:
        pass

    return _render(request, 'benchmarks.html', crop_cases=crop_cases, disease_cases=disease_cases)


# ── Plan ─────────────────────────────────────────────────────────────────────

@app.get('/plan', response_class=HTMLResponse)
def plan_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        from agents.agents import UserAuthAgent
        fid = UserAuthAgent.get_farmer_profile_by_user(request.session['user_id'])
        request.session['farmer_id'] = fid if fid else request.session['user_id']
    return _render(request, 'plan.html')


@app.post('/plan', response_class=HTMLResponse)
def plan_post(
    request: Request,
    crop_name: str = Form(...)
):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        from agents.agents import UserAuthAgent
        fid = UserAuthAgent.get_farmer_profile_by_user(request.session['user_id'])
        request.session['farmer_id'] = fid if fid else request.session['user_id']

    data = {
        'farmer_id': request.session['farmer_id'],
        'crop_name': crop_name
    }
    plan_data = orchestrator.route_request('plan', data)
    return _render(request, 'plan.html', plan=plan_data)


# ── Disease Diagnosis ────────────────────────────────────────────────────────

@app.get('/disease', response_class=HTMLResponse)
def disease_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    return _render(request, 'disease.html')


@app.post('/disease', response_class=HTMLResponse)
async def disease_post(
    request: Request,
    leaf_text: str = Form(default=''),
    leaf_image: UploadFile = File(default=None)
):
    if not _logged_in(request):
        return _redirect('login')

    # Wrap UploadFile so DiseaseDiagnosisAgent can call .filename and open it
    image_obj = None
    if leaf_image and leaf_image.filename:
        import io
        contents = await leaf_image.read()
        image_obj = io.BytesIO(contents)
        image_obj.filename = leaf_image.filename

    data = {'leaf_text': leaf_text, 'leaf_image': image_obj}
    diagnosis = orchestrator.route_request('diagnose', data)
    request.session['last_diagnosis'] = diagnosis
    return _render(request, 'disease.html', diagnosis=diagnosis)








# ── Spatial Planner ──────────────────────────────────────────────────────────

@app.get('/spatial-planner', response_class=HTMLResponse)
def spatial_planner_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        return _redirect('home')
    return _render(request, 'spatial_planner.html')


@app.post('/spatial-planner')
async def spatial_planner_post(request: Request):
    if not _logged_in(request):
        return JSONResponse({'error': 'Unauthorized'}, status_code=401)
    if not request.session.get('farmer_id'):
        return JSONResponse({'error': 'No farmer profile'}, status_code=400)

    data = await request.json()
    if not data:
        return JSONResponse({'error': 'Invalid data format'}, status_code=400)

    layout_data = orchestrator.route_request('spatial_plan', {
        **data,
        'farmer_id': request.session.get('farmer_id', 0)
    })
    return JSONResponse(layout_data)



# ── Report ───────────────────────────────────────────────────────────────────

def _get_report_context(request: Request) -> dict:
    """Helper to collect authentic session and profile context for report generation."""
    return {
        'farmer_id': request.session.get('farmer_id'),
        'user_id': request.session.get('user_id'),
        'soil_data': request.session.get('soil_data'),
        'last_diagnosis': request.session.get('last_diagnosis')
    }

@app.get('/report', response_class=HTMLResponse)
def report_get(request: Request, format: str = None):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        return _redirect('home')
    if format == 'json' or request.headers.get('accept') == 'application/json':
        report_data = orchestrator.route_request('report', _get_report_context(request))
        return JSONResponse(report_data)
    return _render(request, 'report.html')

@app.post('/report')
async def report_post(request: Request):
    if not _logged_in(request):
        return JSONResponse({'error': 'Unauthorized'}, status_code=401)
    if not request.session.get('farmer_id'):
        return JSONResponse({'error': 'No farmer profile'}, status_code=400)

    report_data = orchestrator.route_request('report', _get_report_context(request))
    return JSONResponse(report_data)

@app.post('/generate-report')
async def generate_report_post(request: Request):
    if not _logged_in(request):
        return JSONResponse({'error': 'Unauthorized'}, status_code=401)
    if not request.session.get('farmer_id'):
        return JSONResponse({'error': 'No farmer profile'}, status_code=400)

    report_data = orchestrator.route_request('report', _get_report_context(request))
    return JSONResponse(report_data)


@app.post('/send-report-email')
async def send_report_email_post(request: Request):
    if not _logged_in(request):
        return JSONResponse({'error': 'Unauthorized'}, status_code=401)
    if not request.session.get('farmer_id'):
        return JSONResponse({'error': 'No farmer profile found. Please complete farm intake.'}, status_code=400)

    try:
        data = await request.json()
    except Exception:
        data = {}

    recipient_email = (data.get('recipient_email') or '').strip()
    subject = (data.get('subject') or 'SuperFarmer - Field Advisory Report').strip()
    custom_notes = (data.get('notes') or '').strip()

    # Strict email validation
    if not recipient_email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', recipient_email):
        return JSONResponse({'error': 'Please enter a valid recipient email address.'}, status_code=400)

    from agents.agents import ReportAgent, EmailAgent
    report_data = orchestrator.route_request('report', _get_report_context(request))
    html_body = ReportAgent.build_html_email(report_data, custom_notes=custom_notes)

    # Deliver via EmailAgent
    success = EmailAgent.send_email(
        to_email=recipient_email,
        subject=subject,
        body=html_body,
        image_path=DEFAULT_NOTIFICATION_IMAGE
    )

    if success:
        return JSONResponse({
            'success': True,
            'message': f'Field Advisory Report sent successfully to {recipient_email}!'
        })
    else:
        return JSONResponse({
            'error': 'Failed to send email. Please check server email credentials or network connection.'
        }, status_code=500)



# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import uvicorn
    # Trigger reload with updated Flux models routing
    uvicorn.run('app:app', host='127.0.0.1', port=5000, reload=True)
