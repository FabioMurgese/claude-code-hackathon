CHECK_FRAUD_SCHEMA = {
    "name": "check_fraud_flags",
    "description": (
        "Checks claimant_id and incident details against D.Lgs. 231/2001 mock fraud rules. "
        "Returns fraud_score (0 = clean, >0 = flag present) and triggered_rules list. "
        "Does NOT access Codice Fiscale, Partita IVA, or IBAN — those are blocked by the PreToolUse hook. "
        "Does NOT make the final fraud determination — only returns signals for the coordinator. "
        "Example: check_fraud_flags(claimant_id='CLT-001', incident_date='2024-11-10', amount_eur=800.0)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "claimant_id": {"type": "string", "description": "Opaque claimant ID (not Codice Fiscale)"},
            "incident_date": {"type": "string", "description": "Incident date YYYY-MM-DD"},
            "amount_eur": {"type": "number", "description": "Claimed amount in EUR"},
        },
        "required": ["claimant_id", "incident_date", "amount_eur"],
    },
}

_KNOWN_FRAUD = {"CLT-FRAUD-001", "CLT-FRAUD-002"}
_AML_THRESHOLD = 9_000.0  # D.Lgs. 231/2001 AML reporting proximity threshold


def check_fraud_flags(claimant_id: str, incident_date: str, amount_eur: float) -> dict:
    triggered: list[str] = []
    score = 0
    if claimant_id in _KNOWN_FRAUD:
        triggered.append("known_fraud_claimant")
        score += 2
    if amount_eur >= _AML_THRESHOLD:
        triggered.append("high_amount_aml_threshold")
        score += 1
    return {"claimant_id": claimant_id, "fraud_score": score, "triggered_rules": triggered}
