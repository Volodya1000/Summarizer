class PromptBuilder:
    """Универсальный класс для создания промптов для Ollama."""
    PROMPTS = {
        # Промпты для одноязычной генерации (используются схемы List[KeywordNode])
        'one_shot': {
            'ru': """Проанализируй следующий текст и составь **список корневых узлов** (JSON array) — каждый элемент массива должен быть объектом с полями 'name' и 'children', где 'children' — список дочерних узлов той же структуры.

Требования:
- Верни **JSON-массив** (список) объектов. Никакого дополнительного текста — только корректный JSON.
- Каждый объект — узел формата {{ "name": "...", "children": [...] }}.
- Названия в поле 'name' оставь на языке, указанном параметром language.
- Создай не менее {min_roots} корневых узлов.
- Обязательно сделай хотя бы одну ветку глубиной не менее {min_depth} уровней.
- Используй только поля 'name' и 'children'.

Текст для анализа:
{text}""",

            'en': """Analyze the following text and produce a **JSON array** (list) of root keyword nodes. Each element of the array must be an object with exactly two fields: "name" and "children" (where "children" is a list of nodes of the same structure).

Requirements:
- Return **only** a valid JSON array (no prose, no comments).
- Each element should look like: {{ "name": "...", "children": [...] }}.
- Create at least {min_roots} root nodes.
- Ensure at least one branch reaches depth {min_depth}.
- All "name" values must be written in English (translate from Russian if necessary).
- Use only the fields 'name' and 'children'.
- The JSON must conform to a list of KeywordNode objects.

Text to analyze:
{text}"""
        },
        # Промпт для двуязычной генерации (используется схема KeywordTreeSummary)
        'dual_lang': """Проанализируй следующий текст и составь **единый JSON-объект** с двумя полями:
1.  **"ru"**: Список корневых узлов (JSON array) на **русском** языке.
2.  **"en"**: Список корневых узлов (JSON array) на **английском** языке.

Каждый список должен содержать узлы формата: {{ "name": "...", "children": [...] }}.

Требования:
- Верни **только корректный JSON-объект** (без текста и комментариев).
- Оба списка ("ru" и "en") должны иметь не менее {min_roots} корневых узлов.
- В каждой языковой версии должна быть хотя бы одна ветка глубиной не менее {min_depth} уровней.
- Используй только поля 'name' и 'children' внутри массивов "ru" и "en".
- В поле "en" все названия должны быть переведены на английский.

Текст для анализа:
{text}"""
    }

    @classmethod
    def build_one_shot(cls, text: str, language: str = 'ru', min_roots: int = 2, min_depth: int = 4) -> str:
        """Строит промпт для одноязычной генерации (List[KeywordNode])."""
        key = 'en' if language == 'en' else 'ru'
        return cls.PROMPTS['one_shot'][key].format(text=text, min_roots=min_roots, min_depth=min_depth)

    @classmethod
    def build_dual_lang_prompt(cls, text: str, min_roots: int = 2, min_depth: int = 4) -> str:
        """Строит промпт для двуязычной генерации (KeywordTreeSummary)."""
        return cls.PROMPTS['dual_lang'].format(text=text, min_roots=min_roots, min_depth=min_depth)