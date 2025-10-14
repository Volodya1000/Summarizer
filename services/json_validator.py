import re
import json
from typing import Type, Optional
from pydantic import BaseModel, ValidationError


class JsonValidator:
    """Утилиты для очистки и безопасной валидации JSON-ответов LLM."""
    @staticmethod
    def clean_json(text: str) -> str:
        """Очищает текст от окружающих его маркеров (например, ```json)."""
        text = re.sub(r'^\s*```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
        return text.strip()

    @staticmethod
    def safe_validate(schema: Type[BaseModel], text: str) -> Optional[BaseModel]:
        """Пытается очистить и распарсить JSON в заданную схему Pydantic."""
        if text is None:
            print("⚠️ Пустой ответ от LLM")
            return None
        try:
            cleaned = JsonValidator.clean_json(text)
            # Проверка, что это вообще JSON
            json.loads(cleaned) 
            # Используем model_validate_json для BaseModel/RootModel
            return schema.model_validate_json(cleaned) 
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"❌ Не удалось распарсить JSON в схему {getattr(schema, '__name__', str(schema))}: {e}")
            return None
