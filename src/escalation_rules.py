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
    decision: str = "",
) -> tuple[bool, str]:
    """Return (escalate: bool, reason: str).

    Amount alone does NOT escalate when the coordinator already decided 'investigate' —
    that decision already routes the claim for human review. Escalation on amount fires
    only when the coordinator tries to fast_track or deny a high-value claim, which
    would bypass the review step entirely.
    """
    # Amount: only override fast_track — investigate and deny are already deliberate decisions
    if amount_eur >= AMOUNT_THRESHOLD_EUR and decision not in ("investigate", "deny"):
        return True, f"amount_eur {amount_eur} >= threshold {AMOUNT_THRESHOLD_EUR}"
    if confidence < CONFIDENCE_THRESHOLD:
        return True, f"confidence {confidence} < threshold {CONFIDENCE_THRESHOLD}"
    # score=1 = AML proximity (high amount) → investigate, score>=2 = confirmed fraud → escalate
    if fraud_score >= 2:
        return True, f"fraud_score {fraud_score} >= 2 (confirmed fraud flag, D.Lgs. 231/2001)"
    if sanctions_hit:
        return True, "sanctions_hit: EU/UN sanctions list match"
    # Ambiguous coverage is expected for investigate decisions — only escalate fast_track/deny
    if coverage_status == "ambiguous" and decision != "investigate":
        return True, "coverage_status ambiguous: polizza silente sul tipo di evento"
    if claim_type == "contestazione":
        return True, "claim_type contestazione: claimant disputes prior decision"
    return False, ""
