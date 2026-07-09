def extract_pdf_text(file_path):
    # Imported lazily so a missing PyMuPDF (fitz) only affects PDF parsing — it must
    # not make this module (and the whole ingestion processor) unimportable, which
    # would otherwise break processing of Manual/TXT/DOCX sources too.
    import fitz

    text_parts = []

    with fitz.open(file_path) as doc:
        for page_index, page in enumerate(doc):
            page_text = page.get_text("text") or ""
            if page_text.strip():
                text_parts.append(f"\n\n--- Page {page_index + 1} ---\n\n{page_text}")

    return "\n".join(text_parts).strip()