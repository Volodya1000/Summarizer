import asyncio
from services.ollama_client import OllamaClient 
from models import KeywordNode, KeywordTreeSummary
from services.llm_keyword.prompt_builder import PromptBuilder 
# =============================
# Keyword Tree Generator
# =============================
class LLMKeywordService:
    """Генератор двуязычного дерева ключевых слов, использующий OllamaClient."""
    def __init__(self, client: OllamaClient):
        self.client = client

    async def generate(self, text: str, min_depth: int = 4, min_roots: int = 2, max_attempts: int = 3) -> KeywordTreeSummary: 
        """Запускает асинхронную генерацию с несколькими попытками."""
        prompt = PromptBuilder.build_dual_lang_prompt(text, min_roots=min_roots, min_depth=min_depth)

        for attempt in range(1, max_attempts + 1):
            print(f'\n🔁 Попытка {attempt} (Dual-Lang)...')
            resp = await self.client.async_ask(prompt, schema=KeywordTreeSummary) 

            if isinstance(resp, KeywordTreeSummary):
                print('\n💡 Получен валидный JSON-объект KeywordTreeSummary.')
                return resp
            
            print(f'\n❌ Не удалось получить валидный объект KeywordTreeSummary. Последний ответ: {resp}')
            await asyncio.sleep(1.0) # Ждем перед следующей попыткой

        raise ValueError('❌ Не удалось получить валидный список после всех попыток.')

    @staticmethod
    def tree_depth(node: KeywordNode) -> int:
        """Рекурсивно вычисляет глубину дерева (в настоящее время не используется, но сохранена)."""
        if not node.children:
            return 1
        return 1 + max(LLMKeywordService.tree_depth(child) for child in node.children)

    @staticmethod
    def print_trees(summary: KeywordTreeSummary) -> None:
        """Печатает сгенерированные деревья в консоль."""
        
        # Печать RU
        print('\n--- Дерево ключевых слов (RU) ---')
        for i, node in enumerate(summary.ru, start=1):
            print(f'Root #{i}: {node.name}')
            LLMKeywordService._print_node(node, 1)

        # Печать EN
        print('\n--- Дерево ключевых слов (EN) ---')
        for i, node in enumerate(summary.en, start=1):
            print(f'Root #{i}: {node.name}')
            LLMKeywordService._print_node(node, 1)


    @staticmethod
    def _print_node(node: KeywordNode, indent: int = 0) -> None:
        """Вспомогательная функция для рекурсивной печати узлов."""
        print('    ' * indent + f'- {node.name}')
        for child in node.children:
            LLMKeywordService._print_node(child, indent + 1)
