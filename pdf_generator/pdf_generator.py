import json
import os
from pathlib import Path

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def _font_paths():
    base_dir = Path(__file__).resolve().parent.parent
    return (
        base_dir / "fonts" / "arial.ttf",
        base_dir / "fonts" / "arialbd.ttf",
    )


def draw_question_with_options(c, question, y_position, margin, width, font_regular, font_bold):
    """Render a single question with its options and return updated y position."""
    c.setFont(font_bold, 10)
    question_text = f"{question['id']}. {question['text']}"

    if question.get("img"):
        question_text += " (Vezi imaginea)"

    lines = []
    words = question_text.split()
    current_line = ""
    max_width = width - 2 * margin - 1 * cm

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font_bold, 11) < max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    for line in lines:
        c.drawString(margin, y_position, line)
        y_position -= 0.6 * cm

    y_position -= 0.3 * cm

    c.setFont(font_regular, 10)
    for i, option in enumerate(question.get("options", [])):
        letter = chr(65 + i)

        circle_x = margin + 0.5 * cm
        c.circle(circle_x, y_position + 0.15 * cm, 0.25 * cm, stroke=1, fill=0)

        c.setFont(font_bold, 9)
        text_width = c.stringWidth(letter, font_bold, 9)
        c.drawString(circle_x - text_width / 2, y_position + 0.05 * cm, letter)

        c.setFont(font_regular, 10)
        c.drawString(margin + 1.5 * cm, y_position, option)

        y_position -= 0.7 * cm

    y_position -= 0.5 * cm

    return y_position


def _register_fonts():
    regular_path, bold_path = _font_paths()
    pdfmetrics.registerFont(TTFont("Arial", str(regular_path)))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(bold_path)))
    return "Arial", "Arial-Bold"


def generate_test_pdf(json_file, output_pdf):
    """Generate a printable test PDF (cover sheet, bubbles, and questions)."""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    font_regular, font_bold = _register_fonts()
    num_answers = data.get("num_answers") or 0

    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    margin = 2 * cm

    y_position = height - margin

    c.setFont(font_bold, 18)
    c.drawString(margin, y_position, data.get("title", ""))

    qr = qrcode.make(data.get("id", ""))
    qr_dir = Path(output_pdf).resolve().parent
    qr_dir.mkdir(parents=True, exist_ok=True)
    qr_path = qr_dir / f"qr_{data.get('id', 'test')}.png"
    qr.save(qr_path)
    c.drawImage(str(qr_path), 350, 650, width=150, height=150)
    qr_path.unlink(missing_ok=True)

    y_position -= 1.5 * cm

    c.setFont(font_regular, 11)
    c.drawString(margin, y_position, "Nume: ________________________________")

    y_position -= 2 * cm
    c.drawString(margin, y_position, "Prenume: _____________________________")
    y_position -= 2 * cm

    row_height = 1 * cm
    box_height = (data.get("num_questions", 0) * row_height + 0.3 * cm)

    x_start = margin + 2 * cm
    circle_spacing = 1.2 * cm

    rect_width = (num_answers * circle_spacing) + 0.2 * cm

    c.rect(x_start - 0.7 * cm, y_position - box_height - 0.3 * cm, rect_width, box_height)

    c.setFont(font_bold, 10)
    for i in range(num_answers):
        letter = chr(65 + i)
        x_pos = x_start + (i * circle_spacing)
        text_width = c.stringWidth(letter, font_bold, 10)
        c.drawString(x_pos - text_width / 2, y_position + 0.1 * cm, letter)

    y_position -= 0.8 * cm

    for question in data.get("questions", []):
        q_id = question.get("id")

        c.setFont(font_regular, 10)
        c.drawString(margin + 0.5 * cm, y_position - 0.1 * cm, f"{q_id}.")

        for i in range(num_answers):
            x_pos = x_start + (i * circle_spacing)
            c.circle(x_pos, y_position, 0.3 * cm, stroke=1, fill=0)

        y_position -= row_height

    c.showPage()

    y_position = height - margin

    c.setFont(font_bold, 14)
    c.drawString(margin, y_position, f"{data.get('title', '')} - Varianta {data.get('varianta', 1)}")
    y_position -= 1.5 * cm

    c.line(margin, y_position, width - margin, y_position)
    y_position -= 1 * cm

    for question in data.get("questions", []):
        if y_position < margin + 1 * cm:
            c.showPage()
            y_position = height - margin

            c.setFont(font_bold, 14)
            c.drawString(margin, y_position, f"{data.get('title', '')} - Varianta {data.get('varianta', 1)}")
            y_position -= 1.5 * cm
            c.line(margin, y_position, width - margin, y_position)
            y_position -= 1 * cm

        y_position = draw_question_with_options(c, question, y_position, margin, width, font_regular, font_bold)

    c.save()
    return output_pdf
