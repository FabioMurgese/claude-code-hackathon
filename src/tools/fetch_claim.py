import json
from pathlib import Path

INBOX_PATH = Path("data/inbox")

FETCH_CLAIM_SCHEMA = {
    "name": "fetch_claim",
    "description": (
        "Reads summary.txt and metadata.json from data/inbox/<claim_id>/. "
        "Returns claim text and a metadata dict with policy_id, amount_eur, claim_type, claimant_id, frozen. "
        "Does NOT parse PDFs or images — use parse_attachments for binary attachments. "
        "Does NOT make coverage decisions. "
        "Example: fetch_claim(claim_id='CLM-001')"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "claim_id": {"type": "string", "description": "Folder name under data/inbox/, e.g. 'CLM-001'"}
        },
        "required": ["claim_id"],
    },
}


def fetch_claim(claim_id: str) -> dict:
    claim_dir = INBOX_PATH / claim_id
    if not claim_dir.is_dir():
        return {"isError": True, "code": "CLAIM_NOT_FOUND",
                "guidance": "verify claim_id exists in data/inbox/"}
    summary_text = (
        (claim_dir / "summary.txt").read_text(encoding="utf-8")
        if (claim_dir / "summary.txt").exists() else ""
    )
    metadata = (
        json.loads((claim_dir / "metadata.json").read_text(encoding="utf-8"))
        if (claim_dir / "metadata.json").exists() else {}
    )
    return {"claim_id": claim_id, "summary_text": summary_text, "metadata": metadata}
