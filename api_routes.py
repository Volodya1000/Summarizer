# app/api_routes.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from dependencies import get_document_service
from services.document_service import DocumentService
from models import DocumentInfoDTO, TextDocumentDTO

router = APIRouter()

@router.get("/documents/", response_model=List[DocumentInfoDTO])
async def api_list_documents(service: DocumentService = Depends(get_document_service)):
    return await service.list_documents_info()

@router.get("/documents/{doc_id}", response_model=TextDocumentDTO)
async def api_get_document(doc_id: int, service: DocumentService = Depends(get_document_service)):
    try:
        return await service.get_document(doc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
