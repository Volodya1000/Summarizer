# app/dependencies.py
from fastapi import Request
from services.document_service import DocumentService
from file_handler import FileUploader

def get_document_service(request: Request) -> DocumentService:
    return request.app.state.document_service

def get_uploader(request: Request) -> FileUploader:
    return request.app.state.uploader
