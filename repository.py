# project_root/repository.py

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from models import Base, TextDocument, SummaryResult, TextDocumentDTO, DocumentInfoDTO

class TextRepositoryAsync:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False, future=True)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def add_document(
        self,
        original_text: str,
        summary_result: SummaryResult,
        file_name: str,
        name: str
    ) -> int:
        async with self.async_session() as session:
            async with session.begin():
                doc = TextDocument(
                    original_text=original_text,
                    summary_json=summary_result.dict(),
                    file_name=file_name,
                    name=name
                )
                session.add(doc)
            await session.refresh(doc)
            return doc.id

    async def get_document(self, doc_id: int) -> Optional[TextDocumentDTO]:
        async with self.async_session() as session:
            doc = await session.get(TextDocument, doc_id)
            if doc is None:
                return None
            summary_obj = SummaryResult(**doc.summary_json)
            return TextDocumentDTO(
                id=doc.id,
                file_name=doc.file_name,
                name=doc.name,
                original_text=doc.original_text,
                summary=summary_obj,
                created_at=doc.created_at
            )

    async def list_document_info(self) -> List[DocumentInfoDTO]:
        async with self.async_session() as session:
            result = await session.execute(select(TextDocument).order_by(TextDocument.created_at.desc()))
            docs = result.scalars().all()
            return [
                DocumentInfoDTO(
                    id=d.id,
                    file_name=d.file_name,
                    name=d.name,
                    created_at=d.created_at
                ) for d in docs
            ]

    async def delete_document(self, doc_id: int) -> bool:
        async with self.async_session() as session:
            async with session.begin():
                doc = await session.get(TextDocument, doc_id)
                if doc is None:
                    return False
                await session.delete(doc)
        return True

    async def find_document_by_name(self, name: str) -> Optional[DocumentInfoDTO]:
        async with self.async_session() as session:
            result = await session.execute(select(TextDocument).where(TextDocument.name == name))
            doc = result.scalars().first()
            if doc:
                return DocumentInfoDTO(id=doc.id, file_name=doc.file_name, name=doc.name, created_at=doc.created_at)
            return None