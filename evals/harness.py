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
