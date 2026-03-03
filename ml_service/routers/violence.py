"""
Violence Detection Router
POST /api/violence/detect — upload a video, get back YOLO+XGBoost violence analysis.
"""
import base64
import os
import tempfile
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from schemas import ViolenceResponse

router = APIRouter()

_BASE_DIR = Path(__file__).resolve().parent.parent / "models"
_YOLO_MODEL_PATH = _BASE_DIR / "yolo11s-pose.pt"
_XGB_MODEL_PATH = _BASE_DIR / "trained_model.json"

# Lazy-loaded globals
_yolo = None
_xgb_model = None
_models_loaded = False


def _load_models():
    global _yolo, _xgb_model, _models_loaded
    if _models_loaded:
        return True
    if not _YOLO_MODEL_PATH.exists() or not _XGB_MODEL_PATH.exists():
        return False
    try:
        from ultralytics import YOLO
        import xgboost as xgb

        _yolo = YOLO(str(_YOLO_MODEL_PATH))
        _xgb_model = xgb.Booster()
        _xgb_model.load_model(str(_XGB_MODEL_PATH))
        _models_loaded = True
        return True
    except Exception:
        return False



# ---------------------------------------------------------------------------
# Endpoint 1 — Video file (uploaded via REST or front-end form)
# ---------------------------------------------------------------------------
@router.post(
    "/detect",
    response_model=ViolenceResponse,
    summary="Detect suspicious/violent activity in a video file",
)
async def detect_violence(
    file: UploadFile = File(..., description="Video file to analyse (.mp4, .avi, etc.)"),
):
    """
    Runs YOLO11s-pose pose estimation on every 3rd frame of a full video,
    then passes keypoints through an XGBoost classifier.
    Returns a summary + base64-encoded JPEG thumbnail of the most suspicious frame.
    """
    if not _load_models():
        raise HTTPException(
            status_code=503,
            detail=(
                "Violence detection models not found. "
                "Copy yolo11s-pose.pt and trained_model.json into ml_service/models/."
            ),
        )

    import xgboost as xgb
    import pandas as pd
    import cvzone

    # Save upload to a temp file so OpenCV can read it
    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    cap = cv2.VideoCapture(tmp_path)
    if not cap.isOpened():
        os.unlink(tmp_path)
        raise HTTPException(status_code=400, detail="Could not open uploaded video file.")

    frame_count = 0
    suspicious_frame_count = 0
    thumbnail: Optional[np.ndarray] = None
    count = 0

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            frame_count += 1
            count += 1
            if count % 3 != 0:
                continue

            results = _yolo(frame, verbose=False)
            annotated_frame = results[0].plot(boxes=False)
            annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
            annotated_frame = np.uint8(annotated_frame)

            suspicious_in_frame = False
            for r in results:
                bound_box = r.boxes.xyxy
                conf = r.boxes.conf.tolist()
                keypoints = r.keypoints.xyn.tolist()

                for index, box in enumerate(bound_box):
                    if conf[index] < 0.55:
                        continue
                    x1, y1, x2, y2 = box.tolist()
                    data = {f"x{j}": keypoints[index][j][0] for j in range(len(keypoints[index]))}
                    data.update({f"y{j}": keypoints[index][j][1] for j in range(len(keypoints[index]))})
                    df = pd.DataFrame(data, index=[0])
                    dmatrix = xgb.DMatrix(df)
                    sus = _xgb_model.predict(dmatrix)
                    binary_pred = (sus > 0.5).astype(int)

                    if binary_pred == 0:  # suspicious
                        suspicious_in_frame = True
                        cv2.rectangle(
                            annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2
                        )
                        cvzone.putTextRect(
                            annotated_frame, "Suspicious", (int(x1), int(y1)), scale=1, thickness=1
                        )
                    else:
                        cv2.rectangle(
                            annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2
                        )

            if suspicious_in_frame:
                suspicious_frame_count += 1
                if thumbnail is None:
                    thumbnail = annotated_frame.copy()

    finally:
        cap.release()
        os.unlink(tmp_path)

    thumbnail_b64 = None
    if thumbnail is not None:
        ret, buf = cv2.imencode(".jpg", thumbnail)
        if ret:
            thumbnail_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

    suspicious_detected = suspicious_frame_count > 0
    return ViolenceResponse(
        suspicious_detected=suspicious_detected,
        frame_count=frame_count,
        suspicious_frame_count=suspicious_frame_count,
        thumbnail_b64=thumbnail_b64,
        message=(
            f"Suspicious activity detected in {suspicious_frame_count}/{frame_count} frames."
            if suspicious_detected
            else f"No suspicious activity detected across {frame_count} frames."
        ),
    )


# ---------------------------------------------------------------------------
# Endpoint 2 — Single image frame (used by WebSocket Django Channels consumer)
# ---------------------------------------------------------------------------
@router.post(
    "/detect_frame",
    response_model=ViolenceResponse,
    summary="Detect suspicious activity in a single JPEG frame (WebSocket / real-time use)",
)
async def detect_violence_frame(
    file: UploadFile = File(..., description="Single JPEG/PNG frame from a live camera stream"),
):
    """
    Runs YOLO11s-pose + XGBoost on a **single image frame**.
    Intended for real-time use via the Django Channels WebSocket consumer which
    sends one frame at a time decoded from the browser's WebRTC stream.

    frame_count will always be 1; suspicious_frame_count is 0 or 1.
    """
    if not _load_models():
        raise HTTPException(status_code=503, detail="Violence detection models not loaded.")

    import xgboost as xgb
    import pandas as pd
    import cvzone

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode the uploaded image frame.")

    results = _yolo(frame, verbose=False)
    annotated_frame = results[0].plot(boxes=False)
    annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
    annotated_frame = np.uint8(annotated_frame)

    suspicious_in_frame = False
    for r in results:
        bound_box = r.boxes.xyxy
        conf = r.boxes.conf.tolist()
        keypoints = r.keypoints.xyn.tolist()

        for index, box in enumerate(bound_box):
            if conf[index] < 0.55:
                continue
            x1, y1, x2, y2 = box.tolist()
            data = {f"x{j}": keypoints[index][j][0] for j in range(len(keypoints[index]))}
            data.update({f"y{j}": keypoints[index][j][1] for j in range(len(keypoints[index]))})
            df = pd.DataFrame(data, index=[0])
            dmatrix = xgb.DMatrix(df)
            sus = _xgb_model.predict(dmatrix)
            binary_pred = (sus > 0.5).astype(int)

            if binary_pred == 0:
                suspicious_in_frame = True
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                cvzone.putTextRect(annotated_frame, "Suspicious", (int(x1), int(y1)), scale=1, thickness=1)
            else:
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

    thumbnail_b64 = None
    ret, buf = cv2.imencode(".jpg", annotated_frame)
    if ret:
        thumbnail_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

    return ViolenceResponse(
        suspicious_detected=suspicious_in_frame,
        frame_count=1,
        suspicious_frame_count=1 if suspicious_in_frame else 0,
        thumbnail_b64=thumbnail_b64,
        message="Suspicious activity detected." if suspicious_in_frame else "No suspicious activity.",
    )
