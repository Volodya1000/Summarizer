import os
import json
import asyncio
from typing import Optional, Union, Type, AsyncGenerator
from pydantic import BaseModel, RootModel
from ollama import Client
from dotenv import load_dotenv
from .json_validator import JsonValidator
import re

# =============================
# Конфигурация
# =============================
load_dotenv()
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")
if not OLLAMA_API_KEY:
    print("⚠️ Предупреждение: переменная окружения OLLAMA_API_KEY не установлена.")

# =============================
# Ollama Async Client
# =============================
class OllamaClient:
    """Асинхронный клиент для взаимодействия с Ollama API."""
    def __init__(self, model_name: str = "gpt-oss:120b-cloud", host: str = "https://ollama.com"):
        if not OLLAMA_API_KEY:
            raise ValueError("❌ Не найден OLLAMA_API_KEY в переменных окружения")

        self.api_key = OLLAMA_API_KEY
        self.client = Client(host=host, headers={"Authorization": f"Bearer {self.api_key}"})
        self.model_name = model_name

    def _get_schema(self, schema: Optional[Union[dict, Type[BaseModel]]]) -> Optional[dict]:
        """Возвращает JSON-схему из Pydantic-модели или словаря."""
        if schema is None:
            return None
        if isinstance(schema, dict):
            return schema
        if isinstance(schema, type) and (issubclass(schema, BaseModel) or issubclass(schema, RootModel)):
            return schema.model_json_schema()
        raise TypeError("Schema должен быть dict или Pydantic BaseModel/RootModel")

    async def async_stream_ask(
        self, prompt: str, schema: Optional[Union[dict, Type[BaseModel]]] = None
    ) -> AsyncGenerator[str, None]:
        """Асинхронный потоковый запрос к Ollama."""
        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs = {"stream": True}

            schema_dict = self._get_schema(schema)
            if schema_dict:
                kwargs["format"] = "json"
                kwargs["options"] = {
                    "temperature": 0.0,
                    "stop": ["</tool_call>"],
                    "response_format": "json",
                }

            # ✅ Правильный вызов (без _client)
            for part in self.client.chat(self.model_name, messages=messages, **kwargs):
                yield part["message"]["content"]

        except Exception as e:
            print(f"❌ Ошибка соединения с Ollama: {e}")
            return

    async def async_ask(
        self, prompt: str, schema: Optional[Union[dict, Type[BaseModel]]] = None
    ) -> Union[str, BaseModel, None]:
        """Асинхронный запрос к LLM с валидацией Pydantic."""
        response_text = ""

        # --- потоковый ответ ---
        async for chunk in self.async_stream_ask(prompt, schema=schema):
            print(chunk, end="", flush=True)
            response_text += chunk

        # --- если стриминг ничего не вернул ---
        if response_text == "":
            messages = [{"role": "user", "content": prompt}]
            kwargs = {}
            schema_dict = self._get_schema(schema)
            if schema_dict:
                kwargs["format"] = "json"
                kwargs["options"] = {"response_format": "json"}

            # ✅ Синхронный вызов через отдельный поток
            resp = await asyncio.to_thread(self.client.chat, self.model_name, messages=messages, **kwargs)

            if isinstance(resp, dict) and "message" in resp and "content" in resp["message"]:
                response_text = resp["message"]["content"]
            else:
                response_text = json.dumps(resp)

        print()  # новая строка после вывода

        # --- валидация ---
        if schema and isinstance(schema, type) and (issubclass(schema, BaseModel) or issubclass(schema, RootModel)):
            validated = JsonValidator.safe_validate(schema, response_text)
            if validated is not None:
                if issubclass(schema, RootModel):
                    return validated.root
                return validated
            return None

        return response_text
