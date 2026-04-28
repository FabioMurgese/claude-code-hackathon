from src.hooks.pre_tool_use import check_pre_tool_use


def test_clean_args_pass():
    assert check_pre_tool_use("fetch_claim", {"claim_id": "CLM-001"}) is None


def test_codice_fiscale_blocked():
    result = check_pre_tool_use("fetch_claim", {"claim_id": "RSSMRA80A01H501Z"})
    assert result is not None
    assert result["code"] == "GDPR_PII_BLOCKED"


def test_iban_blocked():
    result = check_pre_tool_use("write_decision", {"note": "IBAN IT60X0542811101000000123456"})
    assert result is not None
    assert result["code"] == "GDPR_PII_BLOCKED"


def test_external_url_blocked():
    result = check_pre_tool_use("fetch_claim", {"url": "https://evil.com/exfil"})
    assert result is not None
    assert result["code"] == "EXTERNAL_ROUTING_BLOCKED"


def test_frozen_policy_write_blocked():
    result = check_pre_tool_use("write_decision", {"claim_id": "CLM-014", "metadata": {"frozen": True}})
    assert result is not None
    assert result["code"] == "FROZEN_ACCOUNT_BLOCKED"


def test_fraud_approve_blocked():
    result = check_pre_tool_use("write_decision", {"claim_id": "CLM-015", "decision": "fast_track", "fraud_score": 2})
    assert result is not None
    assert result["code"] == "FRAUD_APPROVE_BLOCKED"
