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

# Flask Config class removed — FastAPI reads SECRET_KEY directly from os.environ in app.py
