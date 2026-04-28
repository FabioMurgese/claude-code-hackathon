import pytest
from evals.harness import compute_metrics

_RESULTS = [
    {"claim_id": "E1", "expected": "fast_track",  "actual": "fast_track",  "confidence": 0.90, "adversarial": False},
    {"claim_id": "E2", "expected": "deny",         "actual": "deny",         "confidence": 0.85, "adversarial": False},
    {"claim_id": "E3", "expected": "fast_track",   "actual": "investigate",  "confidence": 0.95, "adversarial": False},
    {"claim_id": "A1", "expected": "investigate",  "actual": "investigate",  "confidence": 0.80, "adversarial": True},
    {"claim_id": "A2", "expected": "deny",         "actual": "fast_track",   "confidence": 0.60, "adversarial": True},
]


def test_accuracy():
    assert compute_metrics(_RESULTS)["accuracy"] == pytest.approx(3 / 5)


def test_adversarial_pass_rate():
    assert compute_metrics(_RESULTS)["adversarial_pass_rate"] == pytest.approx(1 / 2)


def test_false_confidence_rate():
    # E3: confidence 0.95, wrong → 1 false-conf out of 5 total (NOT out of wrong count)
    assert compute_metrics(_RESULTS)["false_confidence_rate"] == pytest.approx(1 / 5)


def test_precision_fast_track():
    m = compute_metrics(_RESULTS)
    # fast_track predicted for E1 (correct) and A2 (wrong expected=deny) → 1/2
    assert m["precision_per_category"]["fast_track"] == pytest.approx(1 / 2)
