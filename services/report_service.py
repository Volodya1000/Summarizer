# services/report_service.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from models import TextDocumentDTO
import os

class ReportService:
    """Генератор PDF отчёта по документу и его summary."""

    async def generate_pdf(self, doc: TextDocumentDTO) -> bytes:
        buffer = io.BytesIO()
        doc_pdf = SimpleDocTemplate(buffer, pagesize=A4)

        # --- Подключаем шрифт, поддерживающий кириллицу ---
        font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")  # путь к ttf
        if not os.path.exists(font_path):
            raise FileNotFoundError("Шрифт DejaVuSans.ttf не найден в папке services/")
        pdfmetrics.registerFont(TTFont("DejaVu", font_path))

        # Стиль с поддержкой кириллицы
        styles = getSampleStyleSheet()
        normal = ParagraphStyle(
            'NormalUTF8',
            parent=styles['Normal'],
            fontName="DejaVu"
        )
        title_style = ParagraphStyle(
            'TitleUTF8',
            parent=styles['Title'],
            fontName="DejaVu"
        )
        subtitle = ParagraphStyle(
            'SubtitleUTF8',
            parent=styles['Heading2'],
            fontName="DejaVu"
        )

        elements = []

        elements.append(Paragraph(f"Документ: {doc.name or doc.file_name}", title_style))
        elements.append(Paragraph(f"Создан: {doc.created_at}", normal))
        elements.append(Spacer(1, 0.5*cm))

        # --- Original text ---
        elements.append(Paragraph("Оригинальный текст:", subtitle))
        elements.append(Paragraph(doc.original_text or "(пусто)", normal))
        elements.append(PageBreak())

        # --- Summaries ---
        elements.append(Paragraph("Резюме и ключевые слова", title_style))

        # LLM Text Summaries
        elements.append(Paragraph("LLM Text Summary (RU):", subtitle))
        elements.append(Paragraph(doc.summary.llm_text_summary.ru or "(нет)", normal))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph("LLM Text Summary (EN):", subtitle))
        elements.append(Paragraph(doc.summary.llm_text_summary.en or "(нет)", normal))
        elements.append(PageBreak())

        # Extraction summaries
        elements.append(Paragraph("Extraction Text Summary (RU):", subtitle))
        elements.append(Paragraph(doc.summary.extraction_text_summary.ru or "(нет)", normal))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph("Extraction Text Summary (EN):", subtitle))
        elements.append(Paragraph(doc.summary.extraction_text_summary.en or "(нет)", normal))
        elements.append(PageBreak())

        # Keywords
        def render_keywords(nodes, level=0):
            if not nodes:
                return ["(нет ключевых слов)"]
            lines = []
            for node in nodes:
                indent = "    " * level  # отступы через пробелы
                lines.append(f"{indent}• {node.name}")
                if node.children:
                    lines.extend(render_keywords(node.children, level + 1))
            return lines

        for lang, title in [("ru", "RU"), ("en", "EN")]:
            elements.append(Paragraph(f"LLM Keywords {title}:", subtitle))
            kw_lines = render_keywords(getattr(doc.summary.llm_keyword_summary, lang))
            for line in kw_lines:
                elements.append(Paragraph(line, normal))
            elements.append(PageBreak())

        doc_pdf.build(elements)
        buffer.seek(0)
        return buffer.read()
