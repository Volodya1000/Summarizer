# project_root/models.py

from __future__ import annotations
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from sqlalchemy.orm import declarative_base

# ----------------------------
# SQLAlchemy ORM Base
# ----------------------------
Base = declarative_base()

# ----------------------------
# Pydantic DTOs (Data Transfer Objects)
# ----------------------------
class KeywordNode(BaseModel):
    keyword: str
    children: List["KeywordNode"] = []

class TextSummary(BaseModel):
    ru: str
    en: str

class KeywordTreeSummary(BaseModel):
    ru: KeywordNode
    en: KeywordNode

class SummaryResult(BaseModel):
    llm_text_summary: TextSummary
    llm_keyword_summary: KeywordTreeSummary
    extraction_text_summary: TextSummary
    extraction_keyword_summary: KeywordTreeSummary

class TextDocumentDTO(BaseModel):
    id: int
    file_name: str
    name: Optional[str]
    original_text: str
    summary: SummaryResult
    created_at: Optional[datetime] # Added for consistency on detail view

class DocumentInfoDTO(BaseModel):
    id: int
    file_name: str
    name: Optional[str]
    created_at: Optional[datetime]

# Resolve forward references in Pydantic models
KeywordNode.update_forward_refs()
KeywordTreeSummary.update_forward_refs()
SummaryResult.update_forward_refs()


# ----------------------------
# SQLAlchemy ORM Model
# ----------------------------
class TextDocument(Base):
    __tablename__ = "text_documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String, nullable=False)
    name = Column(String, nullable=False, unique=True)
    original_text = Column(String, nullable=False)
    summary_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())