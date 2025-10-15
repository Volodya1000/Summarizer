# clustering.py
import yake
from typing import List, Dict
from .tokenization import core_tokens_with_pos, normalize_text
from .metrics import jaccard
from .config import YAKE_TOP_K, MERGE_THRESH, STOP_WORDS_RU, STOP_WORDS_EN


'''
Принцип работы:

Извлечение ключевых фраз
Функция extract_key_phrases использует YAKE, чтобы из текста выделить важные слова и словосочетания (ключевые фразы).

Подготовка к кластеризации
Каждая фраза превращается в «кластер из одного элемента».
Для каждой фразы:

Определяются токены (слова в нормальной форме) и их части речи.

Создается ядро кластера — множество токенов (core_set) и упорядоченный список токенов (core_list).

Объединение кластеров (жадное)
Пока есть пары кластеров с высокой схожестью (метрика Жаккарда):

Находим пару кластеров с максимальной схожестью.

Объединяем их фразы и ядро:

Если есть общие токены — они становятся новым ядром.

Если общих токенов нет — берем несколько самых частых токенов.

Пересчитываем части речи для нового ядра.

Финализация кластеров
После объединений для каждого кластера:

Если ядро пустое — берутся первые несколько «важных» слов из фраз.

Определяется имя кластера: обычно существительное из ядра, иначе первый токен, иначе самая короткая фраза.

Кластер сохраняется с фразами, ядром и именем

'''
def extract_key_phrases(text: str, lang: str, top_k: int=YAKE_TOP_K) -> List[str]:
    """
    Извлекает ключевые фразы из текста с помощью YAKE.
    
    Args:
        text: исходный текст
        lang: язык текста ("ru" или "en")
        top_k: сколько ключевых фраз возвращать (по умолчанию YAKE_TOP_K)
    
    Returns:
        Список ключевых фраз
    """
    # Инициализация YAKE для выбранного языка, с n-граммами до 4 слов
    # dedupLim=0.9 означает, что похожие ключевые фразы считаются дубликатами
    kw_extractor = yake.KeywordExtractor(lan=lang, n=4, top=top_k, dedupLim=0.9)
    kws = kw_extractor.extract_keywords(text)
    # Возвращаем только сами ключевые слова (без оценки)
    return [kw[0] for kw in kws]


def cluster_phrases(phrases: List[str], merge_thresh: float=MERGE_THRESH, lang: str="ru") -> List[Dict]:
    """
    Кластеризация фраз на основе схожести их "ядра" (core tokens) с использованием метрики Жаккарда.
    
    Args:
        phrases: список фраз для кластеризации
        merge_thresh: порог схожести для объединения кластеров
        lang: язык текста ("ru" или "en")
    
    Returns:
        Список кластеров, где каждый кластер содержит:
            - name: имя кластера
            - members: индексы фраз, входящих в кластер
            - core_set: множество ключевых токенов кластера
            - core_list: упорядоченный список токенов кластера
            - core_pos: части речи токенов
            - phrases: фразы кластера
    """
    
    # Инициализация каждого элемента как отдельного кластера
    items = []
    for i, p in enumerate(phrases):
        lemmas, poses = core_tokens_with_pos(p, lang)  # лемматизация и POS-теги
        core_set = set(lemmas)  # множество уникальных токенов
        items.append({
            "members": {i},          # индекс исходной фразы
            "phrases": [p],          # сама фраза
            "core_list": lemmas,     # упорядоченный список токенов
            "core_pos": poses,       # части речи
            "core_set": core_set     # множество токенов
        })

    def best_pair(items_list):
        """
        Находит пару кластеров с наибольшей схожестью по Жаккарду.
        """
        best = (None, None, -1.0)
        n = len(items_list)
        for i in range(n):
            for j in range(i + 1, n):
                score = jaccard(items_list[i]["core_set"], items_list[j]["core_set"])
                if score > best[2]:
                    best = (i, j, score)
        return best

    # Кластеризация: жадное объединение пар с наибольшей схожестью
    items_list = items.copy()
    while True:
        i, j, score = best_pair(items_list)
        if score < merge_thresh or i is None:
            break  # если схожесть ниже порога, завершить

        A, B = items_list[i], items_list[j]
        
        # Объединяем члены и фразы двух кластеров
        new_members = A["members"] | B["members"]
        new_phrases = A["phrases"] + B["phrases"]
        
        inter = list(A["core_set"].intersection(B["core_set"]))
        
        if inter:
            # Если есть общие токены — формируем новое ядро из них в порядке появления
            combined = []
            for token in A["core_list"] + B["core_list"]:
                if token in inter and token not in combined:
                    combined.append(token)
            new_core_list = combined
            new_core_set = set(new_core_list)
        else:
            # Если общих токенов нет — берем 3 наиболее частых токена из объединения
            union_tokens = list(A["core_list"] + B["core_list"])
            freq = {}
            for t in union_tokens:
                freq[t] = freq.get(t, 0) + 1
            # сортировка по убыванию частоты и оригинальному порядку
            sorted_by_freq = sorted(freq.keys(), key=lambda x: (-freq[x], union_tokens.index(x)))
            new_core_list = sorted_by_freq[:3] 
            new_core_set = set(new_core_list)

        # Пересчет POS-тегов для нового ядра
        new_core_pos = []
        for t in new_core_list:
            pos = None
            if t in A["core_list"]:
                pos = A["core_pos"][A["core_list"].index(t)]
            elif t in B["core_list"]:
                pos = B["core_pos"][B["core_list"].index(t)]
            new_core_pos.append(pos or "X")  # X — неизвестная часть речи

        # Формируем новый кластер
        new_item = {
            "members": new_members, "phrases": new_phrases,
            "core_list": new_core_list, "core_pos": new_core_pos, "core_set": new_core_set
        }

        # Удаляем старые кластеры и добавляем новый
        items_list = [it for k, it in enumerate(items_list) if k not in (i, j)]
        items_list.append(new_item)

    # Финализация кластеров: определяем имя и ядро
    clusters = []
    for it in items_list:
        core_list = it["core_list"]
        core_set = it["core_set"]
        core_pos = it.get("core_pos", [])
        phrases_in_cluster = it["phrases"]
        
        # Если ядро пустое — берем первые 3 не-стоп слова из фраз
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

        # Выбираем имя кластера
        name = None
        for tok, pos in zip(core_list, core_pos):
            # Ищем существительное
            if pos and pos.upper().startswith(("NOUN", "PROPN", "N")):
                name = tok
                break
        
        if not name and core_list:
            name = core_list[0]  # если существительного нет — берем первый токен
        
        if not name:
            name = min(phrases_in_cluster, key=lambda s: len(s))  # иначе самая короткая фраза

        clusters.append({
            "name": name,
            "members": it["members"],
            "core_set": core_set,
            "core_list": core_list,
            "core_pos": core_pos,
            "phrases": phrases_in_cluster
        })
    return clusters
