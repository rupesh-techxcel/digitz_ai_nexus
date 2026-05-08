def extract_txt_text(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()