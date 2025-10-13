# clustering.py

import yake
from typing import List, Dict
from .tokenization import core_tokens_with_pos, normalize_text
from .metrics import jaccard
from .config import YAKE_TOP_K, MERGE_THRESH, STOP_WORDS_RU, STOP_WORDS_EN

def extract_key_phrases(text: str, lang: str, top_k: int=YAKE_TOP_K) -> List[str]:
    """Извлекает ключевые фразы с использованием YAKE."""
    # YAKE использует код языка ISO 639-1 (ru/en)
    kw_extractor = yake.KeywordExtractor(lan=lang, n=4, top=top_k, dedupLim=0.9)
    kws = kw_extractor.extract_keywords(text)
    return [kw[0] for kw in kws]

def cluster_phrases(phrases: List[str], merge_thresh: float=MERGE_THRESH, lang: str="ru") -> List[Dict]:
    """
    Кластеризует фразы с использованием жадного слияния, основанного на Жаккарде.
    """
    items = []
    for i, p in enumerate(phrases):
        lemmas, poses = core_tokens_with_pos(p, lang)
        core_set = set(lemmas)
        items.append({
            "members": {i},
            "phrases": [p],
            "core_list": lemmas,
            "core_pos": poses,
            "core_set": core_set
        })

    def best_pair(items_list):
        best = (None, None, -1.0)
        n = len(items_list)
        for i in range(n):
            for j in range(i + 1, n):
                score = jaccard(items_list[i]["core_set"], items_list[j]["core_set"])
                if score > best[2]:
                    best = (i, j, score)
        return best

    items_list = items.copy()
    while True:
        i, j, score = best_pair(items_list)
        if score < merge_thresh or i is None:
            break

        A, B = items_list[i], items_list[j]
        
        # Логика объединения:
        new_members = A["members"] | B["members"]
        new_phrases = A["phrases"] + B["phrases"]
        
        inter = list(A["core_set"].intersection(B["core_set"]))
        
        if inter:
            # Общие токены - основа нового кластера
            combined = []
            for token in A["core_list"] + B["core_list"]:
                if token in inter and token not in combined:
                    combined.append(token)
            new_core_list = combined
            new_core_set = set(new_core_list)
        else:
            # Нет общих токенов: берем самые часто встречающиеся (или первые 3 из объединения)
            union_tokens = list(A["core_list"] + B["core_list"])
            freq = {}
            for t in union_tokens:
                freq[t] = freq.get(t, 0) + 1
            # Сортируем по частоте и оригинальному порядку
            sorted_by_freq = sorted(freq.keys(), key=lambda x: (-freq[x], union_tokens.index(x)))
            new_core_list = sorted_by_freq[:3] 
            new_core_set = set(new_core_list)

        # Пересчитываем POS-метки для объединенного core_list
        new_core_pos = []
        for t in new_core_list:
            pos = None
            if t in A["core_list"]:
                pos = A["core_pos"][A["core_list"].index(t)]
            elif t in B["core_list"]:
                pos = B["core_pos"][B["core_list"].index(t)]
            new_core_pos.append(pos or "X")

        new_item = {
            "members": new_members, "phrases": new_phrases,
            "core_list": new_core_list, "core_pos": new_core_pos, "core_set": new_core_set
        }

        # Удаляем старые и добавляем новый
        items_list = [it for k, it in enumerate(items_list) if k not in (i, j)]
        items_list.append(new_item)

    # Финализация кластеров
    clusters = []
    for it in items_list:
        core_list = it["core_list"]
        core_set = it["core_set"]
        core_pos = it.get("core_pos", [])
        phrases_in_cluster = it["phrases"]
        
        # Если ядро пустое, используем не-стоп слова из фраз
        if not core_list:
            tokens = []
            stop_words = STOP_WORDS_RU if lang == "ru" else STOP_WORDS_EN
            for p in phrases_in_cluster:
                for w in normalize_text(p).split():
                    if w not in stop_words and w not in tokens:
                        tokens.append(w)
            core_list = tokens[:3]
            core_set = set(core_list)
            core_pos = ["X"] * len(core_list)

        # Выбираем имя кластера (сначала существительное из ядра, иначе первый токен, иначе самая короткая фраза)
        name = None
        for tok, pos in zip(core_list, core_pos):
            if pos and pos.upper().startswith(("NOUN", "PROPN", "N")):
                name = tok
                break
        
        if not name and core_list:
            name = core_list[0]
        
        if not name:
            name = min(phrases_in_cluster, key=lambda s: len(s))

        clusters.append({
            "name": name,
            "members": it["members"],
            "core_set": core_set,
            "core_list": core_list,
            "core_pos": core_pos,
            "phrases": phrases_in_cluster
        })
    return clusters