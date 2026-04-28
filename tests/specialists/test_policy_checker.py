import json
from unittest.mock import patch
from src.specialists.policy_checker import run_policy_checker

_CLAIM = {
    "claim_id": "CLM-001", "summary_text": "Tamponamento lieve.", "amount_eur": 800.0,
    "claim_type": "sinistro_auto", "claimant_id": "CLT-001",
    "numero_sinistro": "NS-2024-001", "incident_date": "2024-11-10",
    "policy_id": "RCA_auto", "frozen": False, "in_contenzioso": False,
}
_MOCK_RESULT = {
    "coverage_status": "covered", "fraud_score": 0, "triggered_rules": [],
    "sanctions_hit": False, "exclusions_matched": [], "policy_valid": True,
}


def test_returns_policy_result():
    with patch("src.specialists.policy_checker.run_agent_loop", return_value=json.dumps(_MOCK_RESULT)):
        result = run_policy_checker(_CLAIM)
    assert result["coverage_status"] == "covered"
    assert result["fraud_score"] == 0
    assert result["sanctions_hit"] is False
