from docx import Document


def extract_docx_text(file_path):
    doc = Document(file_path)
    parts = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)

    return "\n".join(parts).strip()