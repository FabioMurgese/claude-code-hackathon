# Team The Insur-gents

## Participants
- Fabio — PM/BA · Architect · Tool implementation · Presentation pipeline
- Luca — Architect · Core agent (coordinator, loop, specialists) · Integration
- Matteo — Quality · Guardrails (PreToolUse hook) · Adversarial eval set · Scorecard

## Scenario
Scenario 5: Agentic Solution — **Insurance Claims Intake Agent (Italian/EU market)**

## What We Built

A production-grade agentic triage system for inbound Italian insurance claims. Claims arrive as folders in `data/inbox/`. The coordinator agent (LangGraph `StateGraph`) dispatches two specialist subagents — DocumentReader and PolicyChecker — with explicit context passing (subagents receive no coordinator memory), validates structured output against a strict schema with a retry loop (max 3 retries, schema error fed back each time), and routes to `fast_track`, `deny`, `auto_resolve`, or `escalate_claim()`. Every decision is written to `data/decisions/` with the full reasoning chain, confidence score, and retry count — replayable from the log alone.

The system is fully adapted for the Italian/EU market: Codice Fiscale and Partita IVA PII patterns, EUR amounts with a €5 000 escalation threshold, D.Lgs. 231/2001 fraud rules, EU/UN sanctions list, and IVASS regulatory framing. A `PreToolUse` hook deterministically blocks PII leakage and fraud-approve attempts before any LLM call — prompt injection cannot bypass it.

**What runs today:** the entire pipeline is end-to-end functional. `python -m src.agent ingest CLM-001` produces a real decision in ~10 seconds via AWS Bedrock Sonnet 4.6. 37 unit tests pass. The eval harness runs 60 labeled claims (40 normal + 20 adversarial) and emits a scored scorecard. The presentation assembles itself from live docs and eval output.

## Architecture

```
Coordinator (LangGraph StateGraph)
  │
  ├─ read_documents → DocumentReader specialist
  │     tools: fetch_claim · parse_attachments
  │     returns: ClaimSummary { claim_id, summary_text, amount_eur,
  │                             claim_type, claimant_id, numero_sinistro,
  │                             incident_date, policy_id, frozen, in_contenzioso }
  │     ⚠ receives no coordinator context — isolated state
  │
  ├─ check_policy → PolicyChecker specialist
  │     tools: lookup_policy · check_fraud_flags · check_sanctions
  │     returns: PolicyResult { coverage_status, fraud_score, triggered_rules,
  │                             sanctions_hit, exclusions_matched, policy_valid }
  │     ⚠ receives ClaimSummary only — not the full coordinator graph state
  │
  ├─ synthesize → Coordinator LLM produces JSON decision
  │     { claim_id, decision, category, confidence, rationale }
  │
  ├─ validate → src/validator.py checks schema
  │     on failure: error fed back to LLM, retry (max 3)
  │     on 3 failures: escalate_claim()
  │
  ├─ check_escalation → src/escalation_rules.py
  │     amount_eur ≥ 5 000   → escalate
  │     confidence < 0.75    → escalate
  │     fraud_score > 0      → escalate
  │     sanctions_hit        → escalate
  │     coverage = ambiguous → escalate
  │     claim_type = contestazione → escalate
  │
  └─ write_decision()   OR   escalate_claim()
       data/decisions/        data/escalations/
```

### Specialists and tools

| Specialist | Tools | Returns |
|---|---|---|
| DocumentReader | `fetch_claim`, `parse_attachments` | `ClaimSummary` |
| PolicyChecker | `lookup_policy`, `check_fraud_flags`, `check_sanctions` | `PolicyResult` |
| Coordinator | `write_decision`, `escalate_claim` | decision record |

All 7 tools return `{"isError": true, "code": "...", "guidance": "..."}` on failure so the agent can recover without parsing raw exceptions.

### Guardrails

**PreToolUse hook (hard stop — deterministic, no LLM):**

