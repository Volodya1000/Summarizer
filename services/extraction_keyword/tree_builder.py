# tree_builder.py
from typing import List, Dict, Set
from .tokenization import core_tokens_with_pos, normalize_text
from .metrics import jaccard
from .config import SOFT_JACCARD_ATTACH
from models import KeywordNode

MAX_CHILDREN_PER_NODE = 5  # Максимальное количество детей у одного узла
MIN_TOKENS_IN_NODE = 1     # Минимальное количество токенов, чтобы узел считался значимым

def build_tree_from_clusters(clusters: List[Dict], lang: str = "ru") -> List[KeywordNode]:
    """
    Построение логичного дерева ключевых слов.
    Улучшения:
    - Оставляем только значимые «сильные» узлы (с существительными)
    - Убираем однословные узлы, которые полностью входят в более длинные фразы
    - Слияние узлов по токенам
    - Добавление оригинальных фраз только если они добавляют новые токены
    """
    node_data = []

    # Подготовка кластеров
    for c in clusters:
        core_set: Set[str] = c["core_set"]
        core_pos: List[str] = c.get("core_pos", [])
        strong = any(pos.upper().startswith(("NOUN", "PROPN", "N")) for pos in core_pos if pos)
        node_data.append({
            "name": c["name"],
            "core_set": core_set,
            "core_list": c["core_list"],
            "core_pos": core_pos,
            "phrases": c["phrases"],
            "node": KeywordNode(name=c["name"]),
            "size": len(core_set),
            "strong": strong
        })

    # Сортировка: сначала сильные, потом по размеру ядра (большие → маленькие)
    node_data.sort(key=lambda x: (-x["strong"], -x["size"]))

    is_child = set()

    # 1. Строим иерархию: родитель -> дети (subset по токенам)
    for i, parent in enumerate(node_data):
        if not parent["strong"]:
            continue
        children_count = 0
        for j, child in enumerate(node_data):
            if i == j or j in is_child:
                continue
            # Добавляем child только если он подмножество parent и достаточно значимый
            if (child["core_set"].issubset(parent["core_set"]) and
                child["core_set"] != parent["core_set"] and
                len(child["core_set"]) >= MIN_TOKENS_IN_NODE):
                parent["node"].children.append(child["node"])
                is_child.add(j)
                children_count += 1
            if children_count >= MAX_CHILDREN_PER_NODE:
                break

    # 2. Добавляем оригинальные фразы как дети только с уникальными токенами
    for nd in node_data:
        existing_tokens = set(nd["core_set"])
        for phrase in nd["phrases"]:
            phrase_core, _ = core_tokens_with_pos(phrase, lang)
            phrase_core_set = set(phrase_core)
            new_tokens = phrase_core_set - existing_tokens
            if new_tokens and len(phrase_core_set) >= MIN_TOKENS_IN_NODE:
                nd["node"].children.append(KeywordNode(name=phrase))
                existing_tokens.update(new_tokens)

    # 3. Рекурсивная очистка подмножеств: убираем однословные узлы, полностью включённые в родителя
    def clean_tree(node: KeywordNode):
        filtered_children = []
        for child in node.children:
            # Сравниваем токены родителя и ребёнка
            parent_tokens = set(core_tokens_with_pos(node.name, lang)[0])
            child_tokens = set(core_tokens_with_pos(child.name, lang)[0])
            if child_tokens <= parent_tokens and len(child_tokens) < MIN_TOKENS_IN_NODE:
                continue  # удаляем однословный подмножество
            clean_tree(child)  # рекурсивно чистим детей
            filtered_children.append(child)
        node.children = filtered_children

    roots = [nd["node"] for idx, nd in enumerate(node_data) if idx not in is_child]

    for r in roots:
        clean_tree(r)

    return roots

