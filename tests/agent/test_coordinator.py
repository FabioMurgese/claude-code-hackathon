import json
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
import src.tools.write_decision as wd
import src.tools.escalate_claim as ec
from src.agent.coordinator import process_claim
from src.agent.graph_utils import MaxTokensError

_DOC = {
    "claim_id": "CLM-001", "summary_text": "Tamponamento lieve.", "amount_eur": 800.0,
    "claim_type": "sinistro_auto", "claimant_id": "CLT-001",
    "numero_sinistro": "NS-2024-001", "incident_date": "2024-11-10",
    "policy_id": "RCA_auto", "frozen": False, "in_contenzioso": False,
}
_POL = {
    "coverage_status": "covered", "fraud_score": 0, "triggered_rules": [],
    "sanctions_hit": False, "exclusions_matched": [], "policy_valid": True,
}
_FAST_JSON = json.dumps({
    "claim_id": "CLM-001", "decision": "fast_track", "category": "sinistro_auto",
    "confidence": 0.95, "rationale": "Copertura chiara, importo sotto soglia.",
})


def _mock_llm(response_json: str):
    llm = MagicMock()
    llm.invoke.return_value = AIMessage(content=response_json)
    return llm


def test_fast_track_decision(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "DECISIONS_PATH", tmp_path / "decisions")
    monkeypatch.setattr(ec, "ESCALATIONS_PATH", tmp_path / "escalations")
    with (
        patch("src.agent.coordinator.run_document_reader", return_value=_DOC),
        patch("src.agent.coordinator.run_policy_checker", return_value=_POL),
        patch("src.agent.coordinator._get_llm", return_value=_mock_llm(_FAST_JSON)),
    ):
        result = process_claim("CLM-001")
    assert result["decision"] == "fast_track"
    assert result["claim_id"] == "CLM-001"
    assert (tmp_path / "decisions" / "CLM-001.json").exists()


def test_high_amount_escalates(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "DECISIONS_PATH", tmp_path / "decisions")
    monkeypatch.setattr(ec, "ESCALATIONS_PATH", tmp_path / "escalations")
    doc_high = {**_DOC, "amount_eur": 8000.0}
    dec_json = json.dumps({
        "claim_id": "CLM-010", "decision": "investigate",
        "category": "sinistro_auto", "confidence": 0.82, "rationale": "Importo alto.",
    })
    with (
        patch("src.agent.coordinator.run_document_reader", return_value=doc_high),
        patch("src.agent.coordinator.run_policy_checker", return_value=_POL),
        patch("src.agent.coordinator._get_llm", return_value=_mock_llm(dec_json)),
    ):
        result = process_claim("CLM-010")
    assert result["status"] == "pending_human_review"
    assert "amount_eur" in result["escalation_reason"]


def test_validation_retry_on_bad_json(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "DECISIONS_PATH", tmp_path / "decisions")
    monkeypatch.setattr(ec, "ESCALATIONS_PATH", tmp_path / "escalations")
    calls = {"n": 0}

    def llm_side_effect(msgs):
        calls["n"] += 1
        if calls["n"] < 3:
            return AIMessage(content="not valid json")
        return AIMessage(content=_FAST_JSON)

    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = llm_side_effect

    with (
        patch("src.agent.coordinator.run_document_reader", return_value=_DOC),
        patch("src.agent.coordinator.run_policy_checker", return_value=_POL),
        patch("src.agent.coordinator._get_llm", return_value=mock_llm),
    ):
        result = process_claim("CLM-001")
    assert result["decision"] == "fast_track"
    assert calls["n"] == 3


def test_max_tokens_escalates(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "DECISIONS_PATH", tmp_path / "decisions")
    monkeypatch.setattr(ec, "ESCALATIONS_PATH", tmp_path / "escalations")
    with (
        patch("src.agent.coordinator.run_document_reader", side_effect=MaxTokensError("truncated")),
    ):
        result = process_claim("CLM-001")
    assert result["status"] == "pending_human_review"
    assert "max_tokens" in result["escalation_reason"]
