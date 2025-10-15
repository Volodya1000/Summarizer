import argostranslate.translate
import argostranslate.package

def ensure_argos_pair(src: str, tgt: str) -> bool:
    """Проверка наличия установленной пары src→tgt и ее установка, если отсутствует."""
    try:
        langs = argostranslate.translate.get_installed_languages()
        from_lang = next((l for l in langs if l.code == src), None)
        to_lang = next((l for l in langs if l.code == tgt), None)
        if from_lang and to_lang and from_lang.get_translation(to_lang):
            return True
    except Exception:
        pass # Игнорируем и пробуем установить

    try:
        argostranslate.package.update_package_index()
        avail = argostranslate.package.get_available_packages()
        pkg = next((p for p in avail if p.from_code == src and p.to_code == tgt), None)
        if not pkg:
            return False
        pkg_path = pkg.download()
        argostranslate.package.install_from_path(pkg_path)
        return True
    except Exception as e:
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
            return phrase
            
        try:
            return argostranslate.translate.translate(phrase, src, tgt)
        except Exception as e:
            return phrase