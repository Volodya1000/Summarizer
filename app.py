# project_root/app.py
import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Project-specific imports
from models import TextDocumentDTO, DocumentInfoDTO
from repository import TextRepositoryAsync
from services.llm_text.facade import LLMTextSummaryService
from services.llm_keyword.facade import LLMKeywordService
from services.extraction_text.facade import ExtractionTextSummaryService
from services.extraction_keyword.facade import ExtractionKeywordService
from services.summary_generation_service import SummaryGenerationService
from services.document_service import DocumentService
from file_handler import FileUploader

# ----------------------------
# App setup and configuration
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"

app = FastAPI(title="Async Document Summary")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ----------------------------
# Application startup/shutdown events
# ----------------------------
@app.on_event("startup")
async def startup_event():
    # Initialize repository
    db_url = os.environ.get("DB_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'texts_async.db'}")
    repo = TextRepositoryAsync(db_url=db_url)
    await repo.init_models()

    # Initialize services
    summary_service = SummaryGenerationService(
        llm_text_svc=LLMTextSummaryService(),
        llm_keyword_svc=LLMKeywordService(),
        extraction_text_svc=ExtractionTextSummaryService(),
        extraction_keyword_svc=ExtractionKeywordService(),
    )
    document_service = DocumentService(repo=repo, summary_service=summary_service)

    # Store instances in app state for dependency injection
    app.state.document_service = document_service
    app.state.uploader = FileUploader(UPLOADS_DIR)
    app.state.repo = repo

@app.on_event("shutdown")
async def shutdown_event():
    if repo := getattr(app.state, "repo", None):
        await repo.engine.dispose()

# ----------------------------
# Dependency Injection
# ----------------------------
def get_document_service(request: Request) -> DocumentService:
    return request.app.state.document_service

def get_uploader(request: Request) -> FileUploader:
    return request.app.state.uploader

# ----------------------------
# Web Endpoints (HTML)
# ----------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, service: DocumentService = Depends(get_document_service)):
    docs = await service.list_documents_info()
    for d in docs:
        if d.created_at:
            d.created_at = d.created_at.strftime("%Y-%m-%d %H:%M:%S")
    return templates.TemplateResponse("index.html", {"request": request, "documents": docs})

@app.post("/documents/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    service: DocumentService = Depends(get_document_service),
    uploader: FileUploader = Depends(get_uploader),
):
    if not name or not name.strip():
        return templates.TemplateResponse("error.html", {"request": request, "message": "Имя документа обязательно"}, status_code=400)

    if await service.find_by_name(name.strip()):
        return templates.TemplateResponse("error.html", {"request": request, "message": f"Документ с именем '{name}' уже существует"}, status_code=409)

    try:
        saved_path = await uploader.save_upload(file)
        text = await uploader.extract_text(saved_path)
        orig_filename = "_".join(saved_path.name.split("_")[1:])
        doc_id = await service.create_document(file_name=orig_filename, text=text or "", name=name.strip())
        return RedirectResponse(url=f"/documents/{doc_id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "message": f"Произошла ошибка: {e}"}, status_code=500)

@app.get("/documents/{doc_id}", response_class=HTMLResponse)
async def view_document(doc_id: int, request: Request, service: DocumentService = Depends(get_document_service)):
    try:
        doc = await service.get_document(doc_id)
        if doc.created_at:
            doc.created_at = doc.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return templates.TemplateResponse("document.html", {"request": request, "doc": doc})
    except ValueError as e:
        return templates.TemplateResponse("error.html", {"request": request, "message": str(e)}, status_code=404)

@app.post("/documents/{doc_id}/delete")
async def delete_document_form(doc_id: int, service: DocumentService = Depends(get_document_service)):
    await service.delete_document(doc_id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# ----------------------------
# Web Endpoints (JSON API)
# ----------------------------
@app.get("/api/documents/", response_model=List[DocumentInfoDTO])
async def api_list_documents(service: DocumentService = Depends(get_document_service)):
    return await service.list_documents_info()

@app.get("/api/documents/{doc_id}", response_model=TextDocumentDTO)
async def api_get_document(doc_id: int, service: DocumentService = Depends(get_document_service)):
    try:
        return await service.get_document(doc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ----------------------------
# Main entry point for uvicorn
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    print("--- To run the app, use the command: uvicorn app:app --reload ---")
    uvicorn.run(app, host="0.0.0.0", port=8000)