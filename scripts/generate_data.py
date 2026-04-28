"""
Generates synthetic Italian insurance claims using the Claude API.

Usage:
    python scripts/generate_data.py --target inbox --count 15
    python scripts/generate_data.py --target eval --count 60

--target inbox  → writes 15 claim folders to data/inbox/ (dev fixtures)
--target eval   → writes 40 normal.jsonl + 20 adversarial.jsonl to data/eval/

Claims are realistic Italian-market scenarios:
  RCA auto, incendio casa, infortuni, RC professionale, polizza vita.

Each inbox claim folder contains:
  summary.txt   (voicemail transcript or adjuster notes in Italian)
  metadata.json (policy_id, amount_eur, claim_type, claimant_id, frozen)

Each eval JSONL line contains:
  id, text, policy_id, expected_decision, category, notes

After generating eval data, run:
  git tag eval-baseline-v1
Never edit data/eval/ after tagging.

Owner: Person C
"""
