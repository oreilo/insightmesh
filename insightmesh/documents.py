"""Extract text from supported uploaded documents."""
import io

def extract(filename: str, content: bytes) -> str:
    if len(content) > 8_000_000: raise ValueError("Document exceeds 8 MB")
    extension = filename.lower().rsplit(".", 1)[-1]
    if extension in {"txt", "md", "csv", "json", "jsonl"}:
        return content.decode("utf-8-sig")[:200000]
    if extension == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        if len(reader.pages) > 150: raise ValueError("PDF exceeds 150 pages")
        return "\n".join(page.extract_text() or "" for page in reader.pages)[:200000]
    if extension == "docx":
        from docx import Document
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)[:200000]
    raise ValueError("Supported formats: TXT, MD, CSV, JSON, JSONL, PDF, DOCX")
