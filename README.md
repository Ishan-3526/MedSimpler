# MedSimpler

Upload a medical report (PDF / image) and get a clear, structured explanation in
English, Hindi or Marathi, powered by Google Gemini.

## Project layout

```
app.py              FastAPI backend (replaces the Streamlit UI)
gemini_client.py    Gemini client (unchanged)
reports/            One analyser per document type (logic unchanged)
static/             index.html, style.css, app.js  (the new UI)
requirements.txt    Python dependencies
render.yaml         Render deployment blueprint
```

## Run locally

```bash
pip install -r requirements.txt
echo "GOOGLE_API_KEY=your_key_here" > .env
uvicorn app:app --reload
# open http://localhost:8000
```

## Deploy on Render

1. Push this folder to GitHub (the repo root must contain `app.py`).
2. Render dashboard -> New + -> Blueprint -> pick the repo (uses `render.yaml`),
   or New + -> Web Service with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - Health check path: `/health`
3. Add the environment variable GOOGLE_API_KEY with your Gemini key.
4. Deploy. Free instances sleep after ~15 min idle, so the first request can take ~30-60 s.