| Pattern | Block code |
|---|---|
| Codice Fiscale regex in any tool input | `GDPR_PII_BLOCKED` |
| Partita IVA / IBAN IT pattern | `GDPR_PII_BLOCKED` |
| External URL in tool input | `EXTERNAL_ROUTING_BLOCKED` |
| `write_decision` on `frozen=true` polizza | `FROZEN_ACCOUNT_BLOCKED` |
| `approve` decision + `fraud_score > 0` | `FRAUD_APPROVE_BLOCKED` |

**Escalation rules (slow stop — threshold-based):** all thresholds live in [`src/escalation_rules.py`](src/escalation_rules.py) — single source of truth, never inlined elsewhere.

### Italian/EU market

Codice Fiscale · Partita IVA · IBAN IT · EUR amounts · D.Lgs. 231/2001 fraud rules · EU/UN sanctions list · IVASS regulatory framing · GDPR PII protection — baked in from day one, not retrofitted.

## Challenges Attempted

| # | Challenge | Status | Notes |
|---|---|---|---|
| 1 | The Mandate | ✅ done | [`docs/mandate.md`](docs/mandate.md) — decides alone / escalates / never touches, explicit €5 000 and 0.75 confidence thresholds |
| 2 | The Bones | ✅ done | [`docs/adr/001-agent-arch.md`](docs/adr/001-agent-arch.md) — coordinator + 2 specialists, stop_reason dispatch, explicit context passing |
| 3 | The Tools | ✅ done | 7 tools in [`src/tools/`](src/tools/) — fetch_claim, lookup_policy, check_fraud_flags, check_sanctions, write_decision, escalate_claim, parse_attachments. All tested. |
| 4 | The Triage | ✅ done | LangGraph coordinator in [`src/agent/coordinator.py`](src/agent/coordinator.py) — read_documents → check_policy → synthesize → validate (retry ≤ 3) → check_escalation. Reasoning chain logged per decision. |
| 5 | The Brake | ✅ done | [`src/hooks/pre_tool_use.py`](src/hooks/pre_tool_use.py) — hard stops for PII, frozen accounts, fraud approve, external URLs. [`src/escalation_rules.py`](src/escalation_rules.py) deterministic thresholds. |
| 6 | The Attack | ✅ done | 20 adversarial claims in [`data/eval/adversarial.jsonl`](data/eval/adversarial.jsonl): prompt_injection×6, fraud_indicator×4, coverage_ambiguity×3, false_urgency×3, hidden_complexity×2, pii_exfil_attempt×2. |
| 7 | The Scorecard | ✅ done | [`evals/harness.py`](evals/harness.py) + [`evals/run_evals.py`](evals/run_evals.py) — accuracy, precision/category, adversarial-pass rate, false-confidence rate. CI exits with code 1 on threshold failure. 4 unit tests. |
| 8 | The Loop | skipped | Out of time scope. |

## Key Decisions

**Coordinator + specialist split** — DocumentReader and PolicyChecker are separate subagents, not one agent with all tools. This isolates document parsing failures from policy reasoning failures and keeps each specialist under the 4–5 tool reliability ceiling. See [ADR 001](docs/adr/001-agent-arch.md).

**Explicit thresholds, not vague guidance** — Escalation rules use `amount_eur >= 5000` and `confidence < 0.75`, not "when the agent isn't sure." This makes the eval harness deterministic (correct vs. needless escalations are unambiguous) and gives Legal a defensible audit trail under IVASS.

**PreToolUse hook as a hard stop** — PII blocking is not a prompt instruction; it is a regex hook that fires before the LLM ever sees the tool input. Prompt injection cannot bypass it. Escalation rules are the slow stop; the hook is the hard stop.

**Local inbox, no HTTP endpoint** — Claims arrive as folders in `data/inbox/`. This keeps the demo reproducible, lets judges inspect every input, and keeps the hackathon scope on the agent rather than the ingestion plumbing.

