# project_root/services/extraction_keyword/facade.py
import asyncio
from models import KeywordNode, KeywordTreeSummary

class ExtractionKeywordService:
    async def generate(self, text: str) -> KeywordTreeSummary:
        await asyncio.sleep(0.03)
        node = KeywordNode(keyword="extr_root", children=[KeywordNode(keyword="extr_child")])
        return KeywordTreeSummary(ru=node, en=node)