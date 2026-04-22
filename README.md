# 🌱 SuperFarmer — AI Agricultural Intelligence Platform

> A multi-agent AI system built for Indian farmers. Combines **Gemini 2.5 Flash**, **Groq (LLaMA 3.3)**, **Tomorrow.io**, and **Fluxbase** cloud database to deliver hyper-local, multilingual farming intelligence.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Database Initialization](#database-initialization)
- [Agent System](#agent-system)
- [API Routes](#api-routes)
- [MCP Server](#mcp-server)

---

## Overview

SuperFarmer is a full-stack web application that acts as an AI-powered agricultural advisor for Indian farmers. It uses a **multi-agent orchestration** pattern where specialized AI agents handle distinct domains — weather, disease diagnosis, crop planning, spatial layout, yield comparison, and conversational Q&A.

The backend is built on **FastAPI** and uses **Fluxbase** (cloud MySQL via REST API) as the database, replacing traditional local MySQL. All LLM calls go through **Google Gemini 2.5 Flash** with **Groq (LLaMA 3.3-70B)** as a secondary model for crop recommendations and planning.

---

## Features

| Feature | Description |
|---|---|
| 🔐 **Auth** | Signup / Login with Werkzeug password hashing + session cookies. Welcome & login alert emails sent automatically. |
| 🌾 **Crop Recommendation** | LLaMA 3.3-70B (via Groq) analyzes soil NPK, temperature, rainfall, and water availability to recommend top 3 crops. Falls back to a rule-based engine if API is unavailable. |
| 📅 **Crop Planner** | Generates a full crop management plan (sowing, irrigation, fertilizers, pest alerts, harvest timeline) using Groq. |
| 🤒 **Disease Diagnosis** | Gemini 2.5 Flash diagnoses plant diseases from text descriptions **and uploaded leaf images**. Returns treatment + direct purchase links (BigHaat, IFFCO, Amazon). |
| 🌦️ **Weather Analysis** | 3-day hyper-local forecast via Tomorrow.io. Auto-geocodes locations via Nominatim. Gives actionable harvest/irrigation advice. |
| 🗺️ **Spatial Planner (Digital Twin)** | Gemini generates a **personalized 2D hexagonal field layout** based on the farmer's soil, water, and location profile from the database. |
| 📊 **Yield Comparison** | Rule-based engine compares optimized intercropping yield vs. normal monoculture yield in tons/acre with ₹ income delta. |
| 💬 **AI Chat** | Multilingual conversational agent (10 Indian languages) powered by Gemini. Adapts tone to village-level vocabulary. |
| 📄 **Report Generator** | Pulls farmer profile + latest crop plan from Fluxbase and generates a structured advisory report. |
| 📧 **Email Automation** | Gmail SMTP sends welcome emails on signup and security alerts on login — asynchronously in background threads. |
| 🔌 **MCP Server** | A FastMCP stdio server (`farmer_mcp_server.py`) exposes farmer profile data as a tool for AI agent pipelines. |

---

## Architecture

```
Browser
  │
  ▼
FastAPI (app.py)
  │
  ├── OrchestratorAgent ──► routes intent to the right agent
  │
  ├── UserAuthAgent        ──► Fluxbase (users table)
  ├── IntakeAgent          ──► Fluxbase (farmer_profile table)
  ├── CropRecommendationAgent ──► Groq LLaMA 3.3-70B → Fluxbase
  ├── CropPlannerAgent     ──► Groq LLaMA 3.3-70B → Fluxbase
  ├── DiseaseDiagnosisAgent──► Gemini 2.5 Flash (text + image)
  ├── WeatherAgent         ──► Tomorrow.io REST API
  ├── SpatialPlannerAgent  ──► Gemini 2.5 Flash (JSON layout)
  ├── YieldComparisonAgent ──► Rule-based engine
  ├── SuperFarmerChatAgent ──► Gemini 2.5 Flash (multilingual)
  ├── ReportAgent          ──► Fluxbase (reads + writes)
  └── EmailAgent           ──► Gmail SMTP (async thread)

Fluxbase Cloud DB (MySQL via REST API)
  └── POST https://fluxbase.vercel.app/api/execute-sql
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Frontend** | Jinja2 templates, HTML/CSS/JS |
| **Primary LLM** | Google Gemini 2.5 Flash |
| **Secondary LLM** | Groq API — LLaMA 3.3-70B-Versatile |
| **Database** | Fluxbase (cloud MySQL, accessed via REST) |
| **Weather API** | Tomorrow.io v4 |
| **Geocoding** | OpenStreetMap Nominatim |
| **Auth** | Werkzeug password hashing, Starlette SessionMiddleware |
| **Email** | Gmail SMTP (smtplib) |
| **ML (opt.)** | scikit-learn, joblib, numpy |
| **MCP** | FastMCP (stdio transport) |

---

## Project Structure

```
superfarmer/
├── app.py                   # FastAPI app — all routes
├── config.py                # Fluxbase connection + execute_fluxbase_sql()
├── requirements.txt         # Python dependencies
├── farmer_mcp_server.py     # FastMCP server (AI tool interface)
├── .env                     # API keys (not committed)
│
├── agents/
│   └── agents.py            # All agent classes + OrchestratorAgent
│
├── database/
│   └── init_db.py           # Creates all tables in Fluxbase
│
├── ml/                      # (Optional) ML model training scripts
│
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   ├── intake.html
│   ├── recommendation.html
│   ├── plan.html
│   ├── disease.html
│   ├── chat.html
│   ├── weather.html
│   ├── spatial_planner.html
│   ├── yield_comparison.html
│   └── report.html
│
└── static/
    └── css/
        └── style.css
```

---

## Setup & Installation

### 1. Clone / Download

```bash
cd C:\Users\hariv\Downloads\superfarmer
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **requirements.txt** includes: `fastapi`, `uvicorn[standard]`, `python-multipart`, `starlette`, `itsdangerous`, `werkzeug`, `scikit-learn`, `pandas`, `numpy`, `joblib`, `requests`, `python-dotenv`, `google-generativeai`, `Pillow`, `transformers`, `torch`

---

## Environment Variables

Create a `.env` file in the project root:

```env
# AI APIs
GEMINI_API_KEY=your_google_gemini_api_key
GROK_API_KEY=your_groq_api_key

# Weather
TOMORROW_API_KEY=your_tomorrow_io_api_key

# Fluxbase (cloud DB)
FLUXBASE_API_KEY=your_fluxbase_api_key
FLUXBASE_PROJECT_ID=your_fluxbase_project_id

# Email (Gmail)
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password

# Flask/FastAPI Session
SECRET_KEY=your_secret_key_here
```

### Getting your credentials

| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) |
| `GROK_API_KEY` | [GroqCloud Console](https://console.groq.com/) |
| `TOMORROW_API_KEY` | [Tomorrow.io](https://tomorrow.io/) |
| `FLUXBASE_API_KEY` | [Fluxbase Dashboard](https://fluxbase.vercel.app) → Your Project → Settings → API Keys |
| `FLUXBASE_PROJECT_ID` | Fluxbase Dashboard → Your Project → Settings → Project ID |
| `EMAIL_PASSWORD` | Gmail → Security → App Passwords (generate one for "Mail") |

---

## Database Initialization

Run this **once** to create all tables in your Fluxbase project:

```bash
python database/init_db.py
```

This creates the following tables:

| Table | Purpose |
|---|---|
| `users` | Auth — email + hashed password |
| `farmer_profile` | Farmer name, land size, location, water availability, goals |
| `soil_records` | Historical NPK/moisture sensor readings |
| `crop_recommendations` | AI-generated crop suggestions per farmer |
| `crop_plans` | Full sowing/irrigation/fertilizer/harvest plans |
| `nutrient_risk_log` | ML risk predictions and suggested actions |
| `reports` | Generated advisory reports |
| `session_logs` | Interaction history |

---

## Running the App

```bash
python app.py
```

The server starts at **http://127.0.0.1:5000** with hot-reload enabled.

Alternatively with uvicorn directly:

```bash
uvicorn app:app --host 127.0.0.1 --port 5000 --reload
```

---

## Agent System

All agents live in `agents/agents.py` and are dispatched by `OrchestratorAgent.route_request(intent, data)`.

### Agent Reference

| Agent Class | Intent Key | Description |
|---|---|---|
| `UserAuthAgent` | `signup`, `login` | Hashed password auth via Fluxbase |
| `IntakeAgent` | `intake` | Saves new farmer profile to Fluxbase |
| `CropRecommendationAgent` | `recommendation` | Groq LLaMA → rule fallback → top 3 crops |
| `CropPlannerAgent` | `plan` | Groq LLaMA JSON plan → fallback defaults |
| `DiseaseDiagnosisAgent` | `diagnose` | Gemini vision (text + leaf image) |
| `WeatherAgent` | `weather` | Tomorrow.io 3-day forecast + advice |
| `SpatialPlannerAgent` | `spatial_plan` | Gemini JSON hexagonal layout + MCP |
| `YieldComparisonAgent` | `yield_comparison` | Rule-based tons/acre delta calculation |
| `SuperFarmerChatAgent` | `chat` | Gemini multilingual conversational agent |
| `ReportAgent` | `report` | Fluxbase data → structured advisory text |
| `EmailAgent` | `send_email` | Gmail SMTP HTML email delivery |

---

## API Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Home page |
| `GET/POST` | `/signup` | User registration |
| `GET/POST` | `/login` | User login |
| `GET` | `/logout` | Clear session |
| `GET/POST` | `/intake` | Farmer profile setup |
| `GET/POST` | `/recommendation` | Crop recommendation form |
| `GET/POST` | `/plan` | Crop plan generator |
| `GET/POST` | `/disease` | Disease diagnosis (text + image upload) |
| `GET/POST` | `/chat` | JSON API for AI chat |
| `GET/POST` | `/weather` | Weather forecast |
| `GET/POST` | `/spatial-planner` | Digital twin field layout (JSON API) |
| `GET/POST` | `/yield-comparison` | Yield comparison report |
| `GET` | `/report` | Generate advisory report |

---

## MCP Server

`farmer_mcp_server.py` exposes an **MCP (Model Context Protocol)** tool over stdio. It lets external AI agents fetch farmer profile data directly from Fluxbase.

```bash
python farmer_mcp_server.py
```

**Available tool:**

```python
get_farmer_profile(farmer_id: int) -> str
# Returns JSON of farmer's name, land_size, location, water_availability, farming_goals
```

This is used internally by `SpatialPlannerAgent` to give Gemini real farmer context when generating personalized field layouts.

---

## Notes

- **No local MySQL required** — the app uses Fluxbase cloud DB via REST API (`POST /api/execute-sql`).
- **Rate limit** — Fluxbase allows 30 requests/10 seconds per project; SELECT queries are cached for 15 seconds.
- The Groq API key env variable is `GROK_API_KEY` (note: no 'Q' in env name, check `.env` accordingly).
- If Groq is unavailable, both `CropRecommendationAgent` and `CropPlannerAgent` fall back to deterministic rule-based logic automatically.
- If Gemini is unavailable for `SpatialPlannerAgent`, a classic hexagonal grid is generated instead.

---

*© 2026 SuperFarmer. Built for Indian farmers 🇮🇳*
