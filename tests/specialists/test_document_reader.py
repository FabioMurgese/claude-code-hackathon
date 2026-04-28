import json
from unittest.mock import patch
from src.specialists.document_reader import run_document_reader

_MOCK_SUMMARY = {
    "claim_id": "CLM-001", "summary_text": "Tamponamento lieve.", "amount_eur": 800.0,
    "claim_type": "sinistro_auto", "claimant_id": "CLT-001",
    "numero_sinistro": "NS-2024-001", "incident_date": "2024-11-10",
    "policy_id": "RCA_auto", "frozen": False, "in_contenzioso": False,
}


def test_returns_parsed_claim_summary():
    with patch("src.specialists.document_reader.run_agent_loop",
               return_value=json.dumps(_MOCK_SUMMARY)):
        result = run_document_reader("CLM-001")
    assert result["claim_id"] == "CLM-001"
    assert result["amount_eur"] == 800.0
    assert result["claim_type"] == "sinistro_auto"
