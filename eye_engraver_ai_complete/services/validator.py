from __future__ import annotations

import numpy as np
from PIL import Image


def validate_final_image(image: Image.Image, analysis: dict | None = None) -> dict:
    issues = []

    if image.size != (900, 200):
        issues.append(f"Arquivo está em {image.size[0]}×{image.size[1]}, não em 900×200.")

    w, h = image.size
    if h == 0 or abs((w / h) - 4.5) > 1e-9:
        issues.append("A proporção do arquivo não é 4,5:1.")

    arr = np.asarray(image)
    if arr.ndim == 2:
        edges = [arr[0, :], arr[-1, :], arr[:, 0], arr[:, -1]]
    else:
        edges = [arr[0, :, :], arr[-1, :, :], arr[:, 0, :], arr[:, -1, :]]

    suspicious = sum(np.std(edge.astype(float)) < 0.2 for edge in edges)
    if suspicious >= 3:
        issues.append("Possível borda/padding uniforme nas extremidades.")

    return {
        "passed": not issues,
        "issues": issues,
        "size": image.size,
        "aspect_ratio": w / h if h else None,
    }
