# project_root/services/summary_generation_service.py
import asyncio
from models import SummaryResult
from .llm_text.facade import LLMTextSummaryService
from .llm_keyword.facade import LLMKeywordService
from .extraction_text.facade import ExtractionTextSummaryService
from .extraction_keyword.facade import ExtractionKeywordService

class SummaryGenerationService:
    def __init__(
        self,
        llm_text_svc: LLMTextSummaryService,
        llm_keyword_svc: LLMKeywordService,
        extraction_text_svc: ExtractionTextSummaryService,
        extraction_keyword_svc: ExtractionKeywordService,
    ):
        self.llm_text_svc = llm_text_svc
        self.llm_keyword_svc = llm_keyword_svc
        self.extraction_text_svc = extraction_text_svc
        self.extraction_keyword_svc = extraction_keyword_svc

    async def generate_full_summary(self, text: str) -> SummaryResult:
        llm_text, llm_kw, extr_text, extr_kw = await asyncio.gather(
            self.llm_text_svc.generate(text),
            self.llm_keyword_svc.generate(text),
            self.extraction_text_svc.generate(text),
            self.extraction_keyword_svc.generate(text),
        )
        return SummaryResult(
            llm_text_summary=llm_text,
            llm_keyword_summary=llm_kw,
            extraction_text_summary=extr_text,
            extraction_keyword_summary=extr_kw,
        )