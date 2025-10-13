# project_root/services/llm_keyword/facade.py
import asyncio
from models import KeywordNode, KeywordTreeSummary

class LLMKeywordService:
    async def generate(self, text: str) -> KeywordTreeSummary:
        await asyncio.sleep(0.08)
        node = KeywordNode(keyword="llm_root", children=[KeywordNode(keyword="llm_child")])
        return KeywordTreeSummary(ru=node, en=node)