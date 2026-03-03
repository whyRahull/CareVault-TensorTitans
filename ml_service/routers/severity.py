"""
Severity Prediction Router
POST /api/severity/predict — predicts incident severity from a text description.
Model: TF-IDF vectorizer + sklearn classifier (pkl files).
"""
import pickle
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from schemas import SeverityRequest, SeverityResponse

router = APIRouter()

# ---------------------------------------------------------------------------
# Model loading (done once at import time)
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parent.parent / "models"

try:
    with open(_BASE_DIR / "incident_severity_model.pkl", "rb") as f:
        _model = pickle.load(f)
    with open(_BASE_DIR / "tfidf_vectorizer.pkl", "rb") as f:
        _vectorizer = pickle.load(f)
    _models_loaded = True
except FileNotFoundError:
    _model = None
    _vectorizer = None
    _models_loaded = False



# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("/predict", response_model=SeverityResponse, summary="Predict incident severity")
async def predict_severity(body: SeverityRequest):
    """
    Accepts an incident description and returns the predicted severity level
    (e.g. *High*, *Medium*, *Low*).
    """
    if not _models_loaded:
        raise HTTPException(
            status_code=503,
            detail="Severity model files not found. Copy incident_severity_model.pkl "
                   "and tfidf_vectorizer.pkl into ml_service/models/.",
        )

    description = body.description.strip()
    if not description:
        raise HTTPException(status_code=422, detail="description must not be empty.")

    features = _vectorizer.transform([description])
    prediction = _model.predict(features)[0]

    return SeverityResponse(severity=str(prediction), description=description)
