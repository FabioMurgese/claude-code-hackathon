import src.tools.write_decision as wd
import src.tools.escalate_claim as ec
from src.tools.write_decision import write_decision
from src.tools.escalate_claim import escalate_claim


def test_write_decision_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "DECISIONS_PATH", tmp_path / "decisions")
    result = write_decision(
        claim_id="CLM-001", decision="fast_track", category="sinistro_auto",
        confidence=0.92, rationale="Copertura chiara, importo sotto soglia."
    )
    assert result["decision"] == "fast_track"
    assert (tmp_path / "decisions" / "CLM-001.json").exists()


def test_write_decision_invalid_returns_error():
    result = write_decision(claim_id="CLM-001", decision="NOT_VALID",
                            category="x", confidence=0.5, rationale="test")
    assert result["isError"] is True
    assert result["code"] == "SCHEMA_INVALID"


def test_escalate_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ec, "ESCALATIONS_PATH", tmp_path / "escalations")
    result = escalate_claim(claim_id="CLM-010", escalation_reason="amount >= 5000")
    assert result["status"] == "pending_human_review"
    assert (tmp_path / "escalations" / "CLM-010.json").exists()
