import os
import requests
from dotenv import load_dotenv

load_dotenv()

FLUXBASE_URL = 'https://fluxbase.vercel.app/api/execute-sql'
FLUXBASE_API_KEY = os.environ.get('FLUXBASE_API_KEY')
FLUXBASE_PROJECT_ID = os.environ.get('FLUXBASE_PROJECT_ID')

def execute_fluxbase_sql(query):
    if not FLUXBASE_API_KEY or not FLUXBASE_PROJECT_ID:
        raise Exception("Missing FLUXBASE_API_KEY or FLUXBASE_PROJECT_ID in environment")
    headers = {
        'Authorization': f'Bearer {FLUXBASE_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {'projectId': FLUXBASE_PROJECT_ID, 'query': query}
    resp = requests.post(FLUXBASE_URL, json=payload, headers=headers)
    data = resp.json()
    if not data.get('success'):
        error_msg = data.get('error', {}).get('message', 'Fluxbase execution failed')
        raise Exception(f"Fluxbase error: {error_msg}")
    return data.get('result', {})

FLUXBASE_BASE_URL = os.environ.get('FLUXBASE_BASE_URL', 'https://fluxbasedb.me')
FLUXBASE_AI_BASE_URL = os.environ.get('FLUXBASE_AI_BASE_URL', f"{FLUXBASE_BASE_URL}/api/v1")

def get_fluxbase_ai_client():
    from openai import OpenAI
    key = FLUXBASE_API_KEY or os.environ.get('FLUXBASE_API_KEY')
    if not key:
        raise ValueError("Missing FLUXBASE_API_KEY in environment")
    return OpenAI(base_url=FLUXBASE_AI_BASE_URL, api_key=key)

# Flask Config class removed — FastAPI reads SECRET_KEY directly from os.environ in app.py
