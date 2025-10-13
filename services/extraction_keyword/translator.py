# translator.py

import argostranslate.translate
import argostranslate.package
import logging
from .config import logger # Используем настроенный логгер из config

def ensure_argos_pair(src: str, tgt: str) -> bool:
    """Проверка наличия установленной пары src→tgt и ее установка, если отсутствует."""
    try:
        langs = argostranslate.translate.get_installed_languages()
        from_lang = next((l for l in langs if l.code == src), None)
        to_lang = next((l for l in langs if l.code == tgt), None)
        if from_lang and to_lang and from_lang.get_translation(to_lang):
            logger.info("Пара %s→%s уже установлена.", src, tgt)
            return True
    except Exception:
        pass # Игнорируем и пробуем установить

    try:
        logger.info("Пытаемся установить пакет перевода %s→%s...", src, tgt)
        argostranslate.package.update_package_index()
        avail = argostranslate.package.get_available_packages()
        pkg = next((p for p in avail if p.from_code == src and p.to_code == tgt), None)
        if not pkg:
            logger.warning("Пакет %s→%s не найден в доступных.", src, tgt)
            return False
        pkg_path = pkg.download()
        argostranslate.package.install_from_path(pkg_path)
        logger.info("Пакет %s→%s успешно установлен.", src, tgt)
        return True
    except Exception as e:
        logger.error("Ошибка при установке пакета %s→%s: %s", src, tgt, e)
        return False


class LocalTranslator:
    """Локальный переводчик, использующий argos-translate."""
    def __init__(self):
        # Проверяем и устанавливаем необходимые пары
        self.ru_en_ok = ensure_argos_pair("ru", "en")
        self.en_ru_ok = ensure_argos_pair("en", "ru")

    def translate(self, phrase: str, src: str, tgt: str) -> str:
        """Выполняет перевод."""
        if (src == "ru" and tgt == "en" and not self.ru_en_ok) or \
           (src == "en" and tgt == "ru" and not self.en_ru_ok):
            logger.warning("Перевод %s→%s недоступен. Возвращаем исходную фразу.", src, tgt)
            return phrase
            
        try:
            return argostranslate.translate.translate(phrase, src, tgt)
        except Exception as e:
            logger.error("Ошибка во время перевода '%s' (%s→%s): %s", phrase, src, tgt, e)
            return phrase