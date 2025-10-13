# tree_builder.py

from typing import List, Dict
from models import KeywordNode
from .tokenization import core_tokens_with_pos, normalize_text
from .metrics import jaccard
from .config import SOFT_JACCARD_ATTACH

def build_tree_from_clusters(clusters: List[Dict], lang: str="ru") -> List[KeywordNode]:
    """
    Строит иерархическое дерево из кластеров ключевых слов.
    Использует логику 'подмножество' (subset) и 'мягкий Жаккард' (soft Jaccard).
    """
    node_data = []
    for c in clusters:
        core = c["core_set"]
        core_pos = c.get("core_pos", [])
        # 'Сильный' (strong) узел - содержит существительное
        strong = any((pos and pos.upper().startswith(("NOUN", "PROPN", "N"))) for pos in core_pos)
        node = KeywordNode(name=c["name"])
        node_data.append({
            "name": c["name"], "core_set": core, "core_list": c["core_list"],
            "core_pos": core_pos, "phrases": c["phrases"], "node": node,
            "size": len(core), "strong": strong
        })

    # Сортируем для более эффективной иерархии (сначала маленькие, потом не 'сильные')
    node_data.sort(key=lambda x: (x["size"], not x["strong"], x["name"]))

    is_child = set()
    n = len(node_data)
    
    # 1. Строим иерархию по принципу 'подмножество' (core_set.issubset)
    for i, parent in enumerate(node_data):
        for j, child in enumerate(node_data):
            if i == j or j in is_child:
                continue
            # A - подмножество B (A - родитель B)
            if parent["core_set"] and parent["core_set"].issubset(child["core_set"]) and parent["core_set"] != child["core_set"]:
                parent["node"].children.append(child["node"])
                is_child.add(j)

    # 2. Правило для 'сильных' узлов с одним токеном (noun-core)
    for i, parent in enumerate(node_data):
        if parent["size"] == 1 and parent["strong"]:
            token = next(iter(parent["core_set"]))
            for j, child in enumerate(node_data):
                if i == j or j in is_child:
                    continue
                # Если ключевой токен присутствует в какой-либо фразе дочернего кластера
                found_in_phrase = any(token in normalize_text(p) for p in child["phrases"])
                if found_in_phrase and j not in is_child:
                    parent["node"].children.append(child["node"])
                    is_child.add(j)

    # 3. 'Мягкое' присоединение по Жаккарду
    for i, parent in enumerate(node_data):
        for j, child in enumerate(node_data):
            if i == j or j in is_child:
                continue
            if parent["core_set"] and child["core_set"]:
                score = jaccard(parent["core_set"], child["core_set"])
                # Присоединяем, если Жаккард высокий, и родитель меньше дочернего
                if score >= SOFT_JACCARD_ATTACH and parent["size"] < child["size"]:
                    parent["node"].children.append(child["node"])
                    is_child.add(j)

    # Определение корневых узлов
    roots = [nd["node"] for idx, nd in enumerate(node_data) if idx not in is_child]
    final_roots = []
    
    # Постобработка: перенос 'слабых' корневых узлов (без существительных)
    for r in roots:
        nd = next((x for x in node_data if x["node"] is r), None)
        if nd and not nd["strong"]:
            best_score = 0.0
            best_idx = None
            # Ищем самый подходящий 'сильный' узел для поглощения
            for k, cand in enumerate(node_data):
                if cand is nd:
                    continue
                if cand["strong"]:
                    s = jaccard(nd["core_set"], cand["core_set"])
                    if s > best_score:
                        best_score = s
                        best_idx = k
            
            # Если нашли подходящий 'сильный' узел, переносим фразы как его дочерние элементы
            if best_idx is not None and best_score > 0:
                cand_node = node_data[best_idx]["node"]
                for ph in nd["phrases"]:
                    if ph not in {c.name for c in cand_node.children}:
                        cand_node.children.append(KeywordNode(name=ph))
                continue # Не добавляем этот 'слабый' узел в final_roots
        
        final_roots.append(r)
        
    if not final_roots:
        final_roots = roots

    # Добавление оригинальных фраз как дочерних узлов, если их ядро содержит ядро кластера
    for nd in node_data:
        cluster_core = nd["core_set"]
        existing = {c.name for c in nd["node"].children}
        for phrase in nd["phrases"]:
            phrase_core, _ = core_tokens_with_pos(phrase, lang)
            phrase_core_set = set(phrase_core)
            # Фраза является дочерним элементом, если ядро кластера является подмножеством ядра фразы 
            # (и они не идентичны)
            if phrase_core_set and cluster_core and cluster_core.issubset(phrase_core_set) and phrase_core_set != cluster_core:
                if phrase not in existing:
                    nd["node"].children.append(KeywordNode(name=phrase))
                    existing.add(phrase) # Обновляем множество для избежания дубликатов

    return final_roots