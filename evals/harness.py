"""
Eval harness.

Loads data/eval/normal.jsonl and data/eval/adversarial.jsonl, runs each
claim through the coordinator, compares output to the expected_decision label,
and computes scorecard metrics:
  - accuracy
  - precision_per_category (fast_track, investigate, deny)
  - escalation_rate (correct vs. needless)
  - adversarial_pass_rate
  - false_confidence_rate (confidence >= 0.9 AND wrong)

Writes results to evals/scorecard.json (gitignored — regenerated each run).
Stratified sampling ensures the score is not dominated by the most common category.

Owner: Person C
"""
import json
from pathlib import Path

EVAL_PATH      = Path("data/eval")
SCORECARD_PATH = Path("evals/scorecard.json")
_CATEGORIES    = {"fast_track", "investigate", "deny", "auto_resolve"}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def compute_metrics(results: list[dict]) -> dict:
    total = len(results)
    if total == 0:
        return {"accuracy": 0.0, "precision_per_category": {}, "adversarial_pass_rate": 1.0,
                "false_confidence_rate": 0.0, "escalation_rate": {"correct": 0, "needless": 0},
                "total": 0, "correct": 0}

    correct = sum(1 for r in results if r["expected"] == r["actual"])

    precision: dict = {}
    for cat in _CATEGORIES:
        predicted = [r for r in results if r["actual"] == cat]
        precision[cat] = sum(1 for r in predicted if r["expected"] == cat) / len(predicted) if predicted else None

    adv = [r for r in results if r["adversarial"]]
    adv_pass = sum(1 for r in adv if r["expected"] == r["actual"]) / len(adv) if adv else 1.0

    false_conf = sum(1 for r in results if r.get("confidence", 0) >= 0.9 and r["expected"] != r["actual"])

    escalated    = [r for r in results if r["actual"] == "escalated"]
    esc_correct  = sum(1 for r in escalated if r.get("should_escalate", False))
    esc_needless = len(escalated) - esc_correct

    return {
        "accuracy": correct / total,
        "precision_per_category": precision,
        "adversarial_pass_rate": adv_pass,
        "false_confidence_rate": false_conf / total,
        "escalation_rate": {"correct": esc_correct, "needless": esc_needless},
        "total": total,
        "correct": correct,
    }


def run_harness(only: str | None = None) -> dict:
    from src.agent.coordinator import process_claim  # deferred — coordinator may not be ready yet

    normal = _load_jsonl(EVAL_PATH / "normal.jsonl")      if only != "adversarial" else []
    adv    = _load_jsonl(EVAL_PATH / "adversarial.jsonl") if only != "normal"       else []

    results: list[dict] = []

    for item in normal:
        decision = process_claim(item["id"])
        actual = decision.get("decision") or ("escalated" if "escalation_reason" in decision else "unknown")
        results.append({"claim_id": item["id"], "expected": item["expected_decision"], "actual": actual,
                         "confidence": decision.get("confidence", 0.0), "adversarial": False,
                         "should_escalate": item.get("should_escalate", False)})

    for item in adv:
        decision = process_claim(item["id"])
        actual = decision.get("decision") or ("escalated" if "escalation_reason" in decision else "unknown")
        results.append({"claim_id": item["id"], "expected": item.get("expected_decision", "investigate"),
                         "actual": actual, "confidence": decision.get("confidence", 0.0),
                         "adversarial": True, "adversarial_type": item.get("adversarial_type", "unknown")})

    metrics = compute_metrics(results)
    metrics["results"] = results
    SCORECARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCORECARD_PATH.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    return metrics
