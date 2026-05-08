import fitz


def extract_pdf_text(file_path):
    text_parts = []

    with fitz.open(file_path) as doc:
        for page_index, page in enumerate(doc):
            page_text = page.get_text("text") or ""
            if page_text.strip():
                text_parts.append(f"\n\n--- Page {page_index + 1} ---\n\n{page_text}")

    return "\n".join(text_parts).strip()