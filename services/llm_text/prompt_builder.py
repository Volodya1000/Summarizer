class SummaryPromptBuilder:
    """Строитель промптов для двуязычного резюме."""

    TEMPLATE = """Проанализируй следующий текст и создай краткое резюме на двух языках в формате JSON:

{{
  "ru": "резюме на русском языке",
  "en": "summary in English"
}}

Требования:
- Верни **только JSON-объект** (никаких комментариев или текста).
- Резюме должно состоять примерно из {sentences} предложений.
- В "en" — корректный английский перевод.
- Сохрани ключи "ru" и "en" строго как в примере.

Текст для анализа:
{text}
"""

    @classmethod
    def build_dual_lang_prompt(cls, text: str, sentences: int = 5) -> str:
        """Создаёт промпт для генерации двуязычного резюме."""
        return cls.TEMPLATE.format(text=text.strip(), sentences=sentences)
