# services/report_service.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from models import TextDocumentDTO, KeywordNode
import os

class ReportService:
    """Генератор PDF отчёта по документу и его summary."""

    async def generate_pdf(self, doc: TextDocumentDTO) -> bytes:
        buffer = io.BytesIO()
        doc_pdf = SimpleDocTemplate(buffer, pagesize=A4)

        # --- Подключаем шрифт, поддерживающий кириллицу ---
        font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
        if not os.path.exists(font_path):
            raise FileNotFoundError("Шрифт DejaVuSans.ttf не найден в папке services/")
        pdfmetrics.registerFont(TTFont("DejaVu", font_path))

        # --- Стиль для текста ---
        styles = getSampleStyleSheet()
        normal = ParagraphStyle('NormalUTF8', parent=styles['Normal'], fontName="DejaVu")
        title_style = ParagraphStyle('TitleUTF8', parent=styles['Title'], fontName="DejaVu")
        subtitle = ParagraphStyle('SubtitleUTF8', parent=styles['Heading2'], fontName="DejaVu")

        elements = []

        # --- Заголовок документа ---
        elements.append(Paragraph(f"Документ: {doc.name or doc.file_name}", title_style))
        elements.append(Paragraph(f"Создан: {doc.created_at}", normal))
        elements.append(Spacer(1, 0.5*cm))

        # --- Оригинальный текст ---
        elements.append(Paragraph("Оригинальный текст:", subtitle))
        elements.append(Paragraph(doc.original_text or "(пусто)", normal))
        elements.append(PageBreak())

        # --- Текстовые summary ---
        for summary_attr, label in [
            ("llm_text_summary", "LLM Text Summary"),
            ("extraction_text_summary", "Extraction Text Summary")
        ]:
            summary = getattr(doc.summary, summary_attr)
            elements.append(Paragraph(f"{label} (RU):", subtitle))
            elements.append(Paragraph(summary.ru or "(нет)", normal))
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(f"{label} (EN):", subtitle))
            elements.append(Paragraph(summary.en or "(нет)", normal))
            elements.append(PageBreak())

        # --- Рекурсивная функция для отображения ключевых слов с отступами ---
        def render_keywords_tree_paragraphs(nodes: list[KeywordNode], style, level=0):
            elems = []
            indent = 0.5 * cm * level
            for node in nodes:
                elems.append(
                    Paragraph(
                        f"• {node.name}",
                        ParagraphStyle(
                            name=f"KW_Level_{level}",
                            parent=style,
                            leftIndent=indent
                        )
                    )
                )
                if node.children:
                    # Важно использовать extend с распаковкой, чтобы не добавлять вложенный список как элемент
                    child_elems = render_keywords_tree_paragraphs(node.children, style, level + 1)
                    elems.extend(child_elems)  # правильно
            return elems


        # --- Keywords ---
        for keyword_attr, label in [
            ("llm_keyword_summary", "LLM Keywords"),
            ("extraction_keyword_summary", "Extraction Keywords")
        ]:
            kw_summary = getattr(doc.summary, keyword_attr)
            for lang, lang_label in [("ru", "RU"), ("en", "EN")]:
                elements.append(Paragraph(f"{label} {lang_label}:", subtitle))
                kw_nodes = getattr(kw_summary, lang)
                kw_elements = render_keywords_tree_paragraphs(kw_nodes, normal)
                elements.extend(kw_elements) 
                elements.append(PageBreak())

        # --- Генерация PDF ---
        doc_pdf.build(elements)
        buffer.seek(0)
        return buffer.read()
