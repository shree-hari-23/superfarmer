from config import execute_fluxbase_sql
import os
import re
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import google.generativeai as genai
import PIL.Image
from openai import OpenAI
import builtins

# Safe print to prevent Windows terminal crashes when logging emojis/unicode
_original_print = builtins.print
def safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except UnicodeEncodeError:
        new_args = [str(a).encode('ascii', 'replace').decode('ascii') for a in args]
        _original_print(*new_args, **kwargs)
builtins.print = safe_print

import base64
import json

FLUXBASE_AI_BASE_URL = os.environ.get("FLUXBASE_AI_BASE_URL", "https://fluxbasedb.me/api/v1")

# ── Primary LLM: Flux Models (User AI Platform via Fluxbase Gateway) ───────────
def _call_flux(model: str, system_prompt: str, user_message: str, image_b64: str = None, history: list = None, timeout: float = 50.0) -> str:
    """Primary LLM dispatcher for user's Flux models."""
    api_key = os.environ.get("FLUXBASE_API_KEY")
    if not api_key:
        raise ValueError("FLUXBASE_API_KEY missing from environment")

    url = f"{FLUXBASE_AI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for m in history:
            role = "user" if m.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": m.get("content", "")})

    if image_b64:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message},
                {"type": "image_url", "image_url": {"url": image_b64}}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_message})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Flux model {model} returned HTTP {resp.status_code}: {resp.text}")

    data = resp.json()
    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        raise RuntimeError(f"Flux model {model} unexpected response: {data}")

    return choices[0]["message"]["content"]


# ── Secondary LLMs (Fallbacks) ────────────────────────────────────────────────
def _call_glm(system_prompt: str, user_message: str, history: list = None, model: str = "glm-4-flash") -> str:
    """Fallback LLM: Zhipu AI GLM (glm-4-flash / glm-4-plus)."""
    api_key = os.environ.get("GLM_API_KEY")
    if not api_key:
        raise ValueError("GLM_API_KEY missing from .env")
    client = OpenAI(api_key=api_key, base_url="https://open.bigmodel.cn/api/paas/v4", timeout=12.0)
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for m in history:
            role = "user" if m.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": m.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content


def _call_groq(system_prompt: str, user_message: str, history: list = None) -> str:
    """Fallback LLM: Groq qwen/qwen3.8-27b."""
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
        model="qwen/qwen3.8-27b",
        messages=messages,
    )
    return response.choices[0].message.content


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


# ── Unified call: User Flux Model Primary → Fallbacks ─────────────────────────
def _call_llm(system_prompt: str, user_message: str, history: list = None,
              label: str = "LLM", model: str = None) -> str:
    """Call user's Flux model first, fallback to GLM/Groq/Claude."""
    if not model:
        if "crop" in label.lower() or "plan" in label.lower():
            model = "flux-pro"
        elif "spatial" in label.lower() or "twin" in label.lower() or "report" in label.lower():
            model = "flux-ultra"
        elif "disease" in label.lower() or "vision" in label.lower():
            model = "flux-omni"
        elif "chat" in label.lower():
            model = "flux-flash"
        else:
            model = "flux-pro"

    # 1. Primary: User's Flux model
    if os.environ.get("FLUXBASE_API_KEY"):
        for m in [model, "flux-turbo", "flux-flash"]:
            try:
                print(f"   🤖 [{label}] Model : {m} (Fluxbase AI Gateway)")
                t0 = time.time()
                result = _call_flux(m, system_prompt, user_message, history=history)
                print(f"   ✅ [{label}] Response in {round(time.time()-t0, 2)}s")
                return result
            except Exception as e_flux:
                print(f"   ⚠️  [{label}] {m} failed: {e_flux}")

    # 2. Secondary fallback: GLM
    if os.environ.get("GLM_API_KEY"):
        try:
            print(f"   🤖 [{label}] Model : zhipuai/glm-4-flash")
            t0 = time.time()
            result = _call_glm(system_prompt, user_message, history)
            print(f"   ✅ [{label}] Response in {round(time.time()-t0, 2)}s")
            return result
        except Exception as e_glm:
            print(f"   ⚠️  [{label}] GLM failed: {e_glm}")

    # 3. Tertiary fallback: Groq
    if os.environ.get("GROK_API_KEY"):
        try:
            print(f"   🤖 [{label}] Model : groq/qwen/qwen3.8-27b")
            t0 = time.time()
            result = _call_groq(system_prompt, user_message, history)
            print(f"   ✅ [{label}] Response in {round(time.time()-t0, 2)}s")
            return result
        except Exception as e_groq:
            print(f"   ⚠️  [{label}] Groq failed: {e_groq}")

    # 4. Final fallback: Claude
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            t0 = time.time()
            result = _call_claude(system_prompt, user_message, history)
            print(f"   ✅ [{label}] Claude response in {round(time.time()-t0, 2)}s")
            return result
        except Exception as e_claude:
            print(f"   ⚠️  [{label}] Claude failed: {e_claude}")

    return "All AI models failed."


