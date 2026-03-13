import os
import uuid
from typing import Optional
from app.config import settings


def save_upload_file(content: bytes, original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[1] if original_filename else ""
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)
    return filepath


def get_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    voice_exts = {".mp3", ".wav", ".ogg", ".m4a", ".amr"}
    video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    if ext in image_exts:
        return "image"
    if ext in voice_exts:
        return "voice"
    if ext in video_exts:
        return "video"
    return "text"
