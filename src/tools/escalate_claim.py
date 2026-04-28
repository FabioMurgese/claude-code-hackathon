"""
Writes an escalation record to data/escalations/<claim_id>.json for human review.

Call when should_escalate() returns True, or on max_tokens stop_reason.
Does NOT make the final decision.
Does NOT override a human decision once made.

Error: {"isError": true, "code": "ESCALATION_FAILED", "guidance": "..."}

Owner: Person A
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ESCALATIONS_PATH = Path("data/escalations")

ESCALATE_CLAIM_SCHEMA = {
    "name": "escalate_claim",
    "description": (
        "Writes an escalation record to data/escalations/<claim_id>.json for human review. "
        "Call when should_escalate() returns True, or on max_tokens stop_reason. "
        "Does NOT make the final decision. "
        "Does NOT override a human decision once made. "
        "Example: escalate_claim(claim_id='CLM-010', escalation_reason='amount_eur 6500 >= threshold 5000')"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "escalation_reason": {"type": "string"},
            "decision": {"type": "string", "enum": ["fast_track", "investigate", "deny", "auto_resolve"]},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "rationale": {"type": "string"},
        },
        "required": ["claim_id", "escalation_reason"],
    },
}


def escalate_claim(
    claim_id: str,
    escalation_reason: str,
    decision: str | None = None,
    confidence: float | None = None,
    rationale: str | None = None,
) -> dict:
    record: dict = {
        "claim_id": claim_id,
        "escalation_reason": escalation_reason,
        "status": "pending_human_review",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if decision is not None:
        record["tentative_decision"] = decision
    if confidence is not None:
        record["confidence"] = confidence
    if rationale is not None:
        record["rationale"] = rationale
    ESCALATIONS_PATH.mkdir(parents=True, exist_ok=True)
    (ESCALATIONS_PATH / f"{claim_id}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return record
