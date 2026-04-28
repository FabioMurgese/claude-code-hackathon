import json
from datetime import datetime, timezone
from pathlib import Path

from src.validator import validate_decision as _validate

DECISIONS_PATH = Path("data/decisions")

WRITE_DECISION_SCHEMA = {
    "name": "write_decision",
    "description": (
        "Writes the final decision record to data/decisions/<claim_id>.json. "
        "Required fields: claim_id, decision (fast_track|investigate|deny|auto_resolve), "
        "category, confidence (0.0–1.0), rationale. "
        "Does NOT handle escalations — call escalate_claim for those. "
        "Does NOT write to frozen polizze (blocked by PreToolUse hook). "
        "Does NOT approve claims with fraud_score > 0 (blocked by PreToolUse hook). "
        "Example: write_decision(claim_id='CLM-001', decision='fast_track', "
        "category='sinistro_auto', confidence=0.9, rationale='...')"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["fast_track", "investigate", "deny", "auto_resolve"]},
            "category": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "rationale": {"type": "string"},
            "retry_count": {"type": "integer", "default": 0},
        },
        "required": ["claim_id", "decision", "category", "confidence", "rationale"],
    },
}


def write_decision(
    claim_id: str, decision: str, category: str,
    confidence: float, rationale: str, retry_count: int = 0,
) -> dict:
    record = {
        "claim_id": claim_id, "decision": decision, "category": category,
        "confidence": confidence, "rationale": rationale, "retry_count": retry_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    is_valid, error = _validate(record)
    if not is_valid:
        return {"isError": True, "code": "SCHEMA_INVALID", "guidance": error}
    DECISIONS_PATH.mkdir(parents=True, exist_ok=True)
    (DECISIONS_PATH / f"{claim_id}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return record
