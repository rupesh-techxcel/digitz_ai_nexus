def chunk_text(text, chunk_size=650, overlap=100):
    if not text:
        return []

    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = max(end - overlap, start + 1)

    return chunks