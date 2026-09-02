from __future__ import annotations

from PIL import Image

TARGET_ASPECT = 4.5


def _clamp(value, low, high):
    return max(low, min(value, high))


def _make_exact_ratio_box(cx, cy, crop_h, w, h):
    crop_h = max(2, int(round(crop_h)))
    crop_h -= crop_h % 2
    crop_w = int(round(crop_h * TARGET_ASPECT))

    if crop_w > w:
        crop_w = max(9, w - (w % 9))
        crop_h = int(crop_w / TARGET_ASPECT)

    if crop_h > h:
        crop_h = max(2, h - (h % 2))
        crop_w = int(crop_h * TARGET_ASPECT)

    left = int(round(cx - crop_w / 2))
    top = int(round(cy - crop_h / 2))
    left = _clamp(left, 0, max(0, w - crop_w))
    top = _clamp(top, 0, max(0, h - crop_h))
    return (left, top, left + crop_w, top + crop_h)


def fallback_box(w, h):
    crop_h = min(h * 0.38, w / TARGET_ASPECT)
    cx = w / 2
    cy = h * 0.42
    return _make_exact_ratio_box(cx, cy, crop_h, w, h)


def build_smart_crop(
    image: Image.Image,
    analysis: dict,
    output_size=(900, 200),
    vertical_bias: float = 0.0,
    crop_scale: float = 1.05,
):
    w, h = image.size

    if not analysis.get("ok") or not analysis.get("eye_brow_box"):
        box = fallback_box(w, h)
    else:
        x1, y1, x2, y2 = analysis["eye_brow_box"]
        content_w = max(1, x2 - x1)
        content_h = max(1, y2 - y1)

        desired_h = content_h * 1.72 * crop_scale
        desired_w = desired_h * TARGET_ASPECT

        min_w = content_w * 1.32
        if desired_w < min_w:
            desired_w = min_w
            desired_h = desired_w / TARGET_ASPECT

        cx = (x1 + x2) / 2
        content_cy = (y1 + y2) / 2

        # Slight upward composition bias keeps forehead small and eyes central.
        cy = content_cy - (0.05 * desired_h) + (vertical_bias * 0.18 * desired_h)
        box = _make_exact_ratio_box(cx, cy, desired_h, w, h)

    cropped = image.crop(box)
    final = cropped.resize(output_size, Image.Resampling.LANCZOS)
    cw, ch = cropped.size

    return final, {
        "crop_box": box,
        "crop_size": (cw, ch),
        "aspect_ratio": cw / ch if ch else 0,
    }
