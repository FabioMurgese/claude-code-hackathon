from src.tools.parse_attachments import parse_attachments


def test_no_attachments_returns_empty():
    result = parse_attachments("CLM-001")
    assert result["claim_id"] == "CLM-001"
    assert result["attachments"] == []
    assert result["text"] == ""


def test_missing_claim_returns_error():
    result = parse_attachments("DOES-NOT-EXIST")
    assert result["isError"] is True
    assert result["code"] == "CLAIM_NOT_FOUND"
