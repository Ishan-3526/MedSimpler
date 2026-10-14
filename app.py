"""
MedSimpler - FastAPI backend.

The Streamlit UI has been replaced by a plain HTML/CSS/JS front-end (see /static).
All analysis logic still lives untouched in reports/*.py - this file only
receives the upload, picks the right analyser, and returns the result as JSON.
"""
import logging
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from reports import (
    CT_SCAN,
    MRI_reports,
    Medical_prescription as prescription,
    X_ray_report,
    blood_report,
    other,
    ultrasound,
)

log = logging.getLogger("medsimpler")
BASE_DIR = Path(__file__).resolve().parent

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB

# extension -> mime type (browsers sometimes send application/octet-stream)
ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

DIFFICULTIES = ["Ekdam Basic", "Intermidiate", "Advance"]
LANGUAGES = ["English", "Marathi", "Hindi"]

# document type -> analyser. Each analyser has the signature
# analyse(file, doc_type, level, language) exactly as before.
ANALYSERS = {
    "Medicine Prescription": prescription.analyse,
    "Blood Report": blood_report.analyse,
    "Lab Report": blood_report.analyse,
    "Ultrasound Report": ultrasound.analyse,
    "X-Ray Report": X_ray_report.analyse,
    "CT Scan Report": CT_SCAN.analyse,
    "MRI Report": MRI_reports.analyse,
    "Other": other.analyse,
}


class UploadedFileAdapter:
    """
    The analysers were written for Streamlit's UploadedFile, which exposes
    `.type` and `.getvalue()`. This tiny wrapper provides the same two things
    so the analyser code does not need to change.
    """

    def __init__(self, data: bytes, mime_type: str, name: str):
        self._data = data
        self.type = mime_type
        self.name = name

    def getvalue(self) -> bytes:
        return self._data


app = FastAPI(title="MedSimpler", docs_url=None, redoc_url=None)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/options")
def options():
    return {
        "doc_types": list(ANALYSERS.keys()),
        "difficulties": DIFFICULTIES,
        "languages": LANGUAGES,
    }


@app.post("/api/analyse")
def analyse(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    difficulty: str = Form(...),
    language: str = Form(...),
):
    if doc_type not in ANALYSERS:
        raise HTTPException(400, "Please choose a valid report type.")
    if difficulty not in DIFFICULTIES:
        raise HTTPException(400, "Please choose a valid explanation level.")
    if language not in LANGUAGES:
        raise HTTPException(400, "Please choose a valid language.")

    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(400, "Unsupported file type. Upload a PDF, PNG, JPG or WEBP.")

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is too large. Please upload a file under 15 MB.")

    adapted = UploadedFileAdapter(data, ALLOWED_TYPES[ext], filename)

    try:
        result = ANALYSERS[doc_type](adapted, doc_type, difficulty, language)
    except Exception:
        log.exception("Analysis failed for doc_type=%s", doc_type)
        raise HTTPException(
            502,
            "Gemini could not process this file right now. Please try again in a moment.",
        )

    if result is None:
        raise HTTPException(
            502,
            "The report could not be read clearly. Try a sharper photo or the original PDF.",
        )

    return {
        "doc_type": doc_type,
        "difficulty": difficulty,
        "language": language,
        "filename": filename,
        "result": result.model_dump(),
    }


# Front-end (must be mounted last so it doesn't shadow the API routes)
app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
