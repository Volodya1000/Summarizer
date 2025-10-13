# project_root/file_handler.py
import asyncio
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile

class FileUploader:
    def __init__(self, uploads_dir: Path):
        self.uploads_dir = uploads_dir
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile) -> Path:
        filename = Path(upload.filename).name
        target = self.uploads_dir / f"{int(datetime.utcnow().timestamp())}_{filename}"
        await asyncio.to_thread(self._write_file, upload, target)
        return target

    def _write_file(self, upload: UploadFile, target_path: Path):
        try:
            upload.file.seek(0)
            with open(target_path, "wb") as out_f:
                shutil.copyfileobj(upload.file, out_f)
        finally:
            upload.file.close()

    async def extract_text(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return await asyncio.to_thread(self._extract_text_pdf, str(file_path))
        elif suffix == ".docx":
            return await asyncio.to_thread(self._extract_text_docx, str(file_path))
        else:
            raise ValueError("Unsupported file type: only PDF and DOCX are allowed")

    def _extract_text_docx(self, path: str) -> str:
        try:
            from docx import Document
        except ImportError as e:
            raise RuntimeError("python-docx not installed. Install with: pip install python-docx") from e
        doc = Document(path)
        return "\n\n".join([p.text for p in doc.paragraphs if p.text])

    def _extract_text_pdf(self, path: str) -> str:
        try:
            from pdfminer.high_level import extract_text
        except ImportError as e:
            raise RuntimeError("pdfminer.six not installed. Install with: pip install pdfminer.six") from e
        return extract_text(path) or ""