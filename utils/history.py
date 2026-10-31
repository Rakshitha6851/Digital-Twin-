"""
history.py
------------
Saves every generated Digital Twin so it can be reopened later:

    results/<id>.json            record: patient values, twin result, source,
                                 OCR text, list of downloaded reports
    results/<id>_source.<ext>    the original uploaded / camera image (if any)
    reports/<id>_<lang>_<time>.pdf   every PDF the user downloaded

Plain files (no database) keep the project dependency-free. NOTE: there is
no user login in this app, so history is shared by everyone who uses the
same running instance. On hosts with an ephemeral disk (e.g. Streamlit
Community Cloud) saved files are lost when the app restarts/redeploys.
"""

import json
import os
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

_ID_RE = re.compile(r"^[0-9]{14}_[0-9a-f]{6}$")


def _ensure_dirs():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def _valid_id(record_id: Optional[str]) -> bool:
    """Guards against path traversal: ids are only ever generated here."""
    return bool(record_id) and bool(_ID_RE.match(str(record_id)))


def _record_path(record_id: str) -> str:
    return os.path.join(RESULTS_DIR, f"{record_id}.json")


def _write_json(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    os.replace(tmp, path)  # atomic on the same filesystem


def save_record(
    patient: dict,
    twin: dict,
    source: str,
    image_bytes: Optional[bytes] = None,
    image_ext: str = "jpg",
    raw_ocr_text: Optional[str] = None,
) -> str:
    """Saves a new record and returns its id."""
    _ensure_dirs()
    record_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

    image_file = None
    if image_bytes:
        ext = re.sub(r"[^a-z0-9]", "", (image_ext or "jpg").lower()) or "jpg"
        image_file = f"{record_id}_source.{ext}"
        with open(os.path.join(RESULTS_DIR, image_file), "wb") as f:
            f.write(image_bytes)

    record = {
        "id": record_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "patient": patient,
        "twin": twin,
        "image_file": image_file,
        "raw_ocr_text": raw_ocr_text,
        "downloads": [],
    }
    _write_json(_record_path(record_id), record)
    return record_id


def load_record(record_id: str) -> Optional[Dict]:
    if not _valid_id(record_id):
        return None
    try:
        with open(_record_path(record_id), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def list_records() -> List[Dict]:
    """All records, newest first. Unreadable files are skipped."""
    _ensure_dirs()
    records = []
    for name in os.listdir(RESULTS_DIR):
        if name.endswith(".json"):
            rec = load_record(name[:-5])
            if rec:
                records.append(rec)
    records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return records


def log_download(record_id: Optional[str], lang: str, pdf_bytes: bytes):
    """Stores a PDF the user just downloaded and logs it on the record.
    Silently does nothing if there's no saved record to attach it to."""
    try:
        rec = load_record(record_id) if record_id else None
        if rec is None:
            return
        _ensure_dirs()
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{record_id}_{lang}_{stamp}.pdf"
        with open(os.path.join(REPORTS_DIR, filename), "wb") as f:
            f.write(pdf_bytes)
        rec.setdefault("downloads", []).append({
            "lang": lang,
            "file": filename,
            "at": datetime.now().isoformat(timespec="seconds"),
        })
        _write_json(_record_path(record_id), rec)
    except Exception:
        # Saving history must never break the download itself.
        pass


def read_report_file(filename: str) -> Optional[bytes]:
    if not filename or os.path.basename(filename) != filename:
        return None
    path = os.path.join(REPORTS_DIR, filename)
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def read_source_image(record: Dict) -> Optional[bytes]:
    name = record.get("image_file")
    if not name or os.path.basename(name) != name:
        return None
    try:
        with open(os.path.join(RESULTS_DIR, name), "rb") as f:
            return f.read()
    except OSError:
        return None


def delete_record(record_id: str):
    """Deletes a record plus its source image and downloaded reports."""
    rec = load_record(record_id)
    if rec is None:
        return
    targets = [_record_path(record_id)]
    if rec.get("image_file") and os.path.basename(rec["image_file"]) == rec["image_file"]:
        targets.append(os.path.join(RESULTS_DIR, rec["image_file"]))
    for d in rec.get("downloads", []):
        fn = d.get("file", "")
        if fn and os.path.basename(fn) == fn:
            targets.append(os.path.join(REPORTS_DIR, fn))
    for path in targets:
        try:
            os.remove(path)
        except OSError:
            pass


def delete_all():
    for rec in list_records():
        delete_record(rec["id"])
