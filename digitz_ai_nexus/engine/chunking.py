import re


DEFAULT_MAX_CHARS = 1800
DEFAULT_OVERLAP_CHARS = 250


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_text_into_chunks(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[str]:
    """
    Backward-compatible helper.
    Returns list[str].
    """

    chunks = chunk_text(
        text,
        max_chars=chunk_size,
        overlap_chars=chunk_overlap,
    )

    return [chunk.get("text") for chunk in chunks if chunk.get("text")]


def split_into_blocks(text):
    """
    Paragraph-aware splitter.
    """

    text = normalize_text(text)

    if not text:
        return []

    raw_blocks = re.split(r"\n\s*\n", text)

    blocks = []

    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue

        lines = [line.strip() for line in block.split("\n") if line.strip()]
        normalized = "\n".join(lines).strip()

        if normalized:
            blocks.append(normalized)

    return blocks


def is_heading(block):
    """
    Basic heading detector for ERP/business documents.
    """

    if not block:
        return False

    lines = block.splitlines()

    if len(lines) > 2:
        return False

    text = block.strip()

    if len(text) > 120:
        return False

    if text.endswith(":"):
        return True

    if text.isupper() and len(text.split()) <= 10:
        return True

    heading_keywords = {
        "overview",
        "purpose",
        "scope",
        "workflow",
        "process",
        "configuration",
        "validation",
        "approval",
        "accounting",
        "inventory",
        "payroll",
        "attendance",
        "hire return",
        "valuation",
        "rules",
        "steps",
        "example",
    }

    return text.lower() in heading_keywords


def chunk_text(
    text,
    max_chars=DEFAULT_MAX_CHARS,
    overlap_chars=DEFAULT_OVERLAP_CHARS,
):
    """
    Semantic MVP chunker.

    Returns:
        list[dict]: [{"index": 1, "text": "...", "char_count": 123}]
    """

    text = normalize_text(text)

    if not text:
        return []

    blocks = split_into_blocks(text)

    if not blocks:
        return []

    chunks = []
    current_parts = []
    current_len = 0
    pending_heading = None

    def flush_chunk():
        nonlocal current_parts, current_len

        if not current_parts:
            return

        chunk_body = "\n\n".join(current_parts).strip()

        if chunk_body:
            chunks.append({
                "index": len(chunks) + 1,
                "text": chunk_body,
                "char_count": len(chunk_body),
            })

        current_parts = []
        current_len = 0

    for block in blocks:
        block_len = len(block)

        if is_heading(block):
            pending_heading = block
            continue

        if pending_heading:
            block = f"{pending_heading}\n\n{block}"
            block_len = len(block)
            pending_heading = None

        if block_len > max_chars:
            flush_chunk()
            split_large_block(block, chunks, max_chars, overlap_chars)
            continue

        projected_len = current_len + block_len + 2

        if projected_len > max_chars:
            flush_chunk()

        current_parts.append(block)
        current_len += block_len + 2

    if pending_heading:
        current_parts.append(pending_heading)

    flush_chunk()

    return add_overlap(chunks, overlap_chars)


def split_large_block(block, chunks, max_chars, overlap_chars):
    """
    Splits large paragraphs by sentence first,
    then by character if a sentence is too large.
    """

    sentences = re.split(r"(?<=[.!?])\s+", block.strip())

    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence) > max_chars:
            if current:
                chunks.append({
                    "index": len(chunks) + 1,
                    "text": current.strip(),
                    "char_count": len(current.strip()),
                })
                current = ""

            step = max_chars - overlap_chars
            if step <= 0:
                step = max_chars

            start = 0
            while start < len(sentence):
                part = sentence[start:start + max_chars].strip()
                if part:
                    chunks.append({
                        "index": len(chunks) + 1,
                        "text": part,
                        "char_count": len(part),
                    })
                start += step

            continue

        if len(current) + len(sentence) + 1 > max_chars:
            if current:
                chunks.append({
                    "index": len(chunks) + 1,
                    "text": current.strip(),
                    "char_count": len(current.strip()),
                })
            current = sentence
        else:
            current = f"{current} {sentence}".strip()

    if current:
        chunks.append({
            "index": len(chunks) + 1,
            "text": current.strip(),
            "char_count": len(current.strip()),
        })


def add_overlap(chunks, overlap_chars):
    """
    Adds previous chunk tail as continuity context.
    """

    if not chunks or overlap_chars <= 0:
        return chunks

    enhanced = []
    previous_text = ""

    for idx, chunk in enumerate(chunks, start=1):
        text = chunk.get("text") or ""

        if idx > 1 and previous_text:
            overlap = previous_text[-overlap_chars:].strip()

            if overlap:
                text = f"Previous Context:\n{overlap}\n\nCurrent Content:\n{text}"

        enhanced.append({
            "index": idx,
            "text": text.strip(),
            "char_count": len(text.strip()),
        })

        previous_text = chunk.get("text") or ""

    return enhanced