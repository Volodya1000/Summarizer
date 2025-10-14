import asyncio
from services.ollama_client import OllamaClient
from models import TextSummary
from services.llm_text.prompt_builder import SummaryPromptBuilder


class LLMTextSummaryService:
    """Генератор двуязычного резюме текста (RU + EN) с использованием Ollama."""

    def __init__(self, client: OllamaClient):
        self.client = client

    async def generate(
        self,
        text: str,
        sentences: int = 8,
        max_attempts: int = 3
    ) -> TextSummary:
        """Генерирует краткое резюме текста на русском и английском языках."""
        prompt = SummaryPromptBuilder.build_dual_lang_prompt(text, sentences=sentences)

        for attempt in range(1, max_attempts + 1):
            print(f"\n🔁 Попытка {attempt} (summary)...")
            resp = await self.client.async_ask(prompt, schema=TextSummary)

            if isinstance(resp, TextSummary):
                print("✅ Получен валидный объект TextSummary.")
                return resp

            print(f"❌ Ошибка: не удалось получить TextSummary. Ответ: {resp}")
            await asyncio.sleep(1.0)

        raise ValueError("❌ Все попытки исчерпаны — не удалось сгенерировать резюме.")
