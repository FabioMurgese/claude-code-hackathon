from src.tools.check_fraud_flags import check_fraud_flags
from src.tools.check_sanctions import check_sanctions


def test_clean_claimant_zero_score():
    result = check_fraud_flags("CLT-001", "2024-11-10", 800.0)
    assert result["fraud_score"] == 0
    assert result["triggered_rules"] == []


def test_known_fraud_claimant_flagged():
    result = check_fraud_flags("CLT-FRAUD-001", "2024-11-05", 500.0)
    assert result["fraud_score"] > 0
    assert "known_fraud_claimant" in result["triggered_rules"]


def test_high_amount_triggers_aml():
    result = check_fraud_flags("CLT-001", "2024-11-10", 9500.0)
    assert "high_amount_aml_threshold" in result["triggered_rules"]


def test_clean_claimant_not_sanctioned():
    assert check_sanctions("CLT-001")["sanctions_hit"] is False


def test_sanctioned_claimant_hit():
    result = check_sanctions("CLT-SANCTIONED-001")
    assert result["sanctions_hit"] is True
    assert result["list"] is not None
