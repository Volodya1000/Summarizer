# project_root/services/extraction_keyword/facade.py
import asyncio
from models import KeywordNode, KeywordTreeSummary
from langdetect import detect

class ExtractionKeywordService1:
    async def generate(self, text: str) -> KeywordTreeSummary:
        await asyncio.sleep(0.03)
        node = KeywordNode(name="extr_root", children=[KeywordNode(llm_child="extr_child")])
        return KeywordTreeSummary(ru=node, en=node)
from services.translator import LocalTranslator
from .clustering import extract_key_phrases, cluster_phrases
from .tree_builder import build_tree_from_clusters

from typing import List


class ExtractionKeywordService:
    """
    Асинхронный сервис для извлечения ключевых слов и построения двуязычного дерева.
    Всегда возвращает KeywordTreeSummary (RU и EN) независимо от исходного языка.
    """
    def __init__(self, translator: LocalTranslator):
        # Удаляем self.lang, так как он определяется динамически
        self.translator = translator

    def _detect_language(self,text: str) -> str:
        try:
            lang = detect(text)
            if lang.startswith("ru"):
                return "ru"
            return "en"
        except Exception:
            return "en"


    async def _translate_tree(self, nodes: List[KeywordNode], src: str, tgt: str) -> List[KeywordNode]:
        """
        Асинхронно рекурсивно переводит имена узлов в дереве. 
        """
        translated_nodes = []
        for node in nodes:
         
            name_translated = self.translator.translate(node.name, src=src, tgt=tgt)
            
            translated_children = await self._translate_tree(node.children, src=src, tgt=tgt)
            # Предполагаем, что конструктор KeywordNode принимает 'name' и 'children'
            translated_nodes.append(KeywordNode(name=name_translated, children=translated_children))
            
        return translated_nodes

    async def generate(self, text: str) -> KeywordTreeSummary:
        """
        Основной асинхронный метод для построения двуязычного дерева.
        Входной параметр 'lang' удален. Язык определяется автоматически.
        
        :param text: Исходный текст.
        :return: Объект KeywordTreeSummary с деревьями на RU и EN.
        """
        
        # ШАГ 0: АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ ЯЗЫКА
        source_lang = self._detect_language(text)
        
        # Шаг 1: Извлечение и кластеризация
        phrases = extract_key_phrases(text, lang=source_lang)
        
        clusters = cluster_phrases(phrases, lang=source_lang)
        
        roots_original = build_tree_from_clusters(clusters, lang=source_lang)
        
        # Шаг 3: Перевод дерева
        target_lang = "en" if source_lang == "ru" else "ru"
        roots_translated = await self._translate_tree(roots_original, src=source_lang, tgt=target_lang)
        
        # Шаг 4: Формирование результата (берем только первый корневой узел)
        # Если не найдено ключевых слов, создаем заглушку
        default_node = KeywordNode(name="No keywords found", children=[])
        
        if source_lang == "ru":
            ru_tree = roots_original if roots_original else [default_node]
            en_tree = roots_translated if roots_translated else [default_node]
        else:
            en_tree = roots_original if roots_original else [default_node]
            ru_tree = roots_translated if roots_translated else [default_node]

        return KeywordTreeSummary(ru=ru_tree, en=en_tree)