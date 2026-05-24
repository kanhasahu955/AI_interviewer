"""Serve generated media (portrait clips) from local storage."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter()


@router.get("/media/{file_path:path}")
def get_media_file(file_path: str) -> FileResponse:
    base = settings.STORAGE_DIR.resolve()
    target = (base / file_path).resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=403, detail="Invalid path")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    media_type = "video/mp4" if target.suffix.lower() == ".mp4" else None
    return FileResponse(target, media_type=media_type)
