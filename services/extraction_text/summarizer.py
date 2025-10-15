import re
from collections import Counter
from nltk.tokenize import sent_tokenize
from .utils import fix_glued_words, get_stopwords

class ClassicalSummarizer:
    """
    Классический суммаризатор текста на основе частотного анализа слов.
    """
    def __init__(self, prefer_sentence_len: int = 15):
        """
        Инициализация суммаризатора.
        :param prefer_sentence_len: предпочитаемая длина предложения (для учета при оценке предложений)
        """
        self.prefer_sentence_len = prefer_sentence_len

    def summarize(self, text: str, lang: str = "en", summary_size: int = 6) -> str:
        """
        Создает краткое содержание текста.
        :param text: исходный текст
        :param lang: язык текста ("en" или "ru")
        :param summary_size: количество предложений в итоговом резюме
        :return: строка с кратким содержанием текста
        """
        # Проверяем, что текст не пустой
        if not text or not text.strip():
            return "Текст пуст."
        
        # Исправляем "слитные" слова, если такие есть
        text = fix_glued_words(text)
        
        # Разделяем текст на предложения
        try:
            # Используем nltk для токенизации предложений
            sentences = sent_tokenize(text, language="russian" if lang=="ru" else "english")
        except Exception:
            # Если токенизация не сработала, делим вручную по точкам, восклицательным и вопросительным знакам
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        
        if not sentences:
            return "Не удалось разделить текст на предложения."
        
        # Получаем стоп-слова для выбранного языка
        sw = get_stopwords(lang)
        
        # Создаем список значимых слов текста (без стоп-слов, в нижнем регистре)
        words = [w.lower() for w in re.findall(r"\b\w+\b", text, flags=re.UNICODE) if w.lower() not in sw]
        
        if not words:
            return "В тексте не найдено значимых слов."
        
        # Подсчитываем частоты слов
        freq = Counter(words)
        
        # Нормализуем частоты, деля на максимальное значение
        maxf = max(freq.values())
        for k in freq:
            freq[k] /= maxf
        
        scored = []
        # Оцениваем каждое предложение
        for i, s in enumerate(sentences):
            # Получаем слова предложения
            s_words = [w.lower() for w in re.findall(r"\b\w+\b", s, flags=re.UNICODE)]
            
            # Сумма частот слов в предложении — основной балл
            score = sum(freq.get(w,0) for w in s_words)
            
            # Бонус за позицию предложения (предложения в начале текста могут быть важнее)
            pos_bonus = (len(sentences) - i) / len(sentences)
            
            
            # Штраф или бонус за длину предложения
            # length_penalty оценивает, насколько длина предложения близка к prefer_sentence_len
            # Формула:
            #   1. Вычисляем абсолютное отклонение длины предложения от предпочитаемой длины:
            #        abs(len(s_words) - self.prefer_sentence_len)
            #      - len(s_words) — количество слов в текущем предложении
            #      - self.prefer_sentence_len — оптимальная длина предложения (например, 15 слов)
            #      - abs(...) — абсолютная величина отклонения
            #
            #   2. Преобразуем отклонение в коэффициент, уменьшающий значение предложения:
            #        1.0 - abs(len(s_words) - self.prefer_sentence_len) / 50.0
            #      - Делим отклонение на 50, чтобы смягчить эффект (чем больше отклонение, тем ниже коэффициент)
            #      - Вычитаем из 1.0, чтобы предложения, близкие к оптимальной длине, имели коэффициент около 1.0
            #      - Пример:
            #          * Если длина предложения = 15 слов, prefer_sentence_len = 15 → abs(15-15)/50 = 0 → коэффициент = 1.0
            #          * Если длина = 20 слов → abs(20-15)/50 = 5/50 = 0.1 → коэффициент = 0.9
            #          * Если длина = 40 слов → abs(40-15)/50 = 25/50 = 0.5 → коэффициент = 0.5
            #
            #   3. Ограничиваем минимальный и максимальный предел коэффициента:
            #        max(0.7, ...) — коэффициент не меньше 0.7, чтобы длинные или короткие предложения не были слишком сильно наказаны
            #        min(1.3, ...) — коэффициент не больше 1.3, чтобы слишком удачные предложения не получили слишком высокий бонус
            #
            # Итог: length_penalty — это корректирующий коэффициент, который слегка понижает балл слишком коротких/длинных предложений
            # и слегка повышает балл предложений, близких к prefer_sentence_len.
            length_penalty = min(1.3, max(0.7, 1.0 - abs(len(s_words)-self.prefer_sentence_len)/50.0))
            
            # Итоговый балл предложения с учетом позиции и длины
            scored.append((score * pos_bonus * length_penalty, s, i))
        
        # Выбираем топ N предложений с наибольшим баллом
        top = sorted(scored, key=lambda x: x[0], reverse=True)[:summary_size]
        
        # Сортируем выбранные предложения по их оригинальному порядку в тексте
        top_sorted = sorted(top, key=lambda x: x[2])
        
        # Собираем итоговое резюме
        summary = "\n".join([s for _,s,_ in top_sorted])
        
        return f"{summary}"
