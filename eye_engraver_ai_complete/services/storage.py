from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image

DATA = Path("data")
ORIGINALS = DATA / "originals"
PROCESSED = DATA / "processed"
FINAL = DATA / "final"
RECORDS = DATA / "records"

for folder in (ORIGINALS, PROCESSED, FINAL, RECORDS):
    folder.mkdir(parents=True, exist_ok=True)


def sanitize_id(value: str) -> str:
    safe = "".join(ch for ch in value if ch.isalnum() or ch in ("-", "_"))
    return safe or datetime.now().strftime("%Y%m%d-%H%M%S")


def save_job(job_id: str, original: Image.Image, processed: Image.Image, final: Image.Image, meta: dict[str, Any]) -> dict:
    job_id = sanitize_id(job_id)

    original_path = ORIGINALS / f"{job_id}.png"
    processed_path = PROCESSED / f"{job_id}.png"
    final_path = FINAL / f"{job_id}.png"
    record_path = RECORDS / f"{job_id}.json"

    original.save(original_path, "PNG")
    processed.save(processed_path, "PNG")
    final.save(final_path, "PNG")

    record = {
        "job_id": job_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": meta.get("status", "approved"),
        "original_path": str(original_path),
        "processed_path": str(processed_path),
        "final_path": str(final_path),
        "meta": meta,
    }

    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def load_jobs() -> list[dict]:
    jobs = []
    for path in RECORDS.glob("*.json"):
        try:
            jobs.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            pass
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jobs


def delete_job(job_id: str) -> None:
    job_id = sanitize_id(job_id)
    for folder, suffix in [
        (ORIGINALS, ".png"),
        (PROCESSED, ".png"),
        (FINAL, ".png"),
        (RECORDS, ".json"),
    ]:
        path = folder / f"{job_id}{suffix}"
        if path.exists():
            path.unlink()
