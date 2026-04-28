"""
Extracts text from PDF and image attachments in a claim folder.

Uses PyMuPDF for PDFs and Claude vision for images. Returns raw extracted
text only — does NOT make coverage decisions or interpret content.

If parsing fails, fall back to summary.txt via fetch_claim.

Error: {"isError": true, "code": "PARSE_FAILED", "guidance": "fall back to summary.txt via fetch_claim"}

Owner: Person A
"""
