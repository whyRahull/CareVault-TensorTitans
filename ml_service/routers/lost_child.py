"""
Lost Child Search Router
POST /api/lost_child/search

Accepts a live camera frame + an optional ?person_id=<N> query parameter.
If person_id is given, it fetches the reference photo from Django's
/api/incidents/missing-persons/<pk>/photo-bytes/ endpoint and performs
face matching using OpenCV's LBPH face recognizer.

Returns:
  matched        — True if a face match was found
  confidence     — LBPH confidence score (lower = more similar; < 100 = match)
  person_id      — echoed back
  annotated_image_b64 — JPEG with face rectangles drawn
"""
import base64
import os
from pathlib import Path
from typing import Optional

import cv2
import httpx
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi import Query as QueryParam

from schemas import LostChildResponse

router = APIRouter()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Where Django core_api is reachable from the ML service (Docker network / local)
_DJANGO_BASE_URL = os.environ.get("DJANGO_BASE_URL", "http://localhost:8000")

# LBPH confidence threshold — distances below this are considered a match
_MATCH_THRESHOLD = 80.0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_reference_photo(person_id: int) -> Optional[np.ndarray]:
    """
    Download the reference photo for a MissingPerson from Django.
    Returns a grayscale numpy array or None on failure.
    """
    url = f"{_DJANGO_BASE_URL}/api/incidents/missing-persons/{person_id}/photo-bytes/"
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
        nparr = np.frombuffer(resp.content, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        return img
    except Exception:
        return None


def _detect_faces(gray: np.ndarray):
    """Return list of (x, y, w, h) face rectangles using Haar cascade."""
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade      = cv2.CascadeClassifier(cascade_path)
    faces        = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40),
    )
    if not isinstance(faces, np.ndarray) or len(faces) == 0:
        return []
    return faces.tolist()


def _match_faces(reference_gray: np.ndarray, probe_gray: np.ndarray, probe_faces: list):
    """
    Train LBPH on the single reference face, then predict against every
    face in the probe frame.  Returns (best_confidence, best_face_rect).
    """
    # Detect face in reference image
    ref_faces = _detect_faces(reference_gray)
    if not ref_faces:
        # No face found in reference — fall back to whole-image match
        ref_face_img = cv2.resize(reference_gray, (100, 100))
    else:
        x, y, w, h = ref_faces[0]
        ref_face_img = cv2.resize(reference_gray[y:y+h, x:x+w], (100, 100))

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train([ref_face_img], np.array([0]))

    best_confidence = float('inf')
    best_face       = None

    for (fx, fy, fw, fh) in probe_faces:
        face_roi = cv2.resize(probe_gray[fy:fy+fh, fx:fx+fw], (100, 100))
        label, confidence = recognizer.predict(face_roi)
        if confidence < best_confidence:
            best_confidence = confidence
            best_face       = (fx, fy, fw, fh)

    return best_confidence, best_face


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/search",
    response_model=LostChildResponse,
    summary="Search for a missing person in a camera frame",
)
async def search_lost_child(
    file:      UploadFile = File(..., description="Live camera frame (JPEG/PNG)"),
    person_id: Optional[int] = QueryParam(None, description="MissingPerson PK to match against"),
):
    """
    Analyses a live frame for faces and, when ``person_id`` is supplied, attempts
    to match against the registered reference photo using LBPH face recognition.

    - ``matched=True`` when LBPH confidence < 80 (lower = more similar).
    - Without ``person_id``: returns face count only, ``matched`` always ``False``.
    """
    contents = await file.read()
    nparr    = np.frombuffer(contents, np.uint8)
    frame    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode the uploaded image.")

    gray       = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    probe_faces = _detect_faces(gray)
    annotated  = frame.copy()

    # Draw all detected faces in blue
    for (fx, fy, fw, fh) in probe_faces:
        cv2.rectangle(annotated, (fx, fy), (fx+fw, fy+fh), (255, 128, 0), 2)

    if not probe_faces:
        b64_img = _encode_b64(annotated)
        return LostChildResponse(
            status="no_faces",
            message="No faces detected in the frame.",
            matched=False,
            annotated_image_b64=b64_img,
        )

    if person_id is None:
        b64_img = _encode_b64(annotated)
        return LostChildResponse(
            status="no_person_id",
            message=f"{len(probe_faces)} face(s) detected. Provide person_id to attempt matching.",
            matched=False,
            annotated_image_b64=b64_img,
        )

    # Fetch reference photo
    reference_gray = _fetch_reference_photo(person_id)
    if reference_gray is None:
        raise HTTPException(
            status_code=503,
            detail=f"Could not fetch reference photo for person_id={person_id} from Django.",
        )

    # Face matching
    confidence, best_face = _match_faces(reference_gray, gray, probe_faces)
    matched = confidence < _MATCH_THRESHOLD

    # Highlight matched face in green / red
    if best_face:
        fx, fy, fw, fh = best_face
        color  = (0, 255, 0) if matched else (0, 0, 255)
        label  = f"Match ({confidence:.1f})" if matched else f"No match ({confidence:.1f})"
        cv2.rectangle(annotated, (fx, fy), (fx+fw, fy+fh), color, 3)
        cv2.putText(annotated, label, (fx, fy - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    b64_img = _encode_b64(annotated)

    return LostChildResponse(
        status="match" if matched else "no_match",
        message=(
            f"Face match found with confidence {confidence:.1f}."
            if matched else
            f"No match. Best confidence: {confidence:.1f} (threshold: {_MATCH_THRESHOLD})."
        ),
        matched=matched,
        confidence=round(confidence, 2),
        person_id=person_id,
        annotated_image_b64=b64_img,
    )


def _encode_b64(img: np.ndarray) -> Optional[str]:
    ret, buf = cv2.imencode(".jpg", img)
    return base64.b64encode(buf.tobytes()).decode("utf-8") if ret else None
