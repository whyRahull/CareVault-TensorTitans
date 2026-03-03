"""
Hand SOS Router
POST /api/hand_sos/detect — upload an image, detect hand gesture and SOS signal.

Requires HandSOS model files in ml_service/models/keypoint_classifier/:
  keypoint_classifier.tflite
  keypoint_classifier_label.csv
"""
import base64
import copy
import csv
import itertools
import tempfile
import os
from pathlib import Path
from typing import Optional

import cv2 as cv
import numpy as np
import mediapipe as mp
from fastapi import APIRouter, File, HTTPException, UploadFile
from schemas import HandSOSResponse

router = APIRouter()

_BASE_DIR = Path(__file__).resolve().parent.parent / "models"
_KP_MODEL_DIR = _BASE_DIR / "keypoint_classifier"
_KP_LABELS_CSV = _KP_MODEL_DIR / "keypoint_classifier_label.csv"

# Lazy globals
_mp_hands = None
_keypoint_classifier = None
_keypoint_labels: list[str] = []
_models_loaded = False


def _load_models() -> bool:
    global _mp_hands, _keypoint_classifier, _keypoint_labels, _models_loaded
    if _models_loaded:
        return True
    if not _KP_LABELS_CSV.exists():
        return False
    try:
        # Import HandSOS model wrapper — we inline a minimal TFLite classifier
        # rather than depending on the HandSOS directory being on sys.path
        import tensorflow as tf  # noqa: F401 — tflite is bundled with mediapipe
    except ImportError:
        pass

    try:
        _mp_hands = mp.solutions.hands
        with open(_KP_LABELS_CSV, encoding="utf-8-sig") as f:
            _keypoint_labels = [row[0] for row in csv.reader(f)]
        _keypoint_classifier = _KeyPointClassifier(str(_KP_MODEL_DIR / "keypoint_classifier.tflite"))
        _models_loaded = True
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Minimal inline TFLite KeyPoint Classifier (mirrors HandSOS/model/keypoint_classifier/)
# ---------------------------------------------------------------------------
class _KeyPointClassifier:
    def __init__(self, model_path: str):
        import mediapipe as mp  # mediapipe ships with a TFLite runtime

        # Use mediapipe's bundled TFLite interpreter
        try:
            from mediapipe.tasks.python.core.base_options import BaseOptions
        except ImportError:
            pass

        # Fallback: use the standard tflite_runtime if available
        try:
            import tflite_runtime.interpreter as tflite
            self._interpreter = tflite.Interpreter(model_path=model_path)
        except ImportError:
            # Use TensorFlow Lite from TF
            import tensorflow as tf
            self._interpreter = tf.lite.Interpreter(model_path=model_path)

        self._interpreter.allocate_tensors()
        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()

    def __call__(self, landmark_list: list) -> int:
        input_details = self._input_details
        input_data = np.array([landmark_list], dtype=np.float32)
        self._interpreter.set_tensor(input_details[0]["index"], input_data)
        self._interpreter.invoke()
        output_data = self._interpreter.get_tensor(self._output_details[0]["index"])
        return int(np.argmax(np.squeeze(output_data)))


# ---------------------------------------------------------------------------
# Landmark helpers (ported from HandSOS/app.py)
# ---------------------------------------------------------------------------
def _calc_landmark_list(image: np.ndarray, landmarks) -> list:
    h, w = image.shape[:2]
    return [
        [min(int(lm.x * w), w - 1), min(int(lm.y * h), h - 1)]
        for lm in landmarks.landmark
    ]


def _pre_process_landmark(landmark_list: list) -> list:
    temp = copy.deepcopy(landmark_list)
    base_x, base_y = temp[0]
    for pt in temp:
        pt[0] -= base_x
        pt[1] -= base_y
    flat = list(itertools.chain.from_iterable(temp))
    max_val = max(map(abs, flat)) or 1
    return [v / max_val for v in flat]



# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/detect",
    response_model=HandSOSResponse,
    summary="Detect hand SOS gesture in an image",
)
async def detect_hand_sos(
    file: UploadFile = File(..., description="Image file (.jpg, .png, etc.)"),
):
    """
    Runs MediaPipe Hands on the uploaded image and classifies hand gestures
    using the KeyPointClassifier.  Returns `sos_detected=true` when a **Help**
    gesture is recognised.
    """
    if not _load_models():
        raise HTTPException(
            status_code=503,
            detail=(
                "Hand SOS models not found. Copy the keypoint_classifier/ folder "
                "from HandSOS/model/ into ml_service/models/."
            ),
        )

    # Decode uploaded image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image_bgr = cv.imdecode(nparr, cv.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="Could not decode the uploaded image.")

    image_rgb = cv.cvtColor(image_bgr, cv.COLOR_BGR2RGB)
    debug_image = copy.deepcopy(image_bgr)

    with _mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=2,
        min_detection_confidence=0.7,
    ) as hands:
        results = hands.process(image_rgb)

    gesture = "none"
    hand_sign_id = -1
    sos_detected = False
    hands_found = 0

    if results.multi_hand_landmarks:
        hands_found = len(results.multi_hand_landmarks)
        # Process the first detected hand
        hand_landmarks = results.multi_hand_landmarks[0]
        landmark_list = _calc_landmark_list(debug_image, hand_landmarks)
        processed = _pre_process_landmark(landmark_list)
        hand_sign_id = _keypoint_classifier(processed)
        gesture = _keypoint_labels[hand_sign_id] if hand_sign_id < len(_keypoint_labels) else "unknown"
        sos_detected = gesture.strip().lower() == "help"

        # Draw landmarks on debug image
        mp.solutions.drawing_utils.draw_landmarks(
            debug_image,
            hand_landmarks,
            _mp_hands.HAND_CONNECTIONS,
        )

    # Encode annotated image to base64
    ret, buf = cv.imencode(".jpg", debug_image)
    annotated_b64 = base64.b64encode(buf.tobytes()).decode("utf-8") if ret else None

    return HandSOSResponse(
        gesture=gesture,
        hand_sign_id=hand_sign_id,
        sos_detected=sos_detected,
        hands_found=hands_found,
        annotated_image_b64=annotated_b64,
    )
