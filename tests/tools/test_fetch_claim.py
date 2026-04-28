from src.tools.fetch_claim import fetch_claim


def test_returns_summary_and_metadata():
    result = fetch_claim("CLM-001")
    assert result["claim_id"] == "CLM-001"
    assert "summary_text" in result
    assert isinstance(result["metadata"], dict)
    assert result["metadata"]["policy_id"] == "RCA_auto"


def test_missing_claim_returns_error():
    result = fetch_claim("DOES-NOT-EXIST")
    assert result["isError"] is True
    assert result["code"] == "CLAIM_NOT_FOUND"
    assert "guidance" in result
