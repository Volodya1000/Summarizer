# project_root/services/extraction_text/facade.py
import asyncio
from models import TextSummary

class ExtractionTextSummaryService:
    async def generate(self, text: str) -> TextSummary:
        await asyncio.sleep(0.05)
        return TextSummary(ru="Extraction: краткое резюме (RU)", en="Extraction: short summary (EN)")