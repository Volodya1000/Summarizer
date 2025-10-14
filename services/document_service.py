# project_root/services/document_service.py
from typing import List, Optional
from repository import TextRepositoryAsync
from .summary_generation_service import SummaryGenerationService
from models import TextDocumentDTO, DocumentInfoDTO
from .report_service import ReportService
class DocumentService:
    def __init__(self, repo: TextRepositoryAsync, summary_service: SummaryGenerationService):
        self.repo = repo
        self.summary_service = summary_service

    async def create_document(self, file_name: str, text: str, name: str) -> int:
        summary = await self.summary_service.generate_full_summary(text)
        return await self.repo.add_document(text, summary, file_name, name)

    async def get_document(self, doc_id: int) -> TextDocumentDTO:
        doc = await self.repo.get_document(doc_id)
        if doc is None:
            raise ValueError(f"Документ с id={doc_id} не найден.")
        return doc

    async def list_documents_info(self) -> List[DocumentInfoDTO]:
        return await self.repo.list_document_info()
        
    async def find_by_name(self, name: str) -> Optional[DocumentInfoDTO]:
        return await self.repo.find_document_by_name(name)

    async def delete_document(self, doc_id: int) -> bool:
        return await self.repo.delete_document(doc_id)
    
    async def generate_report(self, doc_id: int) -> bytes:
        doc = await self.get_document(doc_id)
        report_service = ReportService()
        return await report_service.generate_pdf(doc)