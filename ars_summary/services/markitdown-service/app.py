import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile


ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx"}
MAX_FILE_BYTES = 30 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024

app = FastAPI(title="Internal MarkItDown converter", version="1.0.0")


def validate_filename(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(status_code=415, detail=f"Unsupported file type. Allowed: {allowed}")
    return suffix


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/convert")
async def convert(file: UploadFile = File(...)) -> dict[str, str]:
    filename = file.filename or "upload"
    suffix = validate_filename(filename)

    with tempfile.TemporaryDirectory(prefix="markitdown-") as temporary_directory:
        input_path = Path(temporary_directory) / f"input{suffix}"
        size = 0
        with input_path.open("wb") as destination:
            while chunk := await file.read(CHUNK_BYTES):
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    raise HTTPException(status_code=413, detail="File exceeds 30 MB limit")
                destination.write(chunk)

        output_path = Path(temporary_directory) / "converted.md"
        try:
            result = subprocess.run(
                ["markitdown", str(input_path), "-o", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired as error:
            raise HTTPException(status_code=422, detail="MarkItDown conversion timed out") from error

        if result.returncode != 0 or not output_path.exists():
            message = (result.stderr or result.stdout or "Unknown conversion error").strip()
            raise HTTPException(status_code=422, detail=f"MarkItDown conversion failed: {message[:1000]}")

        markdown = output_path.read_text(encoding="utf-8", errors="replace")
        return {
            "filename": filename,
            "markdown": markdown,
            "content_type": file.content_type or "application/octet-stream",
        }
