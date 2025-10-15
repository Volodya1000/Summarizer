import asyncio
from .summarizer import ClassicalSummarizer
from services.extraction_keyword.translator import LocalTranslator
from models import TextSummary
from .utils import fix_glued_words, detect_language

class ExtractionTextSummaryService:
    def __init__(self, summary_size: int = 6, prefer_sentence_len: int = 15):
        self.summarizer = ClassicalSummarizer(prefer_sentence_len)
        self.translator = LocalTranslator()
        self.summary_size = summary_size

    async def _summarize_in_thread(self, text: str, lang: str) -> str:
        return await asyncio.to_thread(self.summarizer.summarize, text, lang, self.summary_size)

    async def generate(self, text: str) -> TextSummary:
        if not text or not text.strip():
            return TextSummary(ru="Текст пуст.", en="Empty text.")
        text = fix_glued_words(text)
        detected = detect_language(text)
        if detected=="ru":
            ru_text = text
            en_text = self.translator.translate(ru_text,"ru","en")
        else:
            en_text = text
            ru_text = self.translator.translate(en_text,"en","ru")
        ru_text = ru_text or text
        en_text = en_text or text
        ru_summary_task = asyncio.create_task(self._summarize_in_thread(ru_text,"ru"))
        en_summary_task = asyncio.create_task(self._summarize_in_thread(en_text,"en"))
        ru_summary = await ru_summary_task
        en_summary = await en_summary_task
        return TextSummary(ru=ru_summary, en=en_summary)
