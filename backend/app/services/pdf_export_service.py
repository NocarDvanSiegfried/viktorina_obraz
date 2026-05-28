from io import BytesIO
from pathlib import Path

from fpdf import FPDF

from app.db.models import Question, Quiz

FONT_FAMILY = "DejaVuSans"
FONT_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "fonts" / "DejaVuSans.ttf"
)


def _safe_pdf_text(value: str | None) -> str:
    return value or ""


class QuizPdfExportService:
    def _configure_fonts(self, pdf: FPDF) -> None:
        pdf.add_font(FONT_FAMILY, fname=str(FONT_PATH))

    def build_quiz_pdf(self, quiz: Quiz, questions: list[Question]) -> bytes:
        pdf = FPDF()
        self._configure_fonts(pdf)
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        content_width = 190
        pdf.set_font(FONT_FAMILY, size=14)
        pdf.multi_cell(content_width, 8, _safe_pdf_text(quiz.title or "Quiz"))

        pdf.set_font(FONT_FAMILY, size=10)
        meta = (
            f"Subject: {quiz.subject or '-'} | "
            f"Grade: {quiz.grade or '-'} | "
            f"Difficulty: {quiz.difficulty or '-'}"
        )
        pdf.multi_cell(content_width, 6, _safe_pdf_text(meta))
        pdf.ln(3)

        for index, q in enumerate(questions, start=1):
            pdf.set_font(FONT_FAMILY, size=11)
            pdf.multi_cell(
                content_width,
                7,
                _safe_pdf_text(f"{index}. [{q.question_type}] {q.question_text}"),
            )

            pdf.set_font(FONT_FAMILY, size=10)
            options = q.answers or []
            for option in options:
                marker = "✓" if option in (q.correct_answers or []) else "-"
                pdf.multi_cell(content_width, 6, _safe_pdf_text(f"  {marker} {option}"))

            if q.explanation:
                pdf.multi_cell(
                    content_width,
                    6,
                    _safe_pdf_text(f"  Explanation: {q.explanation}"),
                )

            pdf.ln(2)

        data = bytes(pdf.output(dest="S"))
        buffer = BytesIO(data)
        return buffer.getvalue()


pdf_export_service = QuizPdfExportService()

