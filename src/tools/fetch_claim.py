"""
Reads summary.txt and metadata.json from data/inbox/<claim_id>/.

Returns raw text content and metadata dict. Does NOT parse PDFs or images
(use parse_attachments for that). Does NOT make coverage decisions.

Error: {"isError": true, "code": "CLAIM_NOT_FOUND", "guidance": "verify claim_id exists in data/inbox/"}

Owner: Person A
"""
