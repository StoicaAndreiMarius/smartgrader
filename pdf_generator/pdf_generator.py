import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def draw_question_with_options(c, question, y_position, margin, width, font_regular, font_bold):

    c.setFont(font_bold, 10)
    question_text = f"{question['id']}. {question['text']}"

    if question['img']:
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
    for i, option in enumerate(question['options']):
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


def generate_test_pdf(json_file, output_pdf):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    num_answers = data['num_answers']
    pdfmetrics.registerFont(TTFont('Arial', '../fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', '../fonts/arialbd.ttf'))
    font_regular = 'Arial'
    font_bold = 'Arial-Bold'


    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    margin = 2 * cm

    y_position = height - margin

    c.setFont(font_bold, 18)
    c.drawString(margin, y_position, data['title'])

    c.setFont(font_bold, 14)
    c.drawString(margin + 10 * cm, y_position, f"Varianta:     {data['varianta']}")

    y_position -= 1.5 * cm

    c.setFont(font_regular, 11)
    c.drawString(margin, y_position, "Nume: ________________________________")

    y_position -= 2 * cm
    c.drawString(margin, y_position, "Prenume: _____________________________")
    y_position -= 2 * cm

    row_height = 0.8 * cm
    box_height = (data['num_questions'] * row_height + 0.3*cm)
    
    # Define starting position for circles (closer to numbers)
    x_start = margin + 2 * cm
    circle_spacing = 1.2 * cm
    
    # Calculate rectangle width based on number of answers
    rect_width = (num_answers * circle_spacing) + 0.2*cm
    
    # Draw the rectangle (moved closer to numbers)
    c.rect(x_start - 0.7*cm, y_position - box_height - 0.3*cm, rect_width, box_height)
    
    # Draw letters above the rectangle, aligned with circles
    c.setFont(font_bold, 10)
    for i in range(num_answers):
        letter = chr(65 + i)
        x_pos = x_start + (i * circle_spacing)
        text_width = c.stringWidth(letter, font_bold, 10)
        c.drawString(x_pos - text_width / 2, y_position + 0.1 * cm, letter)

    y_position -= 0.8 * cm

    # Draw question numbers and circles
    for question in data['questions']:
        q_id = question['id']

        c.setFont(font_regular, 10)
        c.drawString(margin + 0.5 * cm, y_position - 0.1 * cm, f"{q_id}.")

        # Draw circles (without letters inside)
        for i in range(num_answers):
            x_pos = x_start + (i * circle_spacing)
            c.circle(x_pos, y_position, 0.3 * cm, stroke=1, fill=0)

        y_position -= row_height

    c.showPage()

    y_position = height - margin

    c.setFont(font_bold, 14)
    c.drawString(margin, y_position, f"{data['title']} - Varianta {data['varianta']}")
    y_position -= 1.5 * cm

    c.line(margin, y_position, width - margin, y_position)
    y_position -= 1 * cm

    for question in data['questions']:
        if y_position < margin + 8 * cm:
            c.showPage()
            y_position = height - margin

            c.setFont(font_bold, 14)
            c.drawString(margin, y_position, f"{data['title']} - Varianta {data['varianta']}")
            y_position -= 1.5 * cm
            c.line(margin, y_position, width - margin, y_position)
            y_position -= 1 * cm

        y_position = draw_question_with_options(c, question, y_position, margin, width, font_regular, font_bold)

    c.save()
    print(f"PDF generat cu succes: {output_pdf}")


if __name__ == "__main__":
    generate_test_pdf('question.json', 'test_output.pdf')