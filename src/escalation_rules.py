"""
Single source of truth for escalation thresholds.

All escalation logic in coordinator.py and harness.py reads from this module.
Change thresholds here only — never inline them elsewhere.

Owner: Person C
"""

AMOUNT_THRESHOLD_EUR: float = 5_000.0
CONFIDENCE_THRESHOLD: float = 0.75


def should_escalate(
    amount_eur: float,
    confidence: float,
    fraud_score: int,
    sanctions_hit: bool,
    coverage_status: str,
    claim_type: str,
) -> tuple[bool, str]:
    """Return (escalate: bool, reason: str)."""
    if amount_eur >= AMOUNT_THRESHOLD_EUR:
        return True, f"amount_eur {amount_eur} >= threshold {AMOUNT_THRESHOLD_EUR}"
    if confidence < CONFIDENCE_THRESHOLD:
        return True, f"confidence {confidence} < threshold {CONFIDENCE_THRESHOLD}"
    if fraud_score > 0:
        return True, f"fraud_score {fraud_score} > 0 (D.Lgs. 231/2001 flag)"
    if sanctions_hit:
        return True, "sanctions_hit: EU/UN sanctions list match"
    if coverage_status == "ambiguous":
        return True, "coverage_status ambiguous: polizza silente sul tipo di evento"
    if claim_type == "contestazione":
        return True, "claim_type contestazione: claimant disputes prior decision"
    return False, ""
