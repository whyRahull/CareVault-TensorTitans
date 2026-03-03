"""
schemas.py — Centralised Pydantic models for CareVault ML Service
"""
from typing import List, Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Severity Prediction
# ---------------------------------------------------------------------------
class SeverityRequest(BaseModel):
    description: str


class SeverityResponse(BaseModel):
    severity: str
    description: str


# ---------------------------------------------------------------------------
# Violence Detection
# ---------------------------------------------------------------------------
class ViolenceResponse(BaseModel):
    suspicious_detected: bool
    frame_count: int
    suspicious_frame_count: int
    thumbnail_b64: Optional[str] = None
    message: str


# ---------------------------------------------------------------------------
# Hand SOS
# ---------------------------------------------------------------------------
class HandSOSResponse(BaseModel):
    gesture: str
    hand_sign_id: int
    sos_detected: bool
    hands_found: int
    annotated_image_b64: Optional[str] = None


# ---------------------------------------------------------------------------
# SOS Alert  (payload only — email sent by Django)
# ---------------------------------------------------------------------------
class SOSResponse(BaseModel):
    subject: str
    recipients: List[str]
    body: str
    image_filename: Optional[str] = None



# ---------------------------------------------------------------------------
# Lost Child Search
# ---------------------------------------------------------------------------
class LostChildResponse(BaseModel):
    status: str
    message: str
    matched: bool = False
    confidence: float = 0.0
    person_id: Optional[int] = None
    annotated_image_b64: Optional[str] = None
