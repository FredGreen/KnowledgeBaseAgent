"""Document parsers: extract text from various file formats."""

from ...infra.logging import logger


def parse_pdf(file_path: str) -> list[dict]:
    """Parse PDF, return list of {text, page}."""
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"text": text, "page": i + 1})
    logger.info("Parsed PDF %s: %d pages", file_path, len(pages))
    return pages


def parse_docx(file_path: str) -> list[dict]:
    """Parse DOCX, return list of {text, page}."""
    from docx import Document
    doc = Document(file_path)
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if full_text.strip():
        return [{"text": full_text, "page": 1}]
    return []


def parse_txt(file_path: str) -> list[dict]:
    """Parse plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    if text.strip():
        return [{"text": text, "page": 1}]
    return []


def parse_md(file_path: str) -> list[dict]:
    """Parse Markdown file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    if text.strip():
        return [{"text": text, "page": 1}]
    return []


def parse_csv(file_path: str) -> list[dict]:
    """Parse CSV file into text blocks."""
    import pandas as pd
    df = pd.read_csv(file_path)
    texts = []
    for _, row in df.iterrows():
        row_text = " | ".join(f"{col}: {val}" for col, val in row.items() if pd.notna(val))
        if row_text.strip():
            texts.append(row_text)
    combined = "\n".join(texts)
    if combined.strip():
        return [{"text": combined, "page": 1}]
    return []


def parse_xlsx(file_path: str) -> list[dict]:
    """Parse Excel file into text blocks."""
    import pandas as pd
    xls = pd.ExcelFile(file_path)
    all_text = []
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        all_text.append(f"[Sheet: {sheet_name}]")
        for _, row in df.iterrows():
            row_text = " | ".join(f"{col}: {val}" for col, val in row.items() if pd.notna(val))
            if row_text.strip():
                all_text.append(row_text)
    combined = "\n".join(all_text)
    if combined.strip():
        return [{"text": combined, "page": 1}]
    return []


def parse_json(file_path: str) -> list[dict]:
    """Parse JSON file into text blocks."""
    import json
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def _flatten(obj, prefix=""):
        texts = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                texts.extend(_flatten(v, f"{prefix}{k}: "))
        elif isinstance(obj, list):
            for item in obj:
                texts.extend(_flatten(item, prefix))
        else:
            texts.append(f"{prefix}{obj}")
        return texts

    texts = _flatten(data)
    combined = "\n".join(texts)
    if combined.strip():
        return [{"text": combined, "page": 1}]
    return []


def parse_url(url: str) -> list[dict]:
    """Fetch and parse URL content (P1 feature)."""
    import requests
    from bs4 import BeautifulSoup
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    if text.strip():
        return [{"text": text, "page": 1}]
    return []


PARSERS = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".txt": parse_txt,
    ".md": parse_md,
    ".csv": parse_csv,
    ".xlsx": parse_xlsx,
    ".json": parse_json,
}

SUPPORTED_EXTENSIONS = set(PARSERS.keys())


def parse_document(file_path: str) -> list[dict]:
    """Parse a document by file extension, return list of {text, page}."""
    import os
    ext = os.path.splitext(file_path)[1].lower()
    parser = PARSERS.get(ext)
    if parser is None:
        raise ValueError(f"Unsupported file type: {ext}")
    return parser(file_path)


def parse_file(file_path: str, file_type: str) -> list[dict]:
    """Parse a file by its type extension. Returns list of {text, page}."""
    parser = PARSERS.get(file_type)
    if not parser:
        raise ValueError(f"Unsupported file type: {file_type}")
    return parser(file_path)
