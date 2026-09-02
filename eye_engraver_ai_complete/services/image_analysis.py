from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

try:
    import mediapipe as mp
except Exception:
    mp = None


LEFT_EYE = [33, 133, 159, 145, 153, 154, 155, 173]
RIGHT_EYE = [362, 263, 386, 374, 380, 381, 382, 398]
LEFT_BROW = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
RIGHT_BROW = [336, 296, 334, 293, 300, 285, 295, 282, 283, 276]


def quality_metrics(rgb: np.ndarray) -> dict:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())

    return {
        "sharpness": sharpness,
        "brightness": brightness,
        "contrast": contrast,
        "sharpness_score": int(np.clip(sharpness / 4.0, 0, 100)),
        "brightness_score": int(np.clip(100 - abs(brightness - 130) * 0.8, 0, 100)),
        "contrast_score": int(np.clip(contrast * 2.0, 0, 100)),
    }


def analyze_face(image: Image.Image) -> dict:
    rgb = np.array(image.convert("RGB"))
    h, w = rgb.shape[:2]
    metrics = quality_metrics(rgb)

    result = {
        "ok": False,
        "confidence": 0.0,
        "eye_brow_box": None,
        "metrics": metrics,
        "message": "Detecção automática indisponível.",
    }

    if mp is None:
        return result

    try:
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )
        detection = face_mesh.process(rgb)
        face_mesh.close()

        if not detection.multi_face_landmarks:
            result["message"] = "Nenhum rosto detectado com confiança."
            return result

        landmarks = detection.multi_face_landmarks[0].landmark
        ids = LEFT_EYE + RIGHT_EYE + LEFT_BROW + RIGHT_BROW
        pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in ids]
        pts_np = np.array(pts, dtype=np.int32)

        x1, y1 = pts_np.min(axis=0)
        x2, y2 = pts_np.max(axis=0)

        result.update({
            "ok": True,
            "confidence": 0.95,
            "eye_brow_box": (int(x1), int(y1), int(x2), int(y2)),
            "message": "Olhos e sobrancelhas detectados.",
        })
        return result

    except Exception as exc:
        result["message"] = f"Falha na detecção automática: {exc}"
        return result
