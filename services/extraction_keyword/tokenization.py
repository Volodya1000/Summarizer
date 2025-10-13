# tokenization.py

import re
from typing import List, Tuple
from .config import USE_SPACY, USE_PYMORPHY, nlp_ru, nlp_en, morph, STOP_WORDS_RU, STOP_WORDS_EN

def normalize_text(s: str) -> str:
    """Приводит текст к нижнему регистру, удаляет пунктуацию и нормализует пробелы."""
    s = s.lower()
    s = re.sub(r'[^\w\s\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def spacy_core_tokens(phrase: str, lang: str) -> Tuple[List[str], List[str]]:
    """Токенизация и лемматизация с использованием spaCy."""
    # Заглушка, если spaCy не импортирован или не настроен
    if not (nlp_ru or nlp_en):
        return simple_core_tokens(phrase, lang)

    doc = nlp_ru(phrase) if lang == "ru" else nlp_en(phrase)
    lemmas, poses = [], []
    for token in doc:
        if token.is_stop or token.is_punct or not token.lemma_:
            continue
        lem = token.lemma_.strip().lower()
        pos = token.pos_
        if lem and lem not in lemmas:
            lemmas.append(lem)
            poses.append(pos)
    return lemmas, poses

def pymorphy_core_tokens(phrase: str) -> Tuple[List[str], List[str]]:
    """Токенизация и лемматизация с использованием pymorphy2 (только для RU)."""
    # Заглушка, если pymorphy2 не импортирован
    if not morph:
        return simple_core_tokens(phrase, "ru")
        
    toks, poses = [], []
    for w in normalize_text(phrase).split():
        if w in STOP_WORDS_RU:
            continue
        parsed = morph.parse(w)
        if not parsed:
            continue
        p = parsed[0]
        if p.normal_form not in toks:
            toks.append(p.normal_form)
            poses.append(p.tag.POS or "X")
    return toks, poses

def simple_core_tokens(phrase: str, lang: str) -> Tuple[List[str], List[str]]:
    """Простая токенизация: удаление стоп-слов и дубликатов."""
    toks, poses = [], []
    stop_words = STOP_WORDS_RU if lang == "ru" else STOP_WORDS_EN
    for w in normalize_text(phrase).split():
        if w in stop_words:
            continue
        if w not in toks:
            toks.append(w)
            poses.append("X") # Неизвестная/универсальная POS-метка
    return toks, poses

def core_tokens_with_pos(phrase: str, lang: str) -> Tuple[List[str], List[str]]:
    """Основная функция для получения лемм/токенов и POS-меток."""
    if USE_SPACY:
        return spacy_core_tokens(phrase, lang)
    if USE_PYMORPHY and lang == "ru":
        return pymorphy_core_tokens(phrase)
    return simple_core_tokens(phrase, lang)