import json
import uuid
import os
from pathlib import Path
from typing import Any
from app.config import get_settings

settings = get_settings()


def to_json_str(data: Any) -> str:
    """Serialize a Python object to a JSON string for storage."""
    return json.dumps(data, ensure_ascii=False)


def from_json_str(value: str | None) -> Any:
    """Deserialize a JSON string from DB storage."""
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def save_upload(file_bytes: bytes, original_filename: str) -> str:
    """Save uploaded bytes to the uploads directory and return relative path."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(original_filename).suffix.lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / filename
    dest.write_bytes(file_bytes)
    return str(dest)


def remove_file(path: str | None) -> None:
    """Silently remove a file if it exists."""
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
