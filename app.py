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
    'weather':          '/weather',
    'spatial_planner':  '/spatial-planner',
    'yield_comparison': '/yield-comparison',
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
    """Shortcut: renders a Jinja2 template and passes session + extra ctx.
    Starlette 1.x signature: TemplateResponse(request, name, context={...})
    The 'request' key is NOT placed inside context — it is the first positional arg.
    """
    ctx.setdefault('session', request.session)
    return templates.TemplateResponse(request, template, ctx)


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

        welcome_html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; padding: 20px; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2e7d32; margin: 0;">🌱 Welcome to SuperFarmer!</h1>
                </div>
                <p style="font-size: 16px; line-height: 1.6;">Hello,</p>
                <p style="font-size: 16px; line-height: 1.6;">Thank you for joining <strong>SuperFarmer</strong>. We are thrilled to have you on board.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #2e7d32; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Explore Your Dashboard</a>
                </div>
                <hr style="border: 0; height: 1px; background-color: #e0e0e0; margin: 30px 0;">
                <p style="font-size: 12px; color: #777; text-align: center;">© 2026 SuperFarmer. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
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

        login_html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; padding: 20px; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #1976d2; margin: 0;">🛡️ New Login Alert</h1>
                </div>
                <p style="font-size: 16px; line-height: 1.6;">Hello,</p>
                <p style="font-size: 16px; line-height: 1.6;">We noticed a new login to your <strong>SuperFarmer</strong> account.</p>
                <div style="background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; border-radius: 5px; padding: 15px; margin: 25px 0;">
                    <p style="margin: 0; font-size: 14px;"><strong>Note:</strong> If you did not authorize this login, please change your password immediately.</p>
                </div>
                <hr style="border: 0; height: 1px; background-color: #e0e0e0; margin: 30px 0;">
                <p style="font-size: 12px; color: #777; text-align: center;">© 2026 SuperFarmer. Account Security Team.</p>
            </div>
        </body>
        </html>
        """
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
    return _render(request, 'recommendation.html', recommendations=request.session.get('last_rec'))


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
    request.session['last_rec'] = rec
    request.session['soil_data'] = data
    return _render(request, 'recommendation.html', recommendations=rec)


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


# ── Weather ──────────────────────────────────────────────────────────────────

@app.get('/weather', response_class=HTMLResponse)
def weather_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        return _redirect('home')
    return _render(request, 'weather.html')


@app.post('/weather', response_class=HTMLResponse)
def weather_post(
    request: Request,
    location: str = Form(...)
):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        return _redirect('home')

    weather_analysis = orchestrator.route_request('weather', {'location': location})
    return _render(request, 'weather.html', analysis=weather_analysis)


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


# ── Yield Comparison ─────────────────────────────────────────────────────────

@app.get('/yield-comparison', response_class=HTMLResponse)
def yield_comparison_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    return _render(request, 'yield_comparison.html')


@app.post('/yield-comparison', response_class=HTMLResponse)
def yield_comparison_post(
    request: Request,
    land_size: float = Form(...),
    main_crop: str = Form(...),
    companion_crop: str = Form(default='None')
):
    if not _logged_in(request):
        return _redirect('login')
    result = orchestrator.route_request('yield_comparison', {
        'land_size': land_size,
        'main_crop': main_crop,
        'companion_crop': companion_crop
    })
    return _render(request, 'yield_comparison.html', result=result,
                   land_size=land_size, main_crop=main_crop, companion_crop=companion_crop)


# ── Report ───────────────────────────────────────────────────────────────────

@app.get('/report', response_class=HTMLResponse)
def report_get(request: Request):
    if not _logged_in(request):
        return _redirect('login')
    if not request.session.get('farmer_id'):
        return _redirect('home')

    report_text = orchestrator.route_request('report', {'farmer_id': request.session['farmer_id']})
    return _render(request, 'report.html', report=report_text)


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='127.0.0.1', port=5000, reload=True)