def _call_gemini(system_prompt: str, user_message: str, history: list = None) -> str:
    return _call_llm(system_prompt, user_message, history, label="LLM", model="flux-pro")

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
    def _find_notification_image(provided_path=None):
        """Locate the notification logo in the images folder or fallback paths."""
        if provided_path and os.path.exists(provided_path):
            return provided_path

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(base_dir, 'images', 'auth_logo.png'),
            os.path.join(os.getcwd(), 'images', 'auth_logo.png'),
            os.path.join(base_dir, 'images', 'ChatGPT Image Sep 9, 2026, 09_53_19 AM.png'),
            os.path.join(base_dir, 'static', 'images', 'auth_logo.png'),
            os.path.join(os.getcwd(), 'static', 'images', 'auth_logo.png'),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path

        images_dir = os.path.join(base_dir, 'images')
        if os.path.isdir(images_dir):
            for fname in os.listdir(images_dir):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    return os.path.join(images_dir, fname)

        return None

    @staticmethod
    def send_email(to_email, subject, body, image_path=None):
        sender_email = os.environ.get('EMAIL_ADDRESS')
        sender_password = os.environ.get('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("⚠️ [EmailAgent] Email credentials not found in environment variables (EMAIL_ADDRESS / EMAIL_PASSWORD).")
            return False
            
        try:
            resolved_image_path = EmailAgent._find_notification_image(image_path)

            # If an image is available and not already referenced in body, auto-prepend logo
            if resolved_image_path and 'cid:superfarmer_logo' not in body:
                body = (
                    '<div style="text-align: center; margin-bottom: 20px;">'
                    '<img src="cid:superfarmer_logo" alt="SuperFarmer Logo" width="130" style="max-width: 130px; height: auto; border-radius: 50%;" />'
                    '</div>'
                ) + body

            # Create related multipart message (RFC 2387) for HTML with inline images
            msg = MIMEMultipart('related')
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Alternative part for plain text & HTML
            msg_alt = MIMEMultipart('alternative')
            msg.attach(msg_alt)

            # Plain text fallback
            plain_text = re.sub(r'<[^>]+>', ' ', body)
            plain_text = re.sub(r'\s+', ' ', plain_text).strip()
            msg_alt.attach(MIMEText(plain_text, 'plain', 'utf-8'))
            msg_alt.attach(MIMEText(body, 'html', 'utf-8'))

            # Attach inline image if found
            if resolved_image_path and os.path.exists(resolved_image_path):
                with open(resolved_image_path, 'rb') as img_f:
                    img_data = img_f.read()
                
                ext = os.path.splitext(resolved_image_path)[1].lower().replace('.', '')
                subtype = 'png' if ext == 'png' else ('jpeg' if ext in ('jpg', 'jpeg') else ext)
                
                mime_img = MIMEImage(img_data, _subtype=subtype)
                mime_img.add_header('Content-ID', '<superfarmer_logo>')
                mime_img.add_header('Content-Disposition', 'inline', filename=os.path.basename(resolved_image_path))
                msg.attach(mime_img)
                print(f"   [EmailAgent] Attached inline notification image: {resolved_image_path}")

            # Using Gmail's SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, to_email, text)
            server.quit()
            print(f"📧 [EmailAgent] Successfully sent notification email with image to {to_email}")
            return True
        except Exception as e:
            print(f"❌ [EmailAgent] Failed to send email to {to_email}: {e}")
            return False

from werkzeug.security import generate_password_hash, check_password_hash
try:
    import bcrypt
except ImportError:
    bcrypt = None

def _verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash:
        return False
    # Check bcrypt hashes ($2a$, $2b$, $2y$)
    if stored_hash.startswith(('$2a$', '$2b$', '$2y$', '$2x$')) and bcrypt:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception:
            pass
    # Check werkzeug hashes (scrypt, pbkdf2)
    try:
        if check_password_hash(stored_hash, password):
            return True
    except (ValueError, Exception):
        pass
    # Fallback to plain text comparison if legacy unhashed
    return stored_hash == password

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
            if _verify_password(user_record.get('password_hash', ''), password):
                return {"success": True, "user_id": user_record['user_id']}
        return {"success": False, "error": "Invalid email or password."}


    @staticmethod
    def get_farmer_profile_by_user(user_id):
        query = f"SELECT farmer_id FROM farmer_profile WHERE user_id = {int(user_id)} LIMIT 1"
        res = execute_fluxbase_sql(query)
        if res.get('rows'):
            return res['rows'][0]['farmer_id']
        return None

    @staticmethod
    def get_user_email(user_id):
        try:
            sel_res = execute_fluxbase_sql(f"SELECT email FROM users WHERE user_id = {int(user_id)} LIMIT 1")
            if sel_res.get('rows'):
                return sel_res['rows'][0]['email']
        except Exception:
            pass
        return None

    @staticmethod
    def get_user_email_by_farmer_id(farmer_id):
        try:
            sel_res = execute_fluxbase_sql(
                f"SELECT u.email FROM users u "
                f"JOIN farmer_profile f ON u.user_id = f.user_id "
                f"WHERE f.farmer_id = {int(farmer_id)} LIMIT 1"
            )
            if sel_res.get('rows'):
                return sel_res['rows'][0]['email']
        except Exception:
            pass
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
    # Emoji map for common crops
    _CROP_EMOJI = {
        'rice': '🌾', 'wheat': '🌾', 'corn': '🌽', 'maize': '🌽',
        'sugarcane': '🎋', 'cotton': '🪴', 'soybean': '🫘', 'tomato': '🍅',
        'onion': '🧅', 'garlic': '🧄', 'potato': '🥔', 'sunflower': '🌻',
        'mustard': '🌿', 'chickpea': '🫘', 'groundnut': '🥜', 'marigold': '🌼',
        'sorghum': '🌾', 'millet': '🌾', 'pearl millet': '🌾',
        'finger millet': '🌾', 'lentil': '🌿', 'pigeon peas': '🌿',
        'moth beans': '🌱', 'sesame': '🌱', 'watermelon': '🍉',
    }

    @staticmethod
    def recommend(farmer_id, soil_type, n, p, k, temp, rain, water_const):
        print("\n" + "━" * 60)
        print("🌾 [CropRecommendation] Analysing soil parameters")
        print(f"   Soil     : {soil_type} | Water: {water_const}")
        print(f"   NPK      : N={n} P={p} K={k} | Temp={temp}°C | Rain={rain}mm")
        print(f"   🤖 Engine  : flux-pro (Structured-Output Tier via Fluxbase Gateway)")
        print("━" * 60)

        crop_details = CropRecommendationAgent._flux_recommend_and_explain(
            soil_type, n, p, k, temp, rain, water_const
        )

        top3    = [d["crop"] for d in crop_details]
        rec_str = ", ".join(top3)

        print(f"   ✅ Recommended : {rec_str}")
        print("━" * 60 + "\n")

        try:
            # Verify farmer_id exists in farmer_profile; if not, create minimal profile
            fid_int = int(farmer_id)
            chk = execute_fluxbase_sql(f"SELECT farmer_id FROM farmer_profile WHERE farmer_id = {fid_int} LIMIT 1")
            if not chk.get('rows'):
                execute_fluxbase_sql(
                    f"INSERT INTO farmer_profile (farmer_id, user_id, name, land_size, location, water_availability) "
                    f"VALUES ({fid_int}, {fid_int}, 'Farmer {fid_int}', 1.0, 'India', 'Medium')"
                )
            query = f"INSERT INTO crop_recommendations (farmer_id, recommended_crops) VALUES ({fid_int}, '{safe_str(rec_str)}');"
            execute_fluxbase_sql(query)
        except Exception as _dbe:
            print(f"   ⚠️  [CropRec] DB recommendation insert note: {_dbe}")

        try:
            fid_int = int(farmer_id)
            execute_fluxbase_sql(
                f"INSERT INTO soil_records (farmer_id, soil_type, nitrogen, phosphorus, potassium, temperature) "
                f"VALUES ({fid_int}, '{safe_str(soil_type)}', {float(n)}, {float(p)}, {float(k)}, {float(temp)});"
            )
        except Exception as _se:
            print(f"   ⚠️  [CropRec] Soil record insert note: {_se}")

        return {
            "crops_str": rec_str,
            "crops": top3,
            "crop_details": crop_details,
        }

    # ── flux-pro: recommend + explain in one shot ─────────────────────────
    @staticmethod
    def _flux_recommend_and_explain(soil_type, n, p, k, temp, rain, water_const):
        """
        Ask flux-pro (Structured-Output Tier) to choose the top-3 crops AND return full
        agronomic explanations for each, based purely on soil/climate data.
        Returns a list of 3 dicts.
        """
        prompt = f"""You are an expert Indian agronomist AI.
Analyze soil & climate parameters:
- Soil Type     : {soil_type}
- Nitrogen (N)  : {n} mg/kg
- Phosphorus (P): {p} mg/kg
- Potassium (K) : {k} mg/kg
- Temperature   : {temp}°C
- Avg Rainfall  : {rain} mm
- Water Supply  : {water_const}

Recommend the TOP 3 most suitable crops from:
Cotton, Soybean, Groundnut, Wheat, Rice, Sugarcane, Sunflower, Mustard, Chickpea, Maize, Onion, Garlic, Potato.

Return ONLY a JSON array of 3 objects in this format:
[
  {{
    "crop": "Cotton",
    "rank": 1,
    "suitability_score": 95,
    "why_recommended": "Thrives in deep {soil_type.lower()} soil with high moisture retention and {temp}°C heat.",
    "key_features": ["Deep taproot system", "High market demand", "Drought tolerant"],
    "nutritional_importance": "Primary commercial cash crop contributing to farmer income.",
    "growing_tips": ["Ensure proper furrow drainage", "Maintain optimal row spacing", "Apply balanced NPK"],
    "ideal_season": "Kharif (June-Oct)",
    "expected_yield": "2-3 tonnes/acre",
    "water_need": "{water_const}"
  }}
]
Rules: Return ONLY valid JSON array of 3 objects. No extra text, no markdown fences.
""".strip()

        raw = None
        for m in ["flux-pro", "flux-turbo", "flux-flash"]:
            try:
                print(f"   🤖 [CropAI] Calling {m} (Fluxbase Gateway)...")
                t0 = time.time()
                raw = _call_flux(
                    model=m,
                    system_prompt="You are an expert Indian agricultural scientist AI. Output valid JSON array only.",
                    user_message=prompt,
                    timeout=45.0
                )
                if raw:
                    print(f"   ✅ [{m}] Crop recommendation generated in {round(time.time()-t0, 2)}s")
                    break
            except Exception as e_flux:
                print(f"   ⚠️  [{m}] error: {e_flux}, trying next model...")

        if not raw:
            try:
                raw = _call_llm(
                    system_prompt="You are an expert Indian agricultural scientist AI. Output valid JSON array only.",
                    user_message=prompt,
                    label="CropRecFallback"
                )
            except Exception:
                raw = None

        if raw:
            try:
                text = raw.strip()
                if text.startswith("```json"):
                    text = text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
                elif text.startswith("```"):
                    text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()

                m_json = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
                if m_json:
                    details = json.loads(m_json.group(0))
                else:
                    details = json.loads(text)

                if isinstance(details, list) and len(details) >= 1:
                    details = details[:3]
                    for idx, d in enumerate(details):
                        cname = d.get("crop", "").lower()
                        d["emoji"] = CropRecommendationAgent._CROP_EMOJI.get(cname, "🌱")
                        d.setdefault("rank", idx + 1)
                        d.setdefault("suitability_score", 92 - idx * 7)
                        d.setdefault("water_need", water_const)
                        d.setdefault("ideal_season", "Kharif (June–Oct)")
                        d.setdefault("expected_yield", "2-3 tonnes/acre")
                        d.setdefault("key_features", ["High yield potential", "Matches soil fertility"])
                        d.setdefault("growing_tips", ["Maintain proper soil drainage", "Apply balanced fertilizers"])
                        d.setdefault("nutritional_importance", "High economic value in Indian agriculture.")
                    return details
            except Exception as e_parse:
                print(f"   ⚠️  JSON parse error ({e_parse}) from output: {raw[:150]}")

        print("   ⚠️  All AI models failed, using deterministic agronomy fallback.")
        return CropRecommendationAgent._rule_based_fallback(soil_type, n, p, k, temp, rain, water_const)

    @staticmethod
    def _ollama_recommend_and_explain(soil_type, n, p, k, temp, rain, water_const):
        """Backward-compatibility alias pointing to _flux_recommend_and_explain."""
        return CropRecommendationAgent._flux_recommend_and_explain(soil_type, n, p, k, temp, rain, water_const)

    # ── Rule-based fallback (Ollama offline) ──────────────────────────────
    @staticmethod
    def _rule_based_fallback(soil_type, n, p, k, temp, rain, water_const):
        soil  = soil_type.lower()
        water = water_const.lower()
        crops = []
        if water == 'low':
            crops = ['Pearl Millet', 'Chickpea', 'Moth Beans'] if soil in ('red', 'laterite', 'sandy') else ['Sorghum', 'Chickpea', 'Lentil']
        elif soil == 'black':
            if n > 40 and temp > 22: crops.append('Cotton')
            if rain > 600 or water == 'high': crops.append('Wheat')
            crops.append('Soybean')
        elif soil == 'alluvial':
            if water == 'high': crops.append('Rice')
            if n > 30: crops.append('Sugarcane')
            crops.append('Maize')
        elif soil in ('red', 'laterite'):
            crops += ['Groundnut', 'Finger Millet', 'Sorghum']
        elif soil == 'sandy':
            crops = ['Pearl Millet', 'Watermelon', 'Sesame']
        if not crops:
            crops = ['Maize', 'Sorghum', 'Pigeon Peas']
        crops = crops[:3]

        details = []
        for idx, crop in enumerate(crops):
            cname = crop.lower()
            details.append({
                "crop": crop,
                "rank": idx + 1,
                "suitability_score": 82 - idx * 8,
                "emoji": CropRecommendationAgent._CROP_EMOJI.get(cname, "🌱"),
                "why_recommended": (
                    f"{crop} is well-suited to {soil_type} soil with N={n}, P={p}, K={k} mg/kg. "
                    f"It performs reliably at {temp}°C with {rain} mm average rainfall and {water_const.lower()} water supply."
                ),
                "key_features": [
                    f"Thrives in {soil_type} soil conditions",
                    f"Adapted to {temp}°C temperature range",
                    f"Requires {water_const.lower()} water — matches farm supply",
                ],
                "nutritional_importance": (
                    f"{crop} is a staple crop in Indian agriculture with strong market demand "
                    f"and contributes to both food security and farmer income."
                ),
                "growing_tips": [
                    "Prepare land thoroughly before sowing",
                    "Follow recommended plant spacing for best yield",
                    "Monitor regularly for pests and apply organic controls first",
                ],
                "ideal_season": "Kharif (June–Oct) or Rabi (Nov–Apr) depending on region",
                "expected_yield": "Varies by region and farming practice",
                "water_need": water_const,
            })
        return details

class CropPlannerAgent:
    # Known crop names for clean extraction
    _KNOWN_CROPS = [
        'Rice', 'Wheat', 'Corn', 'Maize', 'Sugarcane', 'Cotton', 'Soybean',
        'Tomato', 'Tomatoes', 'Onion', 'Garlic', 'Potato', 'Sunflower',
        'Mustard', 'Chickpea', 'Groundnut', 'Marigold', 'Sorghum', 'Millet',
        'Pearl Millet', 'Finger Millet', 'Lentil', 'Pigeon Peas', 'Jute',
        'Banana', 'Papaya', 'Sesame', 'Barley', 'Oat',
    ]

    @staticmethod
    def _sanitize_crop_name(raw: str) -> str:
        """
        Extract a clean crop name from whatever was submitted.
        If the input is longer than 40 chars (i.e. full AI text), scan it
        for a known crop name and return that. Otherwise return the first
        word-pair (handles 'Pearl Millet', 'Pigeon Peas', etc.).
        """
        raw = (raw or '').strip()
        if len(raw) <= 40:
            # Looks like a normal short crop name — just title-case the first token
            first = raw.split('\n')[0].split('.')[0].strip()
            return first[:64] if first else 'Unknown'

        # Long string: scan for a known crop name
        raw_lower = raw.lower()
        for crop in CropPlannerAgent._KNOWN_CROPS:
            if crop.lower() in raw_lower:
                return crop
        # Last resort: return first word, max 40 chars
        return raw.split()[0][:40]

    @staticmethod
    def generate_plan(farmer_id, crop_name):
        # ── Sanitize: store only the clean crop name in DB ───────────
        clean_crop_name = CropPlannerAgent._sanitize_crop_name(crop_name)

        print("\n" + "━" * 60)
        print("📋 [CropPlanner] Generating crop management plan")
        print(f"   Crop (raw)  : {crop_name[:60]}{'...' if len(str(crop_name)) > 60 else ''}")
        print(f"   Crop (clean): {clean_crop_name}")
        print(f"   Farmer ID   : {farmer_id}")
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
            print("   🤖 [CropPlanner] Model : flux-pro (Structured-Output Tier via Fluxbase Gateway)")
            t0 = time.time()
            text = _call_flux(
                model="flux-pro",
                system_prompt="You are an expert Indian agricultural scientist AI. Output valid JSON only.",
                user_message=prompt,
                timeout=45.0
            )
            print(f"   ✅ [CropPlanner] Plan ready in {round(time.time()-t0, 2)}s")
            if text.startswith("```json"):
                text = text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
            elif text.startswith("```"):
                text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()
            m_json = re.search(r'\{.*\}', text, re.DOTALL)
            if m_json:
                plan = json.loads(m_json.group(0))
            else:
                plan = json.loads(text)
        except Exception as e_flux:
            print(f"   ⚠️  [CropPlanner] flux-pro error: {e_flux}, trying fallback...")
            try:
                text = _call_llm(
                    system_prompt="You are an expert Indian agricultural scientist AI. Output valid JSON only.",
                    user_message=prompt,
                    label="CropPlannerFallback",
                    model="flux-turbo"
                )
                m_json = re.search(r'\{.*\}', text, re.DOTALL)
                if m_json:
                    plan = json.loads(m_json.group(0))
            except Exception as e_fb:
                print(f"   ⚠️  [CropPlanner] Fallback error: {e_fb}")

        if not plan or not all(k in plan for k in ['sowing_schedule', 'irrigation_plan', 'fertilizer_schedule', 'pest_alerts', 'harvest_timeline']):
            plan = CropPlannerAgent._fallback_plan(crop_name)

        fid_int = int(farmer_id)
        try:
            chk = execute_fluxbase_sql(f"SELECT farmer_id FROM farmer_profile WHERE farmer_id = {fid_int} LIMIT 1")
            if not chk.get('rows'):
                execute_fluxbase_sql(
                    f"INSERT INTO farmer_profile (farmer_id, user_id, name, land_size, location, water_availability) "
                    f"VALUES ({fid_int}, {fid_int}, 'Farmer {fid_int}', 1.0, 'India', 'Medium')"
                )
            query = f"""INSERT INTO crop_plans 
                       (farmer_id, crop_name, sowing_schedule, irrigation_plan, 
                        fertilizer_schedule, pest_alerts, harvest_timeline) 
                       VALUES ({fid_int}, '{safe_str(clean_crop_name)}', '{safe_str(plan['sowing_schedule'])}', '{safe_str(plan['irrigation_plan'])}', 
                       '{safe_str(plan['fertilizer_schedule'])}', '{safe_str(plan['pest_alerts'])}', '{safe_str(plan['harvest_timeline'])}');"""
            execute_fluxbase_sql(query)
            sel_query = f"SELECT plan_id FROM crop_plans WHERE farmer_id = {fid_int} ORDER BY plan_id DESC LIMIT 1"
            sel_res = execute_fluxbase_sql(sel_query)
            plan['plan_id'] = sel_res['rows'][0]['plan_id'] if sel_res.get('rows') else None
        except Exception as _pe:
            print(f"   ⚠️  [CropPlanner] DB insert note: {_pe}")
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

        # Prepare base64 image if attached
        image_b64 = None
        if has_image:
            try:
                if hasattr(leaf_image, 'file'):
                    leaf_image.file.seek(0)
                    img_bytes = leaf_image.file.read()
                elif hasattr(leaf_image, 'read'):
                    img_bytes = leaf_image.read()
                else:
                    img_bytes = None

                if img_bytes:
                    b64_str = base64.b64encode(img_bytes).decode('utf-8')
                    content_type = getattr(leaf_image, 'content_type', 'image/jpeg') or 'image/jpeg'
                    image_b64 = f"data:{content_type};base64,{b64_str}"
            except Exception as e_b64:
                print(f"   ⚠️  Failed to encode image to base64: {e_b64}")

        # ── Primary: User's Flux Models (flux-omni -> flux-max) ────────────────
        for m in ["flux-omni", "flux-max"]:
            try:
                print(f"   🤖 [DiseaseAI] Model : {m} (Vision Pathology Tier via Fluxbase Gateway)")
                t0 = time.time()
                raw_result = _call_flux(
                    model=m,
                    system_prompt=DiseaseDiagnosisAgent._DIAGNOSIS_SYSTEM,
                    user_message=prompt,
                    image_b64=image_b64,
                    timeout=30.0
                )
                print(f"   ✅ [{m}] Diagnosis ready in {round(time.time()-t0, 2)}s")
                break
            except Exception as e_flux:
                print(f"   ⚠️  [{m}] error: {e_flux}, trying next model...")

        # ── Fallback A: Gemini Vision (if image attached and flux failed) ─────
        if raw_result is None and has_image:
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                try:
                    print("   🤖 Model    : gemini-2.5-flash  [Vision Fallback]")
                    t0 = time.time()
                    genai.configure(api_key=api_key)
                    gmodel = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
                    if hasattr(leaf_image, 'file'):
                        leaf_image.file.seek(0)
                    img = PIL.Image.open(leaf_image)
                    response = gmodel.generate_content([DiseaseDiagnosisAgent._DIAGNOSIS_SYSTEM + "\n\n" + prompt, img])
                    raw_result = response.text
                    print(f"   ✅ Gemini Vision response in {round(time.time()-t0, 2)}s")
                except Exception as e:
                    print(f"   ⚠️  Gemini Vision failed: {e}")

        # ── Fallback B: Groq / Claude text fallback ───────────────────────────
        if raw_result is None:
            try:
                print("   🤖 [DiseaseAI] Fallback Model : groq/qwen/qwen3.8-27b")
                t0 = time.time()
                raw_result = _call_groq(DiseaseDiagnosisAgent._DIAGNOSIS_SYSTEM, prompt)
                print(f"   ✅ [DiseaseAI] Groq response in {round(time.time()-t0, 2)}s")
            except Exception as e_groq:
                print(f"   ⚠️  Groq failed: {e_groq}, falling back to Claude...")
                try:
                    t0 = time.time()
                    raw_result = _call_claude(
                        system_prompt=DiseaseDiagnosisAgent._DIAGNOSIS_SYSTEM,
                        user_message=prompt,
                    )
                    print(f"   ✅ Claude response in {round(time.time()-t0, 2)}s")
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
    def _calculate_yield_metrics(land_size: float, main_crop: str, companion_crop: str) -> dict:
        base_yields = {
            'rice': 2.5, 'wheat': 1.9, 'maize': 2.2, 'cotton': 0.5,
            'sugarcane': 35.0, 'groundnut': 0.9, 'soybean': 1.0, 'chickpea': 0.7,
            'pigeon peas': 0.6, 'pearl millet': 1.2, 'sorghum': 1.1, 'lentil': 0.6,
            'tomatoes': 8.0, 'tomato': 8.0, 'corn': 2.2, 'banana': 15.0, 'coconut': 5.0,
            'sunflower': 0.8, 'mustard': 0.8, 'jute': 2.0, 'finger millet': 1.3,
            'vegetables': 5.0, 'papaya': 12.0, 'sesame': 0.5,
        }
        companion_bonus_map = {
            'soybean': 0.08, 'chickpea': 0.07, 'pigeon peas': 0.07,
            'lentil': 0.06, 'clover': 0.06, 'marigold': 0.05, 'marigolds': 0.05,
            'coriander': 0.04, 'beans': 0.06, 'cover crop': 0.05,
        }
        mc = (main_crop or 'Corn').lower().strip()
        cc = (companion_crop or '').lower().strip() if companion_crop and companion_crop.lower() != 'none' else ''

        base = base_yields.get(mc)
        if not base:
            for k, v in base_yields.items():
                if k in mc or mc in k:
                    base = v
                    break
        if not base:
            base = 1.8

        companion_bonus = 0.0
        for k, bonus in companion_bonus_map.items():
            if k in cc:
                companion_bonus = bonus
                break
        intercrop_boost = min(0.15 + companion_bonus, 0.30)
        normal_penalty = 0.10

        opt_per_acre = round(base * (1 + intercrop_boost), 2)
        norm_per_acre = round(base * (1 - normal_penalty), 2)
        improvement_pct = round(((opt_per_acre - norm_per_acre) / max(0.1, norm_per_acre)) * 100, 1)

        opt_total = round(opt_per_acre * land_size, 2)
        norm_total = round(norm_per_acre * land_size, 2)
        extra_tons = round(opt_total - norm_total, 2)

        return {
            "base_yield": base,
            "optimized_total": opt_total,
            "normal_total": norm_total,
            "improvement_pct": improvement_pct,
            "extra_tons": extra_tons
        }

    @staticmethod
    def _generate_grounded_insights(farmer_name, land_size, soil_info, plan_info, spatial_info, disease_info=None):
        """Generate strictly grounded agronomic recommendations based only on real inputs (NO WEATHER)."""
        insights = []
        p_crop = plan_info.get('crop_name')
        s_main = spatial_info.get('main_crop')
        s_comp = spatial_info.get('companion_crop')

        # 1. Soil nutrient insight
        n_val = soil_info.get('nitrogen')
        p_val = soil_info.get('phosphorus')
        k_val = soil_info.get('potassium')
        if n_val is not None and p_val is not None and k_val is not None:
            if float(n_val) < 140:
                insights.append(
                    f"Soil Nitrogen ({n_val} kg/ha) is low for optimal vegetative growth. "
                    f"Prioritize split nitrogen application or intercrop with nitrogen-fixing pulses to restore balance."
                )
            else:
                insights.append(
                    f"Soil NPK reserve (N={n_val}, P={p_val}, K={k_val} kg/ha) supports strong crop establishment for {p_crop or 'cultivation'}."
                )
        elif soil_info.get('soil_type'):
            insights.append(
                f"For {soil_info.get('soil_type')} soil, apply periodic organic compost to preserve root-zone moisture and organic carbon."
            )

        # 2. Crop Plan & Sowing / Irrigation
        if p_crop:
            sow = plan_info.get('sowing_schedule')
            if sow and 'not available' not in sow.lower():
                insights.append(f"Crop Plan ({p_crop}): Follow optimal sowing window ({sow[:70]}) to facilitate uniform germination.")
            irrig = plan_info.get('irrigation_plan')
            if irrig and 'not available' not in irrig.lower():
                insights.append(f"Water Management: Implement {irrig[:80]} to maintain steady root-zone aeration.")

        # 3. Spatial Twin Intercropping Synergy
        if s_main and s_comp and s_comp.lower() != 'none':
            insights.append(
                f"Spatial Layout Synergy: Intercropping {s_main} with {s_comp} maximizes solar canopy interception "
                f"and provides ecological pest barrier protection via hexagonal grid spacing."
            )

        # 4. Disease / Pathology
        if disease_info and disease_info.get('diagnosis'):
            diag = disease_info.get('diagnosis')
            treat = disease_info.get('treatment', '')
            first_treat = treat.split('\n')[0] if treat else 'Targeted bio-control'
            insights.append(f"Disease Management Alert: Address detected {diag} promptly using recommended treatment: {first_treat[:80]}.")

        if len(insights) < 3:
            insights.append("Maintain routine weed vigilance and inspect border rows regularly to preserve crop health and maximize yield.")

        return insights[:4]

    @staticmethod
    def generate_report(farmer_id=None, **kwargs):
        import os
        import json
        import re
        import time
        from config import execute_fluxbase_sql

        if farmer_id is None:
            farmer_id = kwargs.get('farmer_id')

        try:
            fid = int(farmer_id)
        except (TypeError, ValueError):
            fid = 0

        user_id = kwargs.get('user_id')
        print("\n" + "=" * 60)
        print("📄 [ReportAgent] Generating authentic Field Advisory Report (Sections 1-7, No Weather)")
        print(f"   Farmer ID : {fid}")
        print("=" * 60)

        # ── 1. Fetch Profile (IntakeAgent / farmer_profile) ───────────
        profile = {}
        try:
            profile_res = execute_fluxbase_sql(f"SELECT * FROM farmer_profile WHERE farmer_id={fid} LIMIT 1")
            profile = profile_res['rows'][0] if profile_res.get('rows') else {}
        except Exception as e:
            print(f"   [Report] Profile fetch error: {e}")

        farmer_name = profile.get('name') or 'SuperFarmer Farmer'
        location = profile.get('location') or 'Not specified'
        land_size_raw = profile.get('land_size')
        water_avail = profile.get('water_availability') or 'Standard'
        farming_goals = profile.get('farming_goals') or 'Sustainable yield & profitability'

        try:
            land_size_val = float(land_size_raw) if land_size_raw is not None else 1.0
            if land_size_val <= 0:
                land_size_val = 1.0
        except (TypeError, ValueError):
            land_size_val = 1.0

        # Retrieve user email for prefilling
        user_email = ""
        try:
            if not user_id and profile.get('user_id'):
                user_id = profile.get('user_id')
            if user_id:
                user_email = UserAuthAgent.get_user_email(user_id) or ""
            if not user_email and fid:
                user_email = UserAuthAgent.get_user_email_by_farmer_id(fid) or ""
        except Exception:
            pass

        # ── 2. Fetch Soil Records (soil_records) ─────────────────────
        soil_row = {}
        try:
            soil_res = execute_fluxbase_sql(f"SELECT * FROM soil_records WHERE farmer_id={fid} ORDER BY recorded_at DESC LIMIT 1")
            soil_row = soil_res['rows'][0] if soil_res.get('rows') else {}
        except Exception as e:
            print(f"   [Report] Soil records fetch error: {e}")

        # Check kwargs fallback if soil_records was empty
        session_soil = kwargs.get('soil_data') or {}
        soil_type = soil_row.get('soil_type') or session_soil.get('soil_type') or 'Loamy'
        n_val = soil_row.get('nitrogen') if soil_row.get('nitrogen') is not None else session_soil.get('n')
        p_val = soil_row.get('phosphorus') if soil_row.get('phosphorus') is not None else session_soil.get('p')
        k_val = soil_row.get('potassium') if soil_row.get('potassium') is not None else session_soil.get('k')
        ph_val = soil_row.get('ph') # None if not recorded in database
        moisture_val = soil_row.get('soil_moisture')
        soil_temp = soil_row.get('temperature') if soil_row.get('temperature') is not None else session_soil.get('temp')
        soil_recorded_at = soil_row.get('recorded_at')

        soil_info = {
            'soil_type': soil_type,
            'nitrogen': n_val,
            'phosphorus': p_val,
            'potassium': k_val,
            'ph': ph_val,
            'soil_moisture': moisture_val,
            'temperature': soil_temp,
            'recorded_at': soil_recorded_at,
            'has_npk': (n_val is not None and p_val is not None and k_val is not None)
        }

        # ── 3. Fetch Crop Recommendations (crop_recommendations) ─────
        rec_row = {}
        try:
            rec_res = execute_fluxbase_sql(f"SELECT * FROM crop_recommendations WHERE farmer_id={fid} ORDER BY created_at DESC LIMIT 1")
            rec_row = rec_res['rows'][0] if rec_res.get('rows') else {}
        except Exception as e:
            print(f"   [Report] Recommendations fetch error: {e}")

        rec_crops_str = rec_row.get('recommended_crops') or 'Corn, Soybean, Groundnut'
        rec_crops_list = [c.strip() for c in rec_crops_str.split(',') if c.strip()]

        rec_factors = []
        if soil_type:
            rec_factors.append(f"Soil Texture: {soil_type}")
        if soil_info['has_npk']:
            rec_factors.append(f"Nutrient Level: N={n_val}, P={p_val}, K={k_val} kg/ha")
        if water_avail:
            rec_factors.append(f"Water Availability: {water_avail}")

        rec_info = {
            'recommended_crops': rec_crops_list,
            'crops_str': rec_crops_str,
            'recommendation_reason': f"Recommended based on {soil_type} soil properties and {water_avail.lower()} irrigation capacity using rule-based agronomic suitability matching.",
            'factors_used': rec_factors
        }

        # ── 4. Fetch Crop Plan (crop_plans) ──────────────────────────
        plan_row = {}
        try:
            plan_res = execute_fluxbase_sql(f"SELECT * FROM crop_plans WHERE farmer_id={fid} ORDER BY created_at DESC LIMIT 1")
            plan_row = plan_res['rows'][0] if plan_res.get('rows') else {}
        except Exception as e:
            print(f"   [Report] Plan fetch error: {e}")

        planned_crop = plan_row.get('crop_name') or (rec_crops_list[0] if rec_crops_list else 'Corn')
        sowing_sched = plan_row.get('sowing_schedule') or 'Seasonal schedule aligned with monsoon onset'
        irrig_plan = plan_row.get('irrigation_plan') or 'Scheduled drip irrigation per growth stage'
        fert_sched = plan_row.get('fertilizer_schedule') or 'Split basal dose and vegetative top-dressing'
        pest_alerts = plan_row.get('pest_alerts') or 'Periodic monitoring for stem borers and foliar pathogens'
        harvest_time = plan_row.get('harvest_timeline') or 'Standard seasonal maturity timeline'
        plan_status = plan_row.get('status') or 'Active'

        # Optional disease diagnosis from session
        last_diag = kwargs.get('last_diagnosis')

        plan_info = {
            'crop_name': planned_crop,
            'sowing_schedule': sowing_sched,
            'irrigation_plan': irrig_plan,
            'fertilizer_schedule': fert_sched,
            'pest_alerts': pest_alerts,
            'harvest_timeline': harvest_time,
            'status': plan_status,
            'disease_diagnosis': last_diag if (last_diag and isinstance(last_diag, dict) and last_diag.get('diagnosis')) else None
        }

        # ── 5. Fetch Spatial Twin Log (spatial_twin_log) ─────────────
        spatial_row = {}
        try:
            sp_res = execute_fluxbase_sql(f"SELECT * FROM spatial_twin_log WHERE farmer_id={fid} ORDER BY created_at DESC LIMIT 1")
            spatial_row = sp_res['rows'][0] if sp_res.get('rows') else {}
        except Exception:
            pass

        has_spatial = bool(spatial_row)
        spatial_main = spatial_row.get('main_crop') or planned_crop
        spatial_comp = spatial_row.get('companion_crop') or ('Soybean' if spatial_main == 'Corn' else 'Marigold')
        spatial_mode = spatial_row.get('layout_mode') or 'Hexagonal Staggered Grid'
        if spatial_mode.lower() == 'grid':
            spatial_mode = 'Hexagonal Staggered Grid'
        spatial_score = spatial_row.get('layout_score', 88)
        spatial_soil = spatial_row.get('soil_impact') or 'improves soil nitrogen'
        spatial_yield_val = spatial_row.get('total_yield_t')

        # Retrieve spacing metadata from SpatialPlannerAgent.CROP_DB
        main_meta = SpatialPlannerAgent.CROP_DB.get(spatial_main, SpatialPlannerAgent.CROP_DB.get('Corn', {}))
        comp_meta = SpatialPlannerAgent.CROP_DB.get(spatial_comp, SpatialPlannerAgent.CROP_DB.get('Soybean', {}))

        main_spacing = main_meta.get('spacing', 60)
        comp_spacing = comp_meta.get('spacing', 30)
        main_height = main_meta.get('height_m', 2.0)
        comp_height = comp_meta.get('height_m', 0.8)

        # Solar orientation logic
        sunlight_note = (
            f"Taller crop {spatial_main} ({main_height}m) positioned relative to {spatial_comp} ({comp_height}m) "
            f"to optimize canopy solar interception and prevent shading."
        )

        # Check for crop discrepancy between plan and spatial twin
        crops_match = (planned_crop.lower().strip() == spatial_main.lower().strip())
        crop_sync_note = None
        if not crops_match:
            crop_sync_note = (
                f"Note: Active Crop Plan is configured for {planned_crop}, while the Spatial Twin model "
                f"was generated for {spatial_main} + {spatial_comp}. Each module reflects your saved work. "
                f"To align your 3D field layout with your crop plan, run the Spatial Planner for {planned_crop}."
            )

        spatial_info = {
            'has_spatial': has_spatial,
            'main_crop': spatial_main,
            'companion_crop': spatial_comp,
            'layout_mode': spatial_mode,
            'layout_score': spatial_score,
            'soil_impact': spatial_soil,
            'main_spacing_cm': main_spacing,
            'comp_spacing_cm': comp_spacing,
            'sunlight_note': sunlight_note,
            'land_efficiency_pct': min(95, 75 + int(spatial_score * 0.2)),
            'nitrogen_balance': 'Legume biological N₂ fixation balances nitrogen uptake' if 'improves' in spatial_soil.lower() or comp_meta.get('nitrogen') == 'Fixer' else 'Balanced nutrient depletion',
            'algorithm_note': 'Spatial Twin layout is generated using the implemented rule-based spatial planning and hexagonal crop placement algorithm.',
            'crops_match': crops_match,
            'crop_sync_note': crop_sync_note
        }

        # ── 6. Fetch Yield & Farm Efficiency (ONLY real calculated metrics) ─
        yield_data = None
        has_yield_data = False
        if spatial_yield_val is not None and float(spatial_yield_val) > 0:
            has_yield_data = True
            opt_yield = round(float(spatial_yield_val), 2)
            # Baseline monoculture yield estimation
            metrics = ReportAgent._calculate_yield_metrics(land_size_val, spatial_main, spatial_comp)
            base_yield = metrics.get('normal_total', round(opt_yield * 0.82, 2))
            diff_t = round(opt_yield - base_yield, 2)
            diff_pct = round((diff_t / max(0.1, base_yield)) * 100, 1)

            yield_data = {
                'has_yield_data': True,
                'optimized_yield_t': opt_yield,
                'baseline_yield_t': base_yield,
                'difference_t': diff_t,
                'difference_pct': diff_pct,
                'land_size_acres': land_size_val,
                'note': f"Estimated total harvest of {opt_yield} tonnes across {land_size_val} acre(s) under optimized companion spacing."
            }
        else:
            yield_data = {
                'has_yield_data': False,
                'note': "No yield simulation logged yet. Open the Spatial Planner or Yield Comparison to generate quantitative yield projections."
            }

        # ── 7. AI Insights & Grounded Recommendations (NO WEATHER) ───
        ai_insights = ReportAgent._generate_grounded_insights(
            farmer_name=farmer_name,
            land_size=land_size_val,
            soil_info=soil_info,
            plan_info=plan_info,
            spatial_info=spatial_info,
            disease_info=plan_info.get('disease_diagnosis')
        )

        # ── 8. System Limitations ────────────────────────────────────
        limitations = [
            "Yield values are algorithmic estimates derived from published botanical spacing models and intercropping coefficients, not real-time satellite telemetry.",
            "Spatial layout planning assumes a uniform plot gradient; adjustments must be made on-field for irregular topography, slopes, and drainage channels.",
            "Soil macronutrient data reflects submitted test records; periodic laboratory soil testing is recommended to calibrate fertilizer requirements.",
            "No dynamic automated weather telemetry is integrated into this report; verify current regional conditions prior to critical field operations.",
            "Consult local agricultural extension officers or university farm advisory centers before large-scale implementation of chemical treatments."
        ]

        # ── 9. Reports count ─────────────────────────────────────────
        report_count = 0
        try:
            rc_res = execute_fluxbase_sql(f"SELECT COUNT(*) as cnt FROM reports WHERE farmer_id={fid}")
            report_count = rc_res['rows'][0].get('cnt', 0) if rc_res.get('rows') else 0
        except Exception:
            pass

        current_time_str = time.strftime("%d %B %Y, %I:%M %p")

        # ── 10. Summary Lines for Quick Takeaway (NO WEATHER) ─────────
        s_lines = [
            f"Farm Details: {farmer_name}'s {land_size_val}-acre holding in {location} has {soil_type.lower()} soil with {water_avail.lower()} water capacity.",
            f"Crop Recommendation: System recommends {rec_crops_str} based on soil parameters and regional agro-climatic profile.",
            f"Active Crop Plan: {planned_crop} — sowing window: {sowing_sched[:50]}; irrigation: {irrig_plan[:50]}.",
            f"Spatial Layout: {spatial_mode} pairing {spatial_main} with {spatial_comp} (layout score: {spatial_score}/100) using hexagonal spacing.",
        ]
        if has_yield_data:
            s_lines.append(f"Yield Impact: Projected harvest of {yield_data['optimized_yield_t']} tonnes (+{yield_data['difference_pct']}% over traditional baseline).")
        if crop_sync_note:
            s_lines.append(f"Crop Status Note: Crop plan is configured for {planned_crop}, while spatial twin is modeled for {spatial_main} + {spatial_comp}.")

        report_data = {
            "farmer_name": farmer_name,
            "user_email": user_email,
            "location": location,
            "land_size": str(land_size_val),
            "generated_at": current_time_str,
            "report_number": report_count + 1,
            "summary_lines": s_lines,
            "report": "\n".join(s_lines),
            "sections": {
                "header": {
                    "title": "Field Advisory Report",
                    "farmer_name": farmer_name,
                    "report_number": report_count + 1,
                    "generated_at": current_time_str,
                    "location": location,
                    "land_size_acres": land_size_val,
                },
                "section_1_farmer": {
                    "title": "Farmer & Farm Details",
                    "farmer_name": farmer_name,
                    "land_size_acres": land_size_val,
                    "location": location,
                    "soil_type": soil_type,
                    "nitrogen": n_val,
                    "phosphorus": p_val,
                    "potassium": k_val,
                    "ph": ph_val,
                    "soil_moisture": moisture_val,
                    "water_availability": water_avail,
                    "farming_goals": farming_goals,
                    "has_npk": soil_info['has_npk']
                },
                "section_2_recommendations": {
                    "title": "Crop Recommendations",
                    "recommended_crops": rec_crops_list,
                    "crops_str": rec_crops_str,
                    "reason": rec_info['recommendation_reason'],
                    "factors": rec_info['factors_used']
                },
                "section_3_crop_plan": {
                    "title": "Active Crop Plan",
                    "planned_crop": planned_crop,
                    "sowing_schedule": sowing_sched,
                    "irrigation_plan": irrig_plan,
                    "fertilizer_schedule": fert_sched,
                    "pest_alerts": pest_alerts,
                    "harvest_timeline": harvest_time,
                    "status": plan_status,
                    "disease_diagnosis": plan_info['disease_diagnosis']
                },
                "section_4_spatial_twin": {
                    "title": "Spatial Twin / Farm Layout",
                    "main_crop": spatial_main,
                    "companion_crop": spatial_comp,
                    "layout_mode": spatial_mode,
                    "layout_score": spatial_score,
                    "main_spacing_cm": main_spacing,
                    "comp_spacing_cm": comp_spacing,
                    "sunlight_note": sunlight_note,
                    "land_efficiency_pct": spatial_info['land_efficiency_pct'],
                    "nitrogen_balance": spatial_info['nitrogen_balance'],
                    "algorithm_note": spatial_info['algorithm_note'],
                    "crops_match": crops_match,
                    "crop_sync_note": crop_sync_note
                },
                "section_5_yield_efficiency": {
                    "title": "Yield & Farm Efficiency",
                    "has_yield_data": has_yield_data,
                    "data": yield_data
                },
                "section_6_ai_insights": {
                    "title": "AI Insights & Grounded Recommendations",
                    "insights": ai_insights
                },
                "section_7_limitations": {
                    "title": "System Limitations & Agronomic Notes",
                    "items": limitations
                }
            }
        }

        # Save to reports table in Fluxbase
        try:
            safe_text = "\n".join(s_lines).replace("'", "''")
            execute_fluxbase_sql(f"INSERT INTO reports (farmer_id, report_text) VALUES ({fid}, '{safe_text}')")
        except Exception as insert_err:
            print(f"   [Report] DB save error: {insert_err}")

        print(f"   ✅ Field Advisory Report synthesized successfully (7 Sections, No Weather)")
        print("=" * 60 + "\n")
        return report_data

    @staticmethod
    def build_html_email(report_data: dict, custom_notes: str = "") -> str:
        """Generate a professionally styled, responsive HTML email containing all 7 report sections (NO WEATHER)."""
        sections = report_data.get('sections', {})
        header = sections.get('header', {})
        s1 = sections.get('section_1_farmer', {})
        s2 = sections.get('section_2_recommendations', {})
        s3 = sections.get('section_3_crop_plan', {})
        s4 = sections.get('section_4_spatial_twin', {})
        s5 = sections.get('section_5_yield_efficiency', {})
        s6 = sections.get('section_6_ai_insights', {})
        s7 = sections.get('section_7_limitations', {})

        # Build custom note block if provided
        notes_block = ""
        if custom_notes:
            notes_block = f"""
            <div style="background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 14px 18px; border-radius: 6px; margin: 18px 0 24px 0;">
                <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 700; color: #166534; text-transform: uppercase;">Message from Sender</p>
                <p style="margin: 0; font-size: 14px; color: #1e293b; line-height: 1.5;">{custom_notes}</p>
            </div>
            """

        # Section 1: Farmer & Farm Details
        npk_display = f"N={s1.get('nitrogen')} | P={s1.get('phosphorus')} | K={s1.get('potassium')} mg/kg" if s1.get('has_npk') else "Pending laboratory test"
        ph_display = f"<br><b>Soil pH:</b> {s1.get('ph')}" if s1.get('ph') is not None else ""

        # Section 2: Recommended crops badges
        rec_badges = " ".join([f"<span style='display: inline-block; background: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 999px; font-size: 13px; font-weight: 600; margin: 2px 4px 2px 0; border: 1px solid #86efac;'>{c}</span>" for c in s2.get('recommended_crops', [])])

        # Section 3: Crop Plan
        disease_block = ""
        diag = s3.get('disease_diagnosis')
        if diag and isinstance(diag, dict) and diag.get('diagnosis'):
            disease_block = f"""
            <div style="background: #fff7ed; border-left: 3px solid #ea580c; padding: 10px 14px; border-radius: 6px; margin-top: 12px;">
                <b style="color: #9a3412; font-size: 13px;">Recent Disease Diagnosis:</b> {diag.get('diagnosis')} (Confidence: {diag.get('confidence', 'N/A')})<br>
                <span style="font-size: 12px; color: #7c2d12;">Treatment: {str(diag.get('treatment',''))[:120]}</span>
            </div>
            """

        # Section 4: Spatial Twin
        sync_notice_block = ""
        if s4.get('crop_sync_note'):
            sync_notice_block = f"""
            <div style="background: #eff6ff; border-left: 3px solid #3b82f6; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;">
                <span style="font-size: 12px; color: #1e40af; line-height: 1.5;">ℹ️ <b>Multi-Module Status:</b> {s4.get('crop_sync_note')}</span>
            </div>
            """

        # Section 5: Yield & Farm Efficiency
        yield_content = ""
        if s5.get('has_yield_data'):
            yd = s5.get('data', {})
            yield_content = f"""
            <table width="100%" cellpadding="8" cellspacing="0" style="border-collapse: collapse; margin-top: 8px; font-size: 13px;">
                <tr style="background: #f8fafc;">
                    <td style="border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Optimized Yield</td>
                    <td style="border: 1px solid #e2e8f0; font-weight: 700; color: #15803d;">{yd.get('optimized_yield_t')} tonnes</td>
                    <td style="border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Baseline Monoculture</td>
                    <td style="border: 1px solid #e2e8f0; color: #64748b;">{yd.get('baseline_yield_t')} tonnes</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Net Gain</td>
                    <td style="border: 1px solid #e2e8f0; font-weight: 700; color: #16a34a;" colspan="3">+{yd.get('difference_t')} tonnes (+{yd.get('difference_pct')}%) across {yd.get('land_size_acres')} acre(s)</td>
                </tr>
            </table>
            """
        else:
            yield_content = "<p style='font-size: 13px; color: #64748b; margin: 6px 0;'>No yield simulation recorded for this profile yet. Run the Spatial Planner to calculate field yields.</p>"

        # Section 6: AI Insights
        insights_html = "".join([f"<li style='margin-bottom: 8px; font-size: 13px; color: #334155; line-height: 1.5;'>{pt}</li>" for pt in s6.get('insights', [])])

        # Section 7: Limitations
        limitations_html = "".join([f"<li style='margin-bottom: 6px; font-size: 12px; color: #64748b; line-height: 1.4;'>{pt}</li>" for pt in s7.get('items', [])])

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SuperFarmer - Field Advisory Report</title>
</head>
<body style="margin: 0; padding: 20px; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; background-color: #f1f5f9; color: #1e293b;">
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 640px; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; margin: 0 auto;">
        <!-- Header Banner with Logo -->
        <tr>
            <td align="center" style="background: linear-gradient(135deg, #166534 0%, #15803d 100%); padding: 28px 20px; text-align: center;">
                <img src="cid:superfarmer_logo" alt="SuperFarmer Logo" width="110" height="110" style="display: block; margin: 0 auto; width: 110px; height: 110px; border-radius: 50%; background: #ffffff; padding: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.18);" />
                <h1 style="color: #ffffff; margin: 14px 0 0 0; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">SuperFarmer</h1>
                <p style="color: #bbf7d0; margin: 4px 0 0 0; font-size: 13px;">FIELD ADVISORY REPORT • #{header.get('report_number', 1)}</p>
                <p style="color: #ffffff; margin: 8px 0 0 0; font-size: 14px; font-weight: 600;">Prepared for: {header.get('farmer_name')} • {header.get('generated_at')}</p>
            </td>
        </tr>

        <!-- Body Content -->
        <tr>
            <td style="padding: 28px 24px;">
                {notes_block}

                <!-- Section 1 -->
                <div style="margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 18px;">
                    <h3 style="color: #166534; font-size: 15px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 0.04em;">
                        🏡 Section 1 — Farmer & Farm Details
                    </h3>
                    <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 13px; color: #334155;">
                        <tr>
                            <td width="50%"><b>Farmer Name:</b> {s1.get('farmer_name')}</td>
                            <td width="50%"><b>Holding Size:</b> {s1.get('land_size_acres')} acre(s)</td>
                        </tr>
                        <tr>
                            <td><b>Location:</b> {s1.get('location')}</td>
                            <td><b>Soil Type:</b> {s1.get('soil_type')}</td>
                        </tr>
                        <tr>
                            <td><b>Soil NPK:</b> {npk_display}</td>
                            <td><b>Water Availability:</b> {s1.get('water_availability')}</td>
                        </tr>
                        <tr>
                            <td colspan="2"><b>Farming Goals:</b> {s1.get('farming_goals')}{ph_display}</td>
                        </tr>
                    </table>
                </div>

                <!-- Section 2 -->
                <div style="margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 18px;">
                    <h3 style="color: #166534; font-size: 15px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 0.04em;">
                        🌾 Section 2 — Crop Recommendation
                    </h3>
                    <div style="margin-bottom: 8px;">{rec_badges}</div>
                    <p style="margin: 0; font-size: 13px; color: #475569; line-height: 1.5;">
                        <b>Selection Logic:</b> {s2.get('reason')}
                    </p>
                </div>

                <!-- Section 3 -->
                <div style="margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 18px;">
                    <h3 style="color: #166534; font-size: 15px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 0.04em;">
                        📋 Section 3 — Active Crop Plan ({s3.get('planned_crop')})
                    </h3>
                    <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 13px; color: #334155;">
                        <tr><td><b>Sowing Window:</b> {s3.get('sowing_schedule')}</td></tr>
                        <tr><td><b>Irrigation Protocol:</b> {s3.get('irrigation_plan')}</td></tr>
                        <tr><td><b>Fertilizer Schedule:</b> {s3.get('fertilizer_schedule')}</td></tr>
                        <tr><td><b>Pest Management:</b> {s3.get('pest_alerts')}</td></tr>
                    </table>
                    {disease_block}
                </div>

                <!-- Section 4 -->
                <div style="margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 18px;">
                    <h3 style="color: #166534; font-size: 15px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 0.04em;">
                        🗺️ Section 4 — Spatial Twin Layout ({s4.get('main_crop')} + {s4.get('companion_crop')})
                    </h3>
                    {sync_notice_block}
                    <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 13px; color: #334155;">
                        <tr>
                            <td width="50%"><b>Layout Mode:</b> {s4.get('layout_mode')}</td>
                            <td width="50%"><b>Layout Quality Score:</b> {s4.get('layout_score')}/100</td>
                        </tr>
                        <tr>
                            <td><b>Main Crop Spacing:</b> {s4.get('main_spacing_cm')} cm</td>
                            <td><b>Companion Spacing:</b> {s4.get('comp_spacing_cm')} cm</td>
                        </tr>
                        <tr>
                            <td colspan="2"><b>Solar Orientation:</b> {s4.get('sunlight_note')}</td>
                        </tr>
                        <tr>
                            <td colspan="2"><b>Soil/Nitrogen Dynamics:</b> {s4.get('nitrogen_balance')}</td>
                        </tr>
                    </table>
                    <p style="margin: 8px 0 0 0; font-size: 11px; color: #64748b; font-style: italic;">
                        *{s4.get('algorithm_note')}
                    </p>
                </div>

                <!-- Section 5 -->
                <div style="margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 18px;">
                    <h3 style="color: #166534; font-size: 15px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 0.04em;">
                        📊 Section 5 — Yield & Farm Efficiency
                    </h3>
                    {yield_content}
                </div>

                <!-- Section 6 -->
                <div style="margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 18px;">
                    <h3 style="color: #166534; font-size: 15px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 0.04em;">
                        🧠 Section 6 — AI Insights & Agronomic Guidance
                    </h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        {insights_html}
                    </ul>
                </div>

                <!-- Section 7 -->
                <div>
                    <h3 style="color: #475569; font-size: 14px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.04em;">
                        ⚠️ Section 7 — System Limitations & Advisory Notes
                    </h3>
                    <ul style="margin: 0; padding-left: 18px;">
                        {limitations_html}
                    </ul>
                </div>
            </td>
        </tr>

        <!-- Footer -->
        <tr>
            <td style="background-color: #f8fafc; padding: 18px 24px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8;">
                © 2026 SuperFarmer Platform • Empowering Farmers with Agentic AI • Generated on demand by user request
            </td>
        </tr>
    </table>
</body>
</html>"""
        return html


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
        # ── Previously missing — companion warning was always firing ──
        'Garlic':    ['Marigold', 'Onion', 'Tomato'],
        'Mustard':   ['Chickpea', 'Soybean', 'Wheat'],
        'Chickpea':  ['Mustard', 'Soybean', 'Wheat'],
        'Sunflower': ['Maize', 'Groundnut', 'Soybean'],
        'Groundnut': ['Corn', 'Maize', 'Soybean', 'Sunflower'],
        'Soybean':   ['Corn', 'Maize', 'Groundnut', 'Sunflower'],
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

    # ── NITROGEN-FIXER lookup (used by decision rules) ─────────────
    _N_FIXERS = {'Chickpea', 'Soybean', 'Groundnut'}
    # High-water crops that cannot survive Low-water farms
    _HIGH_WATER_CROPS = {'Rice', 'Sugarcane', 'Tomato'}
    # Drought-tolerant override pool
    _DRY_FALLBACKS = ['Wheat', 'Chickpea', 'Groundnut', 'Mustard', 'Soybean']

    @staticmethod
    def _fetch_farmer_memory(farmer_id):
        """
        MEMORY FETCH — Pull farmer history from Fluxbase.
        Returns a dict with: prev_crop, nitrogen_level, water, past_yield.
        All fields default gracefully if data is missing.
        """
        memory = {
            'prev_crop':      None,   # crop_name from latest crop_plan
            'nitrogen_level': 'Medium', # derived from crop history
            'water':          'Medium', # water_availability from profile
            'past_yield':     None,   # from spatial_twin_log (if exists)
            'location':       'Unknown',
            'land_size':      1.0,
            'farmer_name':    'Unknown',
        }
        try:
            # Profile
            p = execute_fluxbase_sql(
                f"SELECT name, location, land_size, water_availability FROM farmer_profile "
                f"WHERE farmer_id={int(farmer_id)} LIMIT 1"
            )
            if p.get('rows'):
                row = p['rows'][0]
                memory['farmer_name'] = row.get('name', 'Unknown')
                memory['location']    = row.get('location', 'Unknown')
                memory['water']       = (row.get('water_availability') or 'Medium').strip().capitalize()
                try:
                    memory['land_size'] = float(row.get('land_size', 1.0))
                except (TypeError, ValueError):
                    pass
        except Exception as e:
            print(f"   [Memory] Profile fetch failed: {e}")

        try:
            # Previous season crop from latest crop_plan
            cp = execute_fluxbase_sql(
                f"SELECT crop_name FROM crop_plans WHERE farmer_id={int(farmer_id)} "
                f"ORDER BY created_at DESC LIMIT 1"
            )
            if cp.get('rows'):
                memory['prev_crop'] = (cp['rows'][0].get('crop_name') or '').strip()
        except Exception as e:
            print(f"   [Memory] Crop plan fetch failed: {e}")

        try:
            # Derive nitrogen level: if a N-fixing crop was previously recommended → soil was N-depleted
            cr = execute_fluxbase_sql(
                f"SELECT recommended_crops FROM crop_recommendations WHERE farmer_id={int(farmer_id)} "
                f"ORDER BY created_at DESC LIMIT 1"
            )
            if cr.get('rows'):
                rec_str = (cr['rows'][0].get('recommended_crops') or '').lower()
                # If a legume was top-recommended → soil was low in N
                if any(nf in rec_str for nf in ['chickpea', 'soybean', 'groundnut', 'lentil']):
                    memory['nitrogen_level'] = 'Low'
                elif any(hi in rec_str for hi in ['sugarcane', 'rice', 'cotton']):
                    memory['nitrogen_level'] = 'High'
                else:
                    memory['nitrogen_level'] = 'Medium'
        except Exception as e:
            print(f"   [Memory] Crop rec fetch failed: {e}")

        try:
            # Past yield from spatial_twin_log (graceful skip if table missing)
            sl = execute_fluxbase_sql(
                f"SELECT total_yield_t, main_crop FROM spatial_twin_log WHERE farmer_id={int(farmer_id)} "
                f"ORDER BY created_at DESC LIMIT 1"
            )
            if sl.get('rows'):
                memory['past_yield']      = sl['rows'][0].get('total_yield_t')
                memory['past_twin_crop']  = sl['rows'][0].get('main_crop', '')
        except Exception:
            pass  # table may not exist yet

        return memory

    @staticmethod
    def _run_decision_rules(user_crop_key, memory):
        """
        STEP 1-3 MEMORY DECISION ENGINE — deterministic rule application.
        Returns: final_crop_key, companion_override, memory_log[], warnings[], soil_impact, override details.
        """
        DB         = SpatialPlannerAgent.CROP_DB
        N_FIXERS   = SpatialPlannerAgent._N_FIXERS
        HW_CROPS   = SpatialPlannerAgent._HIGH_WATER_CROPS
        DRY_POOL   = SpatialPlannerAgent._DRY_FALLBACKS
        MATRIX     = SpatialPlannerAgent.COMPANION_MATRIX

        final_crop      = user_crop_key
        companion_override = None
        memory_log      = []
        warnings        = []
        soil_impact     = 'neutral'
        override_crop   = None
        override_reason = None

        prev_crop  = (memory.get('prev_crop') or '').strip()
        nitrogen   = memory.get('nitrogen_level', 'Medium')
        water_farm = memory.get('water', 'Medium')          # Low / Medium / High
        water_crop = DB.get(user_crop_key, {}).get('water', 'Medium')

        # ── STEP 1: Memory Analysis ──────────────────────────────────
        if prev_crop:
            memory_log.append(f"✅ Step 1: Previous season crop was '{prev_crop}'.")
        else:
            memory_log.append("✅ Step 1: No previous crop record found — first season or new farmer.")

        memory_log.append(f"✅ Step 2: Soil nitrogen level inferred as '{nitrogen}' from crop history.")
        memory_log.append(f"✅ Step 3: Farm water availability is '{water_farm}'. "
                          f"Selected crop '{user_crop_key}' needs '{water_crop}' water.")

        # ── STEP 2A: Crop Rotation Rule ──────────────────────────────
        if prev_crop and prev_crop.lower() == user_crop_key.lower():
            warnings.append(
                f"⚠️ Crop Rotation Risk: '{prev_crop}' was grown last season. "
                f"Repeating the same crop depletes specific soil nutrients and increases pest pressure."
            )
            memory_log.append(
                f"⚠️ Step 4 (Rotation): Same crop '{prev_crop}' repeated. "
                f"Forcing a nitrogen-fixing companion to recover soil fertility."
            )
            # Force N-fixing companion to mitigate soil depletion
            # Pick best N-fixer that is a valid companion for this crop
            valid_companions = MATRIX.get(user_crop_key, [])
            fixer_companions = [c for c in valid_companions if c in N_FIXERS]
            if fixer_companions:
                companion_override = max(fixer_companions,
                    key=lambda c: DB[c].get('companion_score', 0))
                memory_log.append(
                    f"✅ Step 4 (Rotation fix): Companion forced to '{companion_override}' "
                    f"(nitrogen-fixer) to restore soil health."
                )
            else:
                # Fallback: any N-fixer available in DB
                companion_override = 'Chickpea' if 'Chickpea' in DB else 'Soybean'
                memory_log.append(
                    f"✅ Step 4 (Rotation fix): Global fallback companion '{companion_override}' applied."
                )

        # ── STEP 2B: Soil Nitrogen Rule ──────────────────────────────
        if nitrogen == 'Low' and companion_override not in N_FIXERS:
            # Force N-fixer as companion (may override rotation selection too)
            valid_companions = MATRIX.get(final_crop, [])
            fixer_companions = [c for c in valid_companions if c in N_FIXERS]
            if fixer_companions:
                companion_override = max(fixer_companions,
                    key=lambda c: DB[c].get('companion_score', 0))
            else:
                companion_override = 'Chickpea' if 'Chickpea' in DB else 'Soybean'
            memory_log.append(
                f"✅ Step 5 (Nitrogen): Soil N is Low → companion '{companion_override}' "
                f"selected to fix nitrogen and restore soil health."
            )
            soil_impact = 'improves'

        # ── STEP 2C: Water Matching Rule ─────────────────────────────
        if water_farm == 'Low' and user_crop_key in HW_CROPS:
            # Override: find a drought-tolerant crop from the fallback pool
            alt_crop = next((c for c in DRY_POOL if c in DB and c != user_crop_key), 'Wheat')
            override_reason = (
                f"Farm water availability is Low, but '{user_crop_key}' requires High water. "
                f"Switched to '{alt_crop}' which is drought-tolerant."
            )
            memory_log.append(f"⚠️ Step 6 (Water): {override_reason}")
            warnings.append(
                f"⚠️ Water Mismatch Detected: '{user_crop_key}' needs High water but your farm has "
                f"Low availability. Crop overridden to '{alt_crop}'."
            )
            final_crop    = alt_crop
            override_crop = alt_crop
            # Reset companion for the new crop
            companion_override = None

        # ── STEP 3: Soil Impact Assessment ───────────────────────────
        if soil_impact == 'neutral':
            final_crop_data = DB.get(final_crop, {})
            comp_data       = DB.get(companion_override, {}) if companion_override else {}
            is_fixer = (
                final_crop_data.get('nitrogen') == 'Fixer' or
                comp_data.get('nitrogen') == 'Fixer' or
                (companion_override in N_FIXERS)
            )
            if is_fixer:
                soil_impact = 'improves'
            elif final_crop_data.get('nitrogen') == 'Consumer':
                soil_impact = 'degrades'

        memory_log.append(
            f"✅ Step 7 (Output): Final decision — Crop: '{final_crop}', "
            f"Companion override: '{companion_override or 'auto-select'}', "
            f"Soil impact: '{soil_impact}'."
        )

        return {
            'final_crop':       final_crop,
            'companion_override': companion_override,
            'memory_log':       memory_log,
            'warnings':         warnings,
            'soil_impact':      soil_impact,
            'override_crop':    override_crop,
            'override_reason':  override_reason,
        }

    @staticmethod
    def generate_layout(farmer_id, width, height, main_crop, layout_preference="Auto", acres=None):
        """
        Structured Rule-Based Spatial Twin Agent.
        Implements: zone division, hexagonal placement, companion scoring,
        layout preference, border crops, sunlight orientation, quality score.
        """
        import math

        try:
            w = float(width)
            h = float(height)
        except (TypeError, ValueError):
            w, h = 600.0, 420.0

        print(f"\n━" * 60)
        print(f"🗺️  [Spatial Twin] Generating Digital Layout")
        print(f"   Land Bounds  : {w}x{h} px")
        print(f"   Layout Pref  : {layout_preference}")
        print(f"   Main Crop    : {main_crop}")

        # ── 1. Crop Normalization ─────────────────────────────────────
        CROP_ALIASES = {
            'tomatoes': 'Tomato','tomato': 'Tomato',
            'corn': 'Corn','maize': 'Maize','wheat': 'Wheat','rice': 'Rice',
            'sugarcane': 'Sugarcane','cotton': 'Cotton',
            'soybean': 'Soybean','soybeans': 'Soybean',
            'onion': 'Onion','onions': 'Onion',
            'garlic': 'Garlic','potato': 'Potato','potatoes': 'Potato',
            'sunflower': 'Sunflower','sunflowers': 'Sunflower',
            'mustard': 'Mustard','chickpea': 'Chickpea','chickpeas': 'Chickpea',
            'groundnut': 'Groundnut','groundnuts': 'Groundnut','peanut': 'Groundnut',
            'marigold': 'Marigold','marigolds': 'Marigold',
        }
        raw = (main_crop or '').strip()
        if raw and raw != 'Auto':
            normalized = CROP_ALIASES.get(raw.lower(), raw)
            requested_crop_key = normalized if normalized in SpatialPlannerAgent.CROP_DB else 'Corn'
        else:
            requested_crop_key = 'Corn'

        print(f"   Crop Lookup  : '{raw}' → '{requested_crop_key}'")

        # ── 2. Memory Fetch ──────────────────────────────────────────
        print(f"   [Memory] Fetching farmer history for farmer_id={farmer_id}...")
        memory = SpatialPlannerAgent._fetch_farmer_memory(farmer_id)

        # Resolve land size: prefer map-drawn acres, then DB value
        farmer_name   = memory['farmer_name']
        land_size_val = float(acres) if acres else memory['land_size']
        try:
            land_size_val = float(land_size_val)
        except (TypeError, ValueError):
            land_size_val = 1.0

        print(f"   [Memory] prev_crop='{memory['prev_crop']}' | nitrogen='{memory['nitrogen_level']}' | water='{memory['water']}'")

        # ── 3. Decision Rules ────────────────────────────────────────
        decision = SpatialPlannerAgent._run_decision_rules(requested_crop_key, memory)
        main_crop_key = decision['final_crop']
        main_data     = SpatialPlannerAgent.CROP_DB[main_crop_key]

        if decision['override_crop']:
            print(f"   [Memory] ⚠️  Crop overridden: '{requested_crop_key}' → '{main_crop_key}'")
        for log_line in decision['memory_log']:
            print(f"   [Memory] {log_line}")

        # ── 3. Score-Based Companion Selection ───────────────────────
        # Rank by companion_score in CROP_DB (highest wins)
        companions_raw = SpatialPlannerAgent.COMPANION_MATRIX.get(main_crop_key, [])
        valid_companions = [c for c in companions_raw if c in SpatialPlannerAgent.CROP_DB]
        if valid_companions:
            companion_key = max(valid_companions,
                                key=lambda c: SpatialPlannerAgent.CROP_DB[c].get('companion_score', 0))
        else:
            companion_key = 'Marigold'
        companion_data = SpatialPlannerAgent.CROP_DB[companion_key]

        print(f"   Partnership  : {main_data['name']} + {companion_data['name']} "
              f"(score {companion_data.get('companion_score',0)}/10)")

        # ── 4. Zone Division with Layout Preference ──────────────────
        pref = (layout_preference or 'Auto').strip()

        def _make_zones_strip():
            """Vertical strip division based on spacing weight."""
            total_weight = (1.0/main_data['spacing']) + (1.0/companion_data['spacing'])
            w_main = math.floor(w * (1.0/main_data['spacing']) / total_weight)
            return [
                {'x': 0,      'y': 0, 'w': w_main,   'h': h,
                 'crop': main_data['name'],      'color': main_data['color'],
                 'label': f"Zone 1 – {main_data['name']} (Strip)"},
                {'x': w_main, 'y': 0, 'w': w-w_main,  'h': h,
                 'crop': companion_data['name'], 'color': companion_data['color'],
                 'label': f"Zone 2 – {companion_data['name']} (Strip)"},
            ]

        def _make_zones_row():
            """Horizontal row division."""
            total_weight = (1.0/main_data['spacing']) + (1.0/companion_data['spacing'])
            h_main = math.floor(h * (1.0/main_data['spacing']) / total_weight)
            return [
                {'x': 0, 'y': 0,      'w': w, 'h': h_main,
                 'crop': main_data['name'],      'color': main_data['color'],
                 'label': f"Zone 1 – {main_data['name']} (Row)"},
                {'x': 0, 'y': h_main, 'w': w, 'h': h-h_main,
                 'crop': companion_data['name'], 'color': companion_data['color'],
                 'label': f"Zone 2 – {companion_data['name']} (Row)"},
            ]

        def _make_zones_grid():
            """Checkerboard interleaving — single full-canvas zone per crop,
            nodes are interleaved by row parity inside hex_layout_interleaved."""
            return [
                {'x': 0, 'y': 0, 'w': w, 'h': h,
                 'crop': main_data['name'],      'color': main_data['color'],
                 'label': f"Zone 1 – {main_data['name']} (Grid)"},
                {'x': 0, 'y': 0, 'w': w, 'h': h,
                 'crop': companion_data['name'], 'color': companion_data['color'],
                 'label': f"Zone 2 – {companion_data['name']} (Grid)"},
            ]

        if pref == 'Strip Layout':
            zones = _make_zones_strip()
            layout_mode = 'strip'
        elif pref == 'Row Layout':
            zones = _make_zones_row()
            layout_mode = 'row'
        elif pref == 'Grid Layout':
            zones = _make_zones_grid()
            layout_mode = 'grid'
        else:  # Auto — spacing-weight strip (default)
            zones = _make_zones_strip()
            layout_mode = 'auto'

        # ── 5. Sunlight orientation hint ─────────────────────────────
        # Taller crop placed in the first zone (west/north) to avoid shading
        if main_data['height_m'] < companion_data['height_m'] and layout_mode in ('strip','auto'):
            zones[0]['crop']  = companion_data['name']
            zones[0]['color'] = companion_data['color']
            zones[0]['label'] = zones[0]['label'].replace(main_data['name'], companion_data['name']) + ' [tall→N]'
            zones[1]['crop']  = main_data['name']
            zones[1]['color'] = main_data['color']
            zones[1]['label'] = zones[1]['label'].replace(companion_data['name'], main_data['name'])
            crop_order = [companion_data, main_data]
            sunlight_note = (f"{companion_data['name']} (taller, {companion_data['height_m']}m) placed on "
                             f"north/west to avoid shading {main_data['name']} ({main_data['height_m']}m).")
        else:
            crop_order = [main_data, companion_data]
            sunlight_note = (f"{main_data['name']} ({main_data['height_m']}m) and "
                             f"{companion_data['name']} ({companion_data['height_m']}m) placed west→east. "
                             f"Monitor for shade if taller plants face east.")

        # ── 6. Plant Node Generation ─────────────────────────────────
        all_nodes = []
        if layout_mode == 'grid':
            # Interleaved hex: odd rows = main_data, even rows = companion_data
            full_zone = {'x': 0, 'y': 0, 'w': w, 'h': h}
            sp_main = main_data['spacing']
            sp_comp = companion_data['spacing']
            row = 0
            y_cur = sp_main * 0.5
            while y_cur < h - sp_main * 0.4:
                cur_crop = main_data if row % 2 == 0 else companion_data
                sp = cur_crop['spacing']
                x_shift = (row % 2) * (sp / 2.0)
                col = 0
                x_cur = x_shift + sp * 0.5
                while x_cur < w - sp * 0.4:
                    all_nodes.append({
                        'x': round(x_cur, 2), 'y': round(y_cur, 2),
                        'type': cur_crop['name'], 'color': cur_crop['color'],
                        'radius': max(4.0, sp * 0.32),
                        'row': row, 'col': col,
                        'height_m': cur_crop.get('height_m', 1.0),
                        'zone': 1 if cur_crop == main_data else 2
                    })
                    col += 1
                    x_cur += sp
                row += 1
                y_cur += math.floor(sp_main * 0.866)
        else:
            for i, crop in enumerate(crop_order):
                zone = zones[i]
                nodes = SpatialPlannerAgent.hex_layout(crop, zone)
                for n in nodes:
                    n['zone'] = i + 1
                all_nodes.extend(nodes)

        # ── 7. Edge / Border Crop (Marigold ring) ───────────────────
        border_nodes = []
        border_crop_name = 'Marigold'
        BORDER_MARGIN = 8   # px from edge
        if main_crop_key != 'Marigold' and companion_key != 'Marigold':
            border_data = SpatialPlannerAgent.CROP_DB['Marigold']
            bsp = border_data['spacing']
            # Top edge
            bx = bsp * 0.5
            while bx < w:
                border_nodes.append({'x': round(bx,2), 'y': BORDER_MARGIN,
                    'type': 'Marigold', 'color': border_data['color'],
                    'radius': max(4.0, bsp*0.3), 'row': -1, 'col': -1,
                    'height_m': border_data['height_m'], 'zone': 0, 'border': True})
                bx += bsp
            # Bottom edge
            bx = bsp * 0.5
            while bx < w:
                border_nodes.append({'x': round(bx,2), 'y': h - BORDER_MARGIN,
                    'type': 'Marigold', 'color': border_data['color'],
                    'radius': max(4.0, bsp*0.3), 'row': -1, 'col': -1,
                    'height_m': border_data['height_m'], 'zone': 0, 'border': True})
                bx += bsp
            # Left edge
            by = bsp
            while by < h - BORDER_MARGIN:
                border_nodes.append({'x': BORDER_MARGIN, 'y': round(by,2),
                    'type': 'Marigold', 'color': border_data['color'],
                    'radius': max(4.0, bsp*0.3), 'row': -1, 'col': -1,
                    'height_m': border_data['height_m'], 'zone': 0, 'border': True})
                by += bsp
            # Right edge
            by = bsp
            while by < h - BORDER_MARGIN:
                border_nodes.append({'x': w - BORDER_MARGIN, 'y': round(by,2),
                    'type': 'Marigold', 'color': border_data['color'],
                    'radius': max(4.0, bsp*0.3), 'row': -1, 'col': -1,
                    'height_m': border_data['height_m'], 'zone': 0, 'border': True})
                by += bsp

        full_layout = border_nodes + all_nodes   # border rendered first (below)

        # ── Apply companion override from decision rules ──────────────
        # (override was set before companion_key was resolved; apply now if still relevant)
        if decision.get('companion_override') and decision['companion_override'] in SpatialPlannerAgent.CROP_DB:
            co_key = decision['companion_override']
            if co_key != companion_key:
                companion_key  = co_key
                companion_data = SpatialPlannerAgent.CROP_DB[companion_key]
                print(f"   [Memory] Companion overridden to '{companion_key}' by decision rules.")

        print(f"   Interior Nodes: {len(all_nodes)}  Border Nodes: {len(border_nodes)}")
        print(f"━" * 60 + "\n")

        # ── 8. Insights ──────────────────────────────────────────────
        all_crop_types = [main_data, companion_data]
        fixer_count = sum(1 for c in all_crop_types if c['nitrogen'] == 'Fixer')
        nitrogen_balance = (f"{fixer_count} nitrogen-fixing crop(s) present — synthetic fertilizer not required"
                            if fixer_count > 0
                            else "No nitrogen-fixing crop — add a legume or apply 40 kg/acre urea")

        avg_water_map = {'Low': 1, 'Medium': 2, 'High': 3}
        total_water_score = sum(avg_water_map.get(c['water'], 2) for c in all_crop_types)
        water_efficiency = round((1 - total_water_score/(len(all_crop_types)*3)) * 30)

        comp_score_raw = companion_data.get('companion_score', 5)
        land_eff = min(95, 70 + comp_score_raw * 2 + (8 if fixer_count > 0 else 0) + (5 if border_nodes else 0))
        yield_boost = min(40, comp_score_raw * 3 + (8 if fixer_count > 0 else 0))

        # Yield per zone
        zone_yields = []
        for i, crop in enumerate(crop_order):
            if layout_mode == 'grid':
                za = land_size_val * 0.5
            else:
                za = (zones[i]['w'] / w) * land_size_val if layout_mode in ('strip','auto') else (zones[i]['h'] / h) * land_size_val
            zone_yields.append({'crop': crop['name'], 'acres': round(za,2),
                                'yield_t': round(crop['yield_t_per_acre'] * za, 2)})
        total_yield = sum(z['yield_t'] for z in zone_yields)
        if border_nodes:
            border_yield = round(SpatialPlannerAgent.CROP_DB['Marigold']['yield_t_per_acre'] * 0.05, 2)
            zone_yields.append({'crop': 'Marigold (border)', 'acres': 0.05, 'yield_t': border_yield})
            total_yield += border_yield

        warnings = []
        if companion_data['name'] not in companions_raw:
            warnings.append(f"⚠ {companion_data['name']} is not a confirmed companion for {main_data['name']}.")
        if any(c['water'] == 'High' for c in all_crop_types) and any(c['water'] == 'Low' for c in all_crop_types):
            warnings.append("⚠ Mixed water needs detected — use zone-specific drip irrigation.")
        if main_data.get('shade') == 'Sensitive' and companion_data['height_m'] > main_data['height_m']:
            warnings.append(f"⚠ {main_data['name']} is shade-sensitive; keep {companion_data['name']} on the north side.")

        # ── 9. Layout Quality Score ──────────────────────────────────
        score_companion = comp_score_raw * 5           # 0–50
        score_nitrogen  = 20 if fixer_count > 0 else 0
        score_water     = 15 if not any('water needs' in w for w in warnings) else 5
        score_border    = 15 if border_nodes else 0
        layout_score    = min(100, score_companion + score_nitrogen + score_water + score_border)

        # ── 10. Limitations (static; always returned) ────────────────
        limitations = [
            "Sunlight direction is approximated (taller crop placed west) but shadow modeling is not performed.",
            "Water source is not spatially mapped — all zones receive uniform irrigation assumptions.",
            "Companion selection uses highest companion_score; no multi-objective optimization.",
            "Farmer soil NPK data is fetched but not used to adjust crop-zone allocation.",
            "Yield calculation is linear (yield_per_acre × area) without layout quality penalties.",
            "No iterative user-feedback loop — layout is generated once per request.",
            f"Layout mode '{pref}' applied; full spatial optimization across all modes is not computed.",
        ]

        # ── 11. Ollama-generated explanation ─────────────────────────
        layout_facts = f"""
Generate a structured, system-level explanation for a Spatial Twin farm layout.

The explanation must NOT be conversational.
Do NOT use phrases like “Hello”, “Let’s talk”, or informal storytelling.
Use a clear, technical but simple tone as if the system is explaining its logic.

---

INPUT:

* Main crop: {main_data['name']} (height: {main_data['height_m']}m, spacing: {main_data['spacing']}cm, water need: {main_data['water']})
* Companion crop: {companion_data['name']} (height: {companion_data['height_m']}m, spacing: {companion_data['spacing']}cm, water need: {companion_data['water']})
* Land size (acres): {land_size_val}
* Layout type: {layout_mode} ({pref})
* Layout score: {layout_score}/100
* Total plants: {len(all_nodes)} interior, {len(border_nodes)} border
* Land efficiency (%): {land_eff}
* Water saving (%): {water_efficiency}
* Yield boost (%): {yield_boost}
* Estimated yield: {round(total_yield, 1)} tonnes
* Zone allocation: {'; '.join([f"{z['crop']}: {z['acres']} acres" for z in zone_yields])}
* Nitrogen fixers present: {'Yes' if fixer_count > 0 else 'No'}
* Sunlight placement: {sunlight_note}
* Warnings: {'; '.join(warnings) if warnings else 'None'}

---

INSTRUCTIONS:

The explanation must be divided into the following sections exactly using these uppercase headers (do NOT use Markdown `#`, just the numbers and text):

1. LAYOUT SUMMARY
Describe the generated layout type, mention land size and crops used, and clearly state that layout is generated using rule-based spatial logic.

2. CROP CHARACTERISTICS
Explain both crops: height, spacing, and growth behavior. Keep it short and factual.

3. ZONE & PLACEMENT LOGIC
Explain how land is divided into zones, which crop occupies which area, and explain placement using: spacing rules, sunlight logic, and companion role.

4. LAYOUT DECISION LOGIC
Explain WHY this layout type was selected. Mention: spacing efficiency, compatibility, and land utilization.

5. YIELD ANALYSIS
Mention estimated yield. Explain reasons: spacing, crop combination, and land efficiency.

6. SYSTEM SCORE EXPLANATION
Explain layout score clearly. Break it into factors (Spacing efficiency, Crop compatibility, Nitrogen support, Water efficiency). Explain why score is high or low based on the INPUT.

7. RESOURCE ANALYSIS
Explain: land efficiency, water savings, and nitrogen balance.

8. LIMITATIONS (IMPORTANT)
Mention current system limitations clearly. Include:
* No advanced sunlight direction modeling
* Water placement is not fully spatial
* Companion selection is rule-based, not fully optimized
* Yield is estimated, not real-time measured

9. RECOMMENDATIONS
Suggest improvements based on the layout (e.g. Add nitrogen-fixing crops, Improve crop compatibility, Adjust spacing or layout, Improve irrigation planning).

RULES:
* Output must be structured with the 9 headings listed above.
* Do NOT generate long paragraphs. Keep each section concise.
* Do NOT generate random explanations.
* Ensure explanation matches input data exactly.
* Maintain deterministic reasoning.
""".strip()

        try:
            analysis = _call_llm(
                system_prompt="You are an expert precision agriculture spatial layout analyzer. Generate a clear, structured, system-level explanation for this digital farm twin.",
                user_message=layout_facts,
                label="SpatialTwin"
            )
        except Exception as _oe:
            print(f"   ⚠️  LLM analysis fallback ({_oe}) — using deterministic analysis.")
            analysis = (
                f"**Digital Farm Twin Generated** — {len(all_nodes)} interior plants + {len(border_nodes)} border Marigolds "
                f"across a **{layout_mode.capitalize()} layout**.\n\n"
                f"**Primary crop:** {main_data['name']} ({main_data['spacing']}cm spacing, {main_data['height_m']}m tall) paired with "
                f"**{companion_data['name']}** ({companion_data['spacing']}cm, {companion_data['height_m']}m).\n\n"
                f"**Sunlight:** {sunlight_note}\n\n"
                f"Land efficiency **{land_eff}%** · Yield boost **{yield_boost}%** · "
                f"Layout quality score **{layout_score}/100**."
            )

        # ── 12. Real Commercial Field Population Calculations ────────
        total_sq_m = round(land_size_val * 4046.86, 1)
        field_dim_m = round(math.sqrt(total_sq_m), 1)

        real_plant_counts = {}
        for z in zone_yields:
            crop_name = z['crop'].replace(' (border)', '')
            crop_info = SpatialPlannerAgent.CROP_DB.get(crop_name, SpatialPlannerAgent.CROP_DB['Corn'])
            sp_m = crop_info['spacing'] / 100.0
            area_m2 = z['acres'] * 4046.86
            plant_count = int(area_m2 / max(0.01, sp_m * sp_m * 0.866))
            real_plant_counts[z['crop']] = {
                'acres': z['acres'],
                'plant_count': plant_count,
                'spacing_cm': crop_info['spacing'],
                'height_m': crop_info.get('height_m', 1.0)
            }

        total_real_plants = sum(v['plant_count'] for v in real_plant_counts.values())
        visual_node_count = len(full_layout)
        node_scale_factor = max(1, round(total_real_plants / max(1, visual_node_count)))

        insights = {
            'total_plants': len(full_layout),
            'interior_plants': len(all_nodes),
            'border_plants': len(border_nodes),
            'total_real_plants': total_real_plants,
            'real_plant_counts': real_plant_counts,
            'total_sq_m': total_sq_m,
            'field_dim_m': f"{field_dim_m}m × {field_dim_m}m",
            'visual_scale_ratio': f"1 3D Node = ~{node_scale_factor:,} Real Field Plants",
            'node_scale_factor': node_scale_factor,
            'total_rows': int(field_dim_m / max(0.2, (main_data['spacing']/100.0))),
            'total_row_km': round((field_dim_m * (field_dim_m / max(0.2, (main_data['spacing']/100.0)))) / 1000.0, 1),
            'land_efficiency': land_eff,
            'water_saving_pct': max(0, water_efficiency),
            'yield_boost_pct': yield_boost,
            'layout_score': layout_score,
            'nitrogen_balance': nitrogen_balance,
            'best_combo': ', '.join(companions_raw[:3]) if companions_raw else 'Marigold, Legumes',
            'sunlight_note': sunlight_note,
            'zone_yields': zone_yields,
            'total_yield': round(total_yield, 2),
            'warnings': warnings,
            'action_items': [
                f"🌱 Field Population: ~{total_real_plants:,} real plants across {land_size_val} acre(s) ({field_dim_m}m × {field_dim_m}m plot)",
                f"🌱 Plant {main_data['name']} with {main_data['spacing']}cm spacing (~{real_plant_counts.get(main_data['name'], {}).get('plant_count', 0):,} plants)",
                f"🌿 Intercrop {companion_data['name']} with {companion_data['spacing']}cm spacing (~{real_plant_counts.get(companion_data['name'], {}).get('plant_count', 0):,} plants)",
                f"🌼 Marigold border: ~{real_plant_counts.get('Marigold (border)', {}).get('plant_count', 0):,} protective border plants" if border_nodes else "Consider adding a Marigold border for pest control",
                f"💧 Irrigation: {main_data['water']} for {main_data['name']}, {companion_data['water']} for {companion_data['name']}",
                "🔬 " + nitrogen_balance,
                f"📦 Estimated total yield: {round(total_yield,1)} tonnes from {land_size_val} acre(s)",
            ]
        }

        # ── Persist to spatial_twin_log ──────────────────────────────
        try:
            execute_fluxbase_sql(
                "CREATE TABLE IF NOT EXISTS spatial_twin_log ("
                "log_id INT AUTO_INCREMENT PRIMARY KEY, "
                "farmer_id INTEGER, "
                "main_crop VARCHAR(64), "
                "companion_crop VARCHAR(64), "
                "layout_mode VARCHAR(32), "
                "land_size_acres FLOAT, "
                "total_yield_t FLOAT, "
                "layout_score INTEGER, "
                "soil_impact VARCHAR(16), "
                "warnings_json TEXT, "
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                ");"
            )
            import json as _json
            _warnings_json = _json.dumps(decision.get('warnings', []))
            execute_fluxbase_sql(
                f"INSERT INTO spatial_twin_log "
                f"(farmer_id, main_crop, companion_crop, layout_mode, land_size_acres, total_yield_t, layout_score, soil_impact, warnings_json) "
                f"VALUES ({int(farmer_id)}, '{safe_str(main_data['name'])}', '{safe_str(companion_data['name'])}', "
                f"'{safe_str(layout_mode)}', {land_size_val}, {round(total_yield, 2)}, {layout_score}, "
                f"'{safe_str(decision.get('soil_impact','neutral'))}', '{safe_str(_warnings_json)}');"
            )
            print("   [Memory] spatial_twin_log row inserted ✓")
        except Exception as _log_err:
            print(f"   [Memory] spatial_twin_log insert skipped: {_log_err}")

        return {
            "layout": full_layout,
            "zones": zones,
            "insights": insights,
            "analysis": analysis,
            "main_crop": main_data['name'],
            "companion": companion_data['name'],
            "farmer_name": farmer_name,
            "land_size": str(land_size_val),
            "layout_mode": layout_mode,
            "layout_score": layout_score,
            "zone_yields": zone_yields,
            "limitations": limitations,
            "sunlight_note": sunlight_note,
            # ── Memory keys ──
            "memory_used":      True,
            "prev_crop":        memory.get('prev_crop'),
            "memory_log":       decision['memory_log'],
            "warnings":         decision['warnings'],
            "soil_impact":      decision['soil_impact'],
            "override_crop":    decision.get('override_crop'),
            "override_reason":  decision.get('override_reason'),
            "requested_crop":   requested_crop_key,
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

    LANGUAGE_MAP = {
        "hi-IN": {"name": "Hindi", "script": "हिन्दी (Devanagari)"},
        "bn-IN": {"name": "Bengali", "script": "বাংলা (Bengali)"},
        "te-IN": {"name": "Telugu", "script": "తెలుగు (Telugu)"},
        "mr-IN": {"name": "Marathi", "script": "मराठी (Devanagari)"},
        "ta-IN": {"name": "Tamil", "script": "தமிழ் (Tamil)"},
        "gu-IN": {"name": "Gujarati", "script": "ગુજરાતી (Gujarati)"},
        "kn-IN": {"name": "Kannada", "script": "ಕನ್ನಡ (Kannada)"},
        "pa-IN": {"name": "Punjabi", "script": "ਪੰਜਾਬੀ (Gurmukhi)"},
        "or-IN": {"name": "Odia", "script": "ଓଡ଼ିଆ (Odia)"},
        "ml-IN": {"name": "Malayalam", "script": "മലയാളം (Malayalam)"},
        "en-IN": {"name": "English", "script": "English (Latin)"},
    }

    @staticmethod
    def chat(message, history, farmer_id=None, language="en-IN"):
        lang_info = SuperFarmerChatAgent.LANGUAGE_MAP.get(language, {})
        target_name = lang_info.get("name", language or "English")
        target_script = lang_info.get("script", language or "English")

        if target_name.lower() != "english":
            lang_directive = (
                f"\n═══════════════════════════════════════════\n"
                f"🚨 MANDATORY LANGUAGE DIRECTIVE (HIGHEST PRIORITY):\n"
                f"The farmer has explicitly chosen: {target_name} ({target_script}).\n"
                f"You MUST generate your ENTIRE response in {target_name} using {target_script} script.\n"
                f"Translate all agricultural advice, recommendations, numbers, and headings into {target_name}.\n"
                f"Even if the farmer asks in English, do NOT respond in English.\n"
                f"═══════════════════════════════════════════\n"
            )
            user_msg = f"{message}\n\n[Mandatory: Write your entire response in {target_name} ({target_script})]"
        else:
            lang_directive = (
                f"\n═══════════════════════════════════════════\n"
                f"LANGUAGE: The farmer has chosen English. Reply in clear, simple English.\n"
                f"═══════════════════════════════════════════\n"
            )
            user_msg = message

        farmer_context = SuperFarmerChatAgent._build_farmer_context(farmer_id)
        full_system_prompt = f"{lang_directive}\n{SuperFarmerChatAgent._BASE_PERSONA}\n{farmer_context}\n{lang_directive}"

        return _call_llm(
            system_prompt=full_system_prompt,
            user_message=user_msg,
            history=history,
            label="SuperFarmerChat"
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
            return SuperFarmerChatAgent.chat(
                message=data['message'],
                history=data.get('history', []),
                farmer_id=data.get('farmer_id'),
                language=data.get('language', 'en-IN')
            )
        elif intent == 'diagnose':
            return DiseaseDiagnosisAgent.diagnose(**data)
        elif intent == 'report':
            return ReportAgent.generate_report(**data)
        elif intent == 'weather':
            return WeatherAgent.analyze_weather(**data)
        elif intent == 'send_email':
            return EmailAgent.send_email(
                data['to_email'],
                data['subject'],
                data['body'],
                image_path=data.get('image_path')
            )
        else:
            return {"error": "Unknown intent"}
