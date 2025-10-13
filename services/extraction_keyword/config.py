# config.py

import nltk
from nltk.corpus import stopwords
import logging

# Настройки для YAKE
YAKE_TOP_K = 40

# Настройки для кластеризации/построения дерева
MERGE_THRESH = 0.3
SOFT_JACCARD_ATTACH = 0.18
MIN_CORE_NOUNS = 1 # Не используется в текущей реализации, но оставлено для полноты

# Настройки для токенизации
USE_SPACY = False # Если True, нужно установить spaCy и модели ru/en
USE_PYMORPHY = False # Если True, нужно установить pymorphy2
nlp_ru = nlp_en = None
morph = None

# Настройка логирования для argostranslate
logger = logging.getLogger(__name__)

# Стоп-слова (используем NLTK, нужно скачать)
try:
    nltk.download('stopwords', quiet=True)
    STOP_WORDS_RU = set(stopwords.words('russian'))
    STOP_WORDS_EN = set(stopwords.words('english'))
except LookupError:
    print("NLTK 'stopwords' not downloaded. Please run: nltk.download('stopwords')")
    STOP_WORDS_RU = set()
    STOP_WORDS_EN = set()