import re
from collections import Counter
from nltk.tokenize import sent_tokenize
from .utils import fix_glued_words, get_stopwords

class ClassicalSummarizer:
    def __init__(self, prefer_sentence_len: int = 15):
        self.prefer_sentence_len = prefer_sentence_len

    def summarize(self, text: str, lang: str = "en", summary_size: int = 6) -> str:
        if not text or not text.strip():
            return "Текст пуст."
        text = fix_glued_words(text)
        try:
            sentences = sent_tokenize(text, language="russian" if lang=="ru" else "english")
        except Exception:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not sentences:
            return "Не удалось разделить текст на предложения."
        sw = get_stopwords(lang)
        words = [w.lower() for w in re.findall(r"\b\w+\b", text, flags=re.UNICODE) if w.lower() not in sw]
        if not words:
            return "В тексте не найдено значимых слов."
        freq = Counter(words)
        maxf = max(freq.values())
        for k in freq:
            freq[k] /= maxf
        scored = []
        for i, s in enumerate(sentences):
            s_words = [w.lower() for w in re.findall(r"\b\w+\b", s, flags=re.UNICODE)]
            score = sum(freq.get(w,0) for w in s_words)
            pos_bonus = (len(sentences) - i) / len(sentences)
            length_penalty = min(1.3, max(0.7, 1.0 - abs(len(s_words)-self.prefer_sentence_len)/50.0))
            scored.append((score * pos_bonus * length_penalty, s, i))
        top = sorted(scored, key=lambda x: x[0], reverse=True)[:summary_size]
        top_sorted = sorted(top, key=lambda x: x[2])
        summary = "\n".join([s for _,s,_ in top_sorted])
        return f"{summary}"
