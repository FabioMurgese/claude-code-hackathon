CHECK_SANCTIONS_SCHEMA = {
    "name": "check_sanctions",
    "description": (
        "Checks claimant_id against a mock EU/UN consolidated sanctions list. "
        "Returns sanctions_hit (bool) and list name if matched. "
        "Does NOT access Codice Fiscale or IBAN. "
        "Does NOT make coverage decisions — only returns the watchlist result. "
        "Example: check_sanctions(claimant_id='CLT-001')"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "claimant_id": {"type": "string", "description": "Opaque claimant ID (not Codice Fiscale)"},
        },
        "required": ["claimant_id"],
    },
}

_SANCTIONED = {"CLT-SANCTIONED-001"}


def check_sanctions(claimant_id: str) -> dict:
    hit = claimant_id in _SANCTIONED
    return {"claimant_id": claimant_id, "sanctions_hit": hit,
            "list": "EU_CONSOLIDATED" if hit else None}
