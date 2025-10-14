from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse

from dependencies import get_document_service, get_uploader
from services.document_service import DocumentService
from file_handler import FileUploader
from fastapi.responses import StreamingResponse
from io import BytesIO

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, service: DocumentService = Depends(get_document_service)):
    docs = await service.list_documents_info()
    return request.app.templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "documents": docs
        }
    )

@router.post("/documents/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    service: DocumentService = Depends(get_document_service),
    uploader: FileUploader = Depends(get_uploader),
):
    if not name.strip():
        return request.app.templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Имя документа обязательно"},
            status_code=400
        )

    if await service.find_by_name(name.strip()):
        return request.app.templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Документ с именем '{name}' уже существует"},
            status_code=409
        )

    try:
        saved_path = await uploader.save_upload(file)  # должен быть async
        text = await uploader.extract_text(saved_path)  # должен быть async
        orig_filename = "_".join(saved_path.name.split("_")[1:])
        doc_id = await service.create_document(file_name=orig_filename, text=text or "", name=name.strip())
        return RedirectResponse(url=f"/documents/{doc_id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return request.app.templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Ошибка: {e}"},
            status_code=500
        )

@router.get("/documents/{doc_id}", response_class=HTMLResponse)
async def view_document(doc_id: int, request: Request, service: DocumentService = Depends(get_document_service)):
    try:
        doc = await service.get_document(doc_id)
        return request.app.templates.TemplateResponse(
            "document.html",
            {"request": request, "doc": doc}
        )
    except ValueError as e:
        return request.app.templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=404
        )

@router.post("/documents/{doc_id}/delete")
async def delete_document_form(doc_id: int, service: DocumentService = Depends(get_document_service)):
    await service.delete_document(doc_id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/documents/{doc_id}/report/download")
async def download_report(doc_id: int, service: DocumentService = Depends(get_document_service)):
    pdf_bytes = await service.generate_report(doc_id)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="document_{doc_id}.pdf"'}
    )


@router.get("/documents/{doc_id}/report/pdf")
async def report_pdf(doc_id: int, service: DocumentService = Depends(get_document_service)):
    pdf_bytes = await service.generate_report(doc_id)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="document_{doc_id}.pdf"'}
    )

@router.get("/documents/{doc_id}/report/print", response_class=HTMLResponse)
async def print_report_page(doc_id: int, request: Request):
    pdf_url = request.url_for("report_pdf", doc_id=doc_id)
    return request.app.templates.TemplateResponse(
        "print_pdf.html",
        {"request": request, "pdf_url": pdf_url}
    )

@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """Отображает страницу помощи пользователю."""
    return request.app.templates.TemplateResponse(
        "help.html",
        {"request": request}
    )