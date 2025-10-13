# project_root/services/llm_text/facade.py
import asyncio
from models import TextSummary

class LLMTextSummaryService:
    async def generate(self, text: str) -> TextSummary:
        await asyncio.sleep(0.1) # Simulate async work
        return TextSummary(ru="LLM: краткое резюме (RU)", en="LLM: short summary (EN)")