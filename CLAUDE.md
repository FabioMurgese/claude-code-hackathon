# Claims Intake Agent — CLAUDE.md

## Project overview
Insurance claims triage agent for the Italian/EU market. Coordinator + 2 specialists.
Built with the Claude Agent SDK (Python). Scenario 5 of the Claude Code Hackathon.

## Conventions
- All monetary amounts are in EUR (€). Never use $ symbols.
- PII fields (Codice Fiscale, Partita IVA, IBAN) must never appear in tool output or logs.
- Every tool must return `{"isError": true, "code": "...", "guidance": "..."}` on failure.
- Each source file has exactly one responsibility. If a file grows past ~150 lines, split it.
- Decision thresholds live in `src/escalation_rules.py`. Change them there, nowhere else.
- Task subagents do NOT inherit coordinator context — always pass context explicitly in the Task prompt.

## Branching
- `main` is always demo-ready. Merge only when a challenge is complete.
- Branch naming: `feat/<challenge-name>` (e.g. `feat/triage-agent`, `feat/guardrails`)

## Running the agent
```bash
pip install -e ".[dev]"
python -m src.agent ingest <claim_id>        # process one claim
python evals/run_evals.py                    # run full eval suite
python scripts/build_presentation.py         # assemble presentation.html
```

## Data directories
- `data/inbox/` — 15 development fixtures. Do not use for eval scoring.
- `data/eval/` — eval dataset, tagged eval-baseline-v1. Never edit after tagging.
- `data/decisions/` — agent writes decision JSON here at runtime (gitignored).
- `data/escalations/` — human review queue (gitignored).
- `data/policies/` — 5 mock Italian policy JSON files.

## Key decisions log
Every non-obvious architectural choice is documented in a `## Key Decision` section
in the relevant file. `scripts/build_presentation.py` extracts these automatically
into the presentation. Write yours as you go — do not reconstruct at the end.
