# MedRisk — Medical Lab Report Analyser

AI-powered web app that analyses medical lab reports (blood tests, echo cardiograms, diagnostics) and predicts risk level with plain-language explanations.

---

## Project Structure

```
medical-risk-app/
├── backend/
│   ├── main.py           # FastAPI backend
│   ├── requirements.txt  # Python dependencies
│   └── Procfile          # For Render deployment
└── frontend/
    └── index.html        # Full frontend (single file)
```

---

## Local Setup

### 1. Get your Anthropic API key
- Go to https://console.anthropic.com
- Create an account → API Keys → Create Key
- Copy the key

### 2. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Set your API key
**Mac/Linux:**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```
**Windows (Command Prompt):**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Run the app
```bash
cd backend
uvicorn main:app --reload
```

### 5. Open in browser
Visit: http://localhost:8000

---

## Deploy to Render (free hosting)

1. Push this project to a GitHub repository
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Set these settings:
   - **Root directory:** `backend`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable:
   - Key: `ANTHROPIC_API_KEY`
   - Value: your API key
6. Click **Deploy** — your app will be live at a public URL

---

## How it works

1. User uploads a PDF or image of their lab report
2. Frontend sends it to the FastAPI backend via `/analyse`
3. Backend encodes the file and sends it to Claude (claude-sonnet-4-20250514)
4. Claude extracts test values, flags abnormals, predicts risk level
5. Structured JSON is returned and rendered as a results dashboard

---

## Features
- Supports PDF, JPG, PNG lab reports
- Risk level: Low / Medium / High
- Per-test findings with normal ranges and status
- Plain-language explanation
- Suggested next steps
- Files are never stored — processed in memory only

---

## Disclaimer
This app is for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment.
