"""
Validates coordinator structured output against DecisionSchema.

Returns (is_valid: bool, error_message: str) for use in the validation-retry
loop. The error_message is fed back to Claude on failure so it can correct
the specific field rather than regenerating from scratch.

Owner: Person B
"""

from typing import Literal

VALID_DECISIONS = {"fast_track", "investigate", "deny", "auto_resolve"}


def validate_decision(output: dict) -> tuple[bool, str]:
    """Validate a decision dict against the required schema."""
    required = {"claim_id", "decision", "category", "confidence", "rationale"}
    missing = required - output.keys()
    if missing:
        return False, f"missing required fields: {sorted(missing)}"
    if output["decision"] not in VALID_DECISIONS:
        return False, f"decision must be one of {sorted(VALID_DECISIONS)}, got: {output['decision']!r}"
    if not isinstance(output["confidence"], (int, float)):
        return False, "confidence must be a number between 0.0 and 1.0"
    if not (0.0 <= output["confidence"] <= 1.0):
        return False, f"confidence {output['confidence']} out of range [0.0, 1.0]"
    if not output.get("rationale", "").strip():
        return False, "rationale must be a non-empty string"
    return True, ""
