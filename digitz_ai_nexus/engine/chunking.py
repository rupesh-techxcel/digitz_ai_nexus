import re


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_text_into_chunks(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> list[str]:
    """
    Simple Phase 1 chunking:
    - Splits by paragraphs first
    - Merges paragraphs up to chunk_size
    - Adds light overlap from previous chunk
    """

    text = normalize_text(text)

    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        if not current:
            current = paragraph
            continue

        if len(current) + len(paragraph) + 2 <= chunk_size:
            current += "\n\n" + paragraph
        else:
            chunks.append(current.strip())

            overlap_text = current[-chunk_overlap:].strip() if chunk_overlap else ""
            current = f"{overlap_text}\n\n{paragraph}".strip() if overlap_text else paragraph

    if current:
        chunks.append(current.strip())

    return chunks