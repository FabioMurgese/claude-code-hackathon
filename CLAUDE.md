# Claims Intake Agent — CLAUDE.md

## Project overview
Insurance claims triage agent for the Italian/EU market. Coordinator + 2 specialists.
Built with Python · LangGraph · AWS Bedrock. Scenario 5 of the Claude Code Hackathon.

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

## Stack
- Agent framework: **LangGraph** (`StateGraph`) via `langchain-aws` + `ChatBedrockConverse`
- AWS Bedrock inference profile: `eu.anthropic.claude-sonnet-4-6` (set in `src/agent/graph_utils.py`)
- Credentials: AWS CLI (`aws login`), loaded from environment. No `ANTHROPIC_API_KEY` needed.

## Running the agent
```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
aws login && source .env                     # AWS credentials + GITHUB_PAT
.venv/bin/python -m src.agent ingest <claim_id>        # process one claim
.venv/bin/python evals/run_evals.py                    # run full eval suite
.venv/bin/python scripts/build_presentation.py         # assemble presentation.html
```

## Data directories
- `data/inbox/` — 15 dev fixtures (CLM-001..015) + 60 eval fixtures (SIN-EVAL-*, EVAL-A-*). Do not use eval folders for debugging.
- `data/eval/` — 40 normal + 20 adversarial labeled claims. Tagged `eval-baseline-v1`.
- `data/decisions/` — agent writes decision JSON here at runtime (gitignored).
- `data/escalations/` — human review queue (gitignored).
- `data/policies/` — 5 mock Italian policy JSON files (RCA_auto, incendio_casa, infortuni, RC_professionale, polizza_vita).

## Key decisions log
Every non-obvious architectural choice is documented in a `## Key Decision` section
in the relevant file. `scripts/build_presentation.py` extracts these automatically
into the presentation. Write yours as you go — do not reconstruct at the end.