**Italian/EU market from day one** — Codice Fiscale and Partita IVA PII patterns, IVASS regulation, D.Lgs. 231/2001 fraud rules, and EUR amounts are baked into the mandate, tools, hook patterns, and synthetic data generator — not retrofitted.

## How to Run It

```bash
# 1. Create virtual env and install (Python 3.11+ required)
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# 2. Authenticate with AWS (Bedrock Sonnet 4.6 — no Anthropic API key needed)
aws login
cp .env.example .env    # fill in GITHUB_PERSONAL_ACCESS_TOKEN
source .env

# 3. Run all 37 unit tests
.venv/bin/pytest tests/ -v

# 4. Process individual claims
.venv/bin/python -m src.agent ingest CLM-001   # fast_track expected
.venv/bin/python -m src.agent ingest CLM-010   # escalation expected (€6 500)
.venv/bin/python -m src.agent ingest CLM-014   # escalation expected (frozen polizza)

# 5. Run the full eval harness (60 claims — takes ~5 min)
.venv/bin/python evals/run_evals.py            # exits 1 if CI thresholds fail

# 6. Rebuild presentation with live scorecard
.venv/bin/python scripts/build_presentation.py
```

AWS Bedrock credentials required (`aws login`). Model: `eu.anthropic.claude-sonnet-4-6` (EU inference profile).

## If We Had More Time

1. **Challenge 8 — The Loop** — when a human overrides a decision, the signal should flow to a labeled-example store that feeds the adversarial eval set and few-shot examples for the coordinator classifier. The scaffolding (`data/escalations/`) is in place; the feedback wiring is not.
2. **Improve false-confidence rate** — currently 18.3% (target ≤ 5%). The `infortuni` policy's `sport_estremi` exclusion is being applied too aggressively. Better exclusion matching or a more explicit PolicyChecker system prompt would fix this.
3. **Adversarial pass rate to 80%** — currently 75%. 5 adversarial cases (mainly coverage ambiguity) are decided autonomously rather than escalated. Tighter adversarial detection in the coordinator prompt.
4. **HTTP ingestion endpoint** — a thin FastAPI layer over `data/inbox/` for live demo purposes. The agent core is ready; only the ingestion surface would change.
5. **CI pipeline** — `pytest` + `evals/run_evals.py` wired as a GitHub Actions workflow. The CI exit codes are already implemented; only the `.github/workflows/` file is missing.

## How We Used Claude Code

**Brainstorming and design** — The entire domain selection, architecture, team split, data strategy, and Italian market adaptation was done through an interactive brainstorming session with the visual companion. Claude drove us from "which of three domains?" to a full spec in one session.

**Parallel scaffolding** — Claude scaffolded the entire repo (33 files, all directories, `CLAUDE.md`, `pyproject.toml`, spec doc, ADR, mandate, all Python stubs with docstrings) in a single plan-then-execute pass. What would have taken a team an hour to agree on and type took one approved plan.

**`CLAUDE.md` as a forcing function** — Writing shared conventions first (€ not $, PII rules, threshold single source of truth in `escalation_rules.py`, `## Key Decision` serialization) meant every stub was already oriented correctly before implementation started.

**LangGraph migration** — Luca chose LangGraph for the coordinator and specialist graphs. Claude adapted immediately — updated graph_utils, tools_node, and all dependent tests without breaking the 37-test suite.

**Self-assembling presentation** — `scripts/build_presentation.py` reads `docs/mandate.md`, the ADR, `evals/scorecard.json`, and live decision records to produce `presentation.html`. Every re-run reflects the current state of the agent. The `## Key Decision` sections written throughout the session are extracted automatically as callouts — the process documented itself.

**Where it saved the most time** — The design phase. Normally 20–30% of a hackathon is spent arguing about architecture. Claude structured that argument, surfaced the trade-offs, and produced an ADR the team agreed on before writing a line of code.
