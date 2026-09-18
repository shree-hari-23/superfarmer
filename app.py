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
    'chat':             '/chat',
    'spatial_planner':  '/spatial-planner',
    'report':           '/report',
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
</head>
<body style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #222222; line-height: 1.6; margin: 20px;">
    <h2 style="color: #2E7D32;">Welcome to SuperFarmer!</h2>
    <p>Hello,</p>
    <p>Thank you for registering with <b>SuperFarmer</b>. Your account has been created successfully.</p>
    <p>You can now log in to explore personalized crop recommendations, real-time weather alerts, disease diagnosis, and spatial farm planning.</p>
    <br>
    <p>Best regards,<br>
    <strong>The SuperFarmer Team</strong></p>
</body>
</html>"""
        threading.Thread(target=send_async_email, args=({
            'to_email': email,
            'subject': 'Welcome to SuperFarmer!',
            'body': welcome_html
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
</head>
<body style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #222222; line-height: 1.6; margin: 20px;">
    <h2 style="color: #1976D2;">Security Alert: New Login to SuperFarmer</h2>
    <p>Hello,</p>
    <p>We detected a new login to your <b>SuperFarmer</b> account (<code>{email}</code>).</p>
    <p><b>Note:</b> If you did not perform this login, please update your account password immediately to secure your profile.</p>
    <br>
    <p>Best regards,<br>
    <strong>SuperFarmer Security Team</strong></p>
</body>
</html>"""
        threading.Thread(target=send_async_email, args=({
            'to_email': email,
            'subject': 'New Login Alert - SuperFarmer',
            'body': login_html
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
        return _redirect('intake')
        
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
        return _redirect('intake')

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


# ── Plan ─────────────────────────────────────────────────────────────────────

@app.get('/plan', response_class=HTMLResponse)
def plan_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        return _redirect('intake')
    return _render(request, 'plan.html')


@app.post('/plan', response_class=HTMLResponse)
def plan_post(
    request: Request,
    crop_name: str = Form(...)
):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        return _redirect('intake')

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
    return _render(request, 'disease.html', diagnosis=diagnosis)





# ── Chat (JSON API) ──────────────────────────────────────────────────────────

@app.get('/chat', response_class=HTMLResponse)
def chat_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    return _render(request, 'chat.html')


@app.post('/chat')
async def chat_post(request: Request):
    if not _logged_in(request):
        return JSONResponse({'error': 'Unauthorized'}, status_code=401)

    data = await request.json()
    if not data or 'message' not in data:
        return JSONResponse({'error': 'No message provided'}, status_code=400)

    # Inject farmer_id from session so the agent can fetch real farmer memory
    data['farmer_id'] = request.session.get('farmer_id')

    reply = orchestrator.route_request('chat', data)
    return JSONResponse({'reply': reply})



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

@app.get('/report', response_class=HTMLResponse)
def report_get(request: Request, format: str = None):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        return _redirect('home')
    if format == 'json' or request.headers.get('accept') == 'application/json':
        report_data = orchestrator.route_request('report', {'farmer_id': request.session['farmer_id']})
        return JSONResponse(report_data)
    return _render(request, 'report.html')

@app.post('/report')
async def report_post(request: Request):
    if not _logged_in(request):
        return JSONResponse({'error': 'Unauthorized'}, status_code=401)
    if not request.session.get('farmer_id'):
        return JSONResponse({'error': 'No farmer profile'}, status_code=400)

    report_data = orchestrator.route_request('report', {'farmer_id': request.session['farmer_id']})
    return JSONResponse(report_data)

@app.post('/generate-report')
async def generate_report_post(request: Request):
    if not _logged_in(request):
        return JSONResponse({'error': 'Unauthorized'}, status_code=401)
    if not request.session.get('farmer_id'):
        return JSONResponse({'error': 'No farmer profile'}, status_code=400)

    report_data = orchestrator.route_request('report', {'farmer_id': request.session['farmer_id']})
    return JSONResponse(report_data)



# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='127.0.0.1', port=5000, reload=True)
