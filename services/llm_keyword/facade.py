# project_root/services/llm_keyword/facade.py
import asyncio
from models import KeywordNode, KeywordTreeSummary

import asyncio
from typing import List

class LLMKeywordService:
    async def generate(self, text: str) -> KeywordTreeSummary:
        # создаём узлы
        root_node = KeywordNode(name="llm_root", children=[KeywordNode(name="llm_child")])
        
        # оборачиваем в список, так как ru/en теперь List[KeywordNode]
        return KeywordTreeSummary(
            ru=[root_node],
            en=[root_node]
        )
