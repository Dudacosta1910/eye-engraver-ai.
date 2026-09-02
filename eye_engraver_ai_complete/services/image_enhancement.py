from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def auto_recommend(metrics: dict) -> dict:
    brightness = metrics.get("brightness", 128)
    contrast = metrics.get("contrast", 45)
    sharpness = metrics.get("sharpness", 150)

    treatment = 55
    if brightness < 95 or brightness > 175:
        treatment += 8
    if contrast < 35:
        treatment += 8
    if sharpness < 80:
        treatment += 10

    return {
        "treatment_strength": int(np.clip(treatment, 25, 80)),
        "note": "Ajuste automático calculado pela qualidade da imagem.",
    }


def enhance_for_engraving(image: Image.Image, strength: float = 0.55) -> Image.Image:
    strength = float(np.clip(strength, 0.0, 1.0))

    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    denoise_h = 2 + int(5 * strength)
    denoised = cv2.fastNlMeansDenoising(
        gray, None, h=denoise_h, templateWindowSize=7, searchWindowSize=21
    )

    clip_limit = 1.25 + (0.9 * strength)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    local = clahe.apply(denoised)

    mixed = cv2.addWeighted(
        gray, 1.0 - 0.52 * strength,
        local, 0.52 * strength,
        0
    )

    blurred = cv2.GaussianBlur(mixed, (0, 0), 1.0)
    amount = 0.18 + 0.5 * strength
    sharpened = cv2.addWeighted(mixed, 1.0 + amount, blurred, -amount, 0)

    out = np.clip(sharpened, 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode="L")
