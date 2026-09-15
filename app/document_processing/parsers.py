from io import BytesIO
from pathlib import Path


class DocumentParser:
    supported = {".txt", ".md", ".docx", ".pdf"}

    def parse(self, filename: str, data: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix not in self.supported:
            raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")
        if suffix in {".txt", ".md"}:
            return data.decode("utf-8", errors="replace")
        if suffix == ".docx":
            from docx import Document as DocxDocument

            return "\n".join(p.text for p in DocxDocument(BytesIO(data)).paragraphs if p.text.strip())
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + size)
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            end = boundary if boundary > start else end
        chunks.append(normalized[start:end].strip())
        if end == len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks
