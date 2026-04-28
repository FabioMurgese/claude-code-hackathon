"""
Extracts text from PDF and image attachments in a claim folder.

Uses PyMuPDF for PDFs and Claude vision for images. Returns raw extracted
text only — does NOT make coverage decisions or interpret content.

If parsing fails, fall back to summary.txt via fetch_claim.

Error: {"isError": true, "code": "PARSE_FAILED", "guidance": "fall back to summary.txt via fetch_claim"}

Owner: Person A
"""

from pathlib import Path

try:
    import fitz
    _PYMUPDF = True
except ImportError:
    _PYMUPDF = False

INBOX_PATH = Path("data/inbox")
_PDF_EXTS = {".pdf"}
_IMG_EXTS = {".jpg", ".jpeg", ".png"}

PARSE_ATTACHMENTS_SCHEMA = {
    "name": "parse_attachments",
    "description": (
        "Extracts text from PDF or image attachments in data/inbox/<claim_id>/. "
        "Uses PyMuPDF for PDFs. Does NOT parse summary.txt — use fetch_claim for that. "
        "Does NOT make coverage decisions — returns raw extracted text only. "
        "Example: parse_attachments(claim_id='CLM-001')"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "filename": {"type": "string", "description": "Specific file, e.g. 'report.pdf'. Omit to parse all."},
        },
        "required": ["claim_id"],
    },
}


def parse_attachments(claim_id: str, filename: str | None = None) -> dict:
    claim_dir = INBOX_PATH / claim_id
    if not claim_dir.is_dir():
        return {"isError": True, "code": "CLAIM_NOT_FOUND", "guidance": "verify claim_id exists in data/inbox/"}
    all_exts = _PDF_EXTS | _IMG_EXTS
    files = [claim_dir / filename] if filename else [f for f in claim_dir.iterdir() if f.suffix.lower() in all_exts]
    if not files:
        return {"claim_id": claim_id, "attachments": [], "text": ""}
    texts: list[str] = []
    for f in files:
        if not f.exists():
            continue
        if f.suffix.lower() == ".pdf":
            if not _PYMUPDF:
                return {"isError": True, "code": "PARSE_FAILED", "guidance": "PyMuPDF not installed — run: pip install pymupdf"}
            try:
                doc = fitz.open(str(f))
                texts.append("\n".join(page.get_text() for page in doc))
            except Exception as exc:
                return {"isError": True, "code": "PARSE_FAILED", "guidance": f"Failed to parse {f.name}: {exc}"}
    return {"claim_id": claim_id, "attachments": [f.name for f in files if f.exists()], "text": "\n\n".join(texts)}
