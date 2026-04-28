from src.tools.lookup_policy import lookup_policy


def test_returns_policy_dict():
    result = lookup_policy("RCA_auto")
    assert result["policy_id"] == "RCA_auto"
    assert "max_coverage_eur" in result
    assert "exclusions" in result


def test_missing_returns_error():
    result = lookup_policy("NONEXISTENT")
    assert result["isError"] is True
    assert result["code"] == "POLICY_NOT_FOUND"
    assert "guidance" in result
