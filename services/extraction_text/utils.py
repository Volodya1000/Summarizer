import re
from nltk.corpus import stopwords

MULTIPLE_SPACES_RE = re.compile(r"\s+")

def fix_glued_words(text: str) -> str:
    """
    Исправляет слипшиеся или некорректно разделённые символы в тексте.
    
    Что делает функция:
    1. Убирает лишний пробел перед знаками препинания (например, "слово , " -> "слово,")
    2. Сводит несколько пробелов подряд к одному
    3. Обрезает пробелы в начале и конце текста
    """
    if not text:
        return ""
    t = re.sub(r"\s+([,.;:!?—–])", r"\1", text)
    t = MULTIPLE_SPACES_RE.sub(" ", t)
    return t.strip()

def detect_language(text: str) -> str:
    if not text or not any(ch.isalpha() for ch in text):
        return "en"
    letters = [ch for ch in text if re.match(r"[A-Za-zА-Яа-яЁё]", ch)]
    if not letters:
        return "en"
    cyr = sum(1 for ch in letters if re.match(r"[А-Яа-яЁё]", ch))
    return "ru" if (cyr / len(letters)) > 0.30 else "en"

def get_stopwords(lang: str):
    try:
        return set(stopwords.words("russian" if lang == "ru" else "english"))
    except Exception:
        return set()
