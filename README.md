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

**What runs today:** the entire pipeline is end-to-end functional. `python -m src.agent ingest CLM-001` produces a real decision in ~10 seconds via AWS Bedrock Opus 4.7. 37 unit tests pass. The eval harness runs 60 labeled claims (40 normal + 20 adversarial) and emits a scored scorecard. The presentation assembles itself from live docs and eval output.

## Challenges Attempted

| # | Challenge | Status | Notes |
|---|---|---|---|
| 1 | The Mandate | ✅ done | [`docs/mandate.md`](docs/mandate.md) — decides alone / escalates / never touches, explicit €5 000 and 0.75 confidence thresholds |
| 2 | The Bones | ✅ done | [`docs/adr/001-agent-arch.md`](docs/adr/001-agent-arch.md) — coordinator + 2 specialists, stop_reason dispatch, explicit context passing |
| 3 | The Tools | ✅ done | 6 tools in [`src/tools/`](src/tools/) — fetch_claim, lookup_policy, check_fraud_flags, check_sanctions, write_decision, escalate_claim, parse_attachments. All tested. |
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

# 2. Authenticate with AWS (Bedrock Opus 4.7 — no Anthropic API key needed)
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

AWS Bedrock credentials required (`aws login`). Model: `eu.anthropic.claude-opus-4-7` (EU inference profile).

## If We Had More Time

1. **Challenge 8 — The Loop** — when a human overrides a decision, the signal should flow to a labeled-example store that feeds the adversarial eval set and few-shot examples for the coordinator classifier. The scaffolding (`data/escalations/`) is in place; the feedback wiring is not.
2. **Improve false-confidence rate** — currently 18.3% (target ≤ 5%). The `infortuni` policy's `sport_estremi` exclusion is being applied too aggressively (calcetto amatoriale, bicicletta). Better exclusion matching logic or a more explicit system prompt for the PolicyChecker would fix this.
3. **Adversarial pass rate to 80%** — currently 75%. 5 adversarial cases (mainly coverage ambiguity) are being decided autonomously rather than escalated. Tighter adversarial detection in the coordinator prompt.
4. **HTTP ingestion endpoint** — a thin FastAPI layer over `data/inbox/` for live demo purposes. The agent core is ready; only the ingestion surface would change.
5. **CI pipeline** — `pytest` + `evals/run_evals.py` wired as a GitHub Actions workflow. The CI exit codes are already implemented; only the `.github/workflows/` file is missing.

## How We Used Claude Code

**Brainstorming and design** — The entire domain selection, architecture, team split, data strategy, and Italian market adaptation was done through an interactive brainstorming session with the visual companion. Claude drove us from "which of three domains?" to a full spec in one session.

**Parallel scaffolding** — Claude scaffolded the entire repo (33 files, all directories, `CLAUDE.md`, `pyproject.toml`, spec doc, ADR, mandate, all Python stubs with docstrings) in a single plan-then-execute pass. What would have taken a team an hour to agree on and type took one approved plan.

**`CLAUDE.md` as a forcing function** — Writing shared conventions first (€ not $, PII rules, threshold single source of truth in `escalation_rules.py`, `## Key Decision` serialization) meant every stub was already oriented correctly before implementation started.

**LangGraph migration** — Luca chose LangGraph for the coordinator and specialist graphs. Claude adapted immediately — updated graph_utils, tools_node, and all dependent tests without breaking the 37-test suite.

**Where it saved the most time** — The design phase. Normally 20–30% of a hackathon is spent arguing about architecture. Claude structured that argument, surfaced the trade-offs, and produced an ADR the team agreed on before writing a line of code.

---

# Claude Code Hackathon

## The Point

This is a hack. You get a team, a scenario, and Claude Code. The scenarios are enterprise-flavored briefs: a monolith nobody understands, a migration nobody agrees on, seven systems that can't agree on what a customer is. Real problems, compressed.

There's no prescribed path. Each scenario sketches a handful of challenges worth working toward. How you get there, what stack you pick, what you skip, what you invent on top is up to you. We care about ambition and judgment, not box-checking.

---

## The Setup

Pick one scenario. Work with your team. Get as far as you can.

Each scenario sketches a handful of challenges. You probably won't do them all, and that's the point. **Depth beats breadth.** Pick the ones that interest you, work in parallel where you can, and let Claude help you coordinate.

---

## How Your Team Works

The scenarios span the SDLC, so there's meaningful work for PM, architect, dev, test, and platform. You won't have one of each, and that's fine. **Play every role, regardless of your day job.** Claude Code doesn't care what your title is, and a lot of what makes the hack interesting is watching the tool perform in parts of the work you don't normally touch.

Divide the challenges up early. Share a running `CLAUDE.md` so everyone teaches the tool the same conventions. Commit often. The commit history is part of the submission and part of how the judges read the journey.

---

## The Rules

1. **Tech stack is yours to choose.** One exception: Scenario 5 requires the **Claude Agent SDK**. Use Claude to help you learn it, or to migrate if you're coming from another framework.
2. **You may need to build starter code, data, or documents.** If the scenario says "a 12-year-old monolith exists," you generate it. That's part of the job. Some scenarios offer optional starter repos. Use them or don't.
3. **Play every role.** Your team needs a PM, architect, developer, tester, data engineer, and infra engineer whether you staffed for it or not.
4. **Commit history is evidence.** We want to see the journey, not just the destination.
5. **`CLAUDE.md` is your friend.** Teach it your conventions early.
6. **Document your work.** Your repo must include a `README.md` (template below) explaining what you built and what you'd do next.
7. **Build a presentation.** Use Claude Code to generate an HTML presentation you *could* deliver if you win the judging. It lives in your repo whether you present or not.
8. **Claude will judge.** At the end, Claude evaluates submissions. A handful of teams present live.

---

## The Scenarios

| \# | Scenario | One-liner |
| :---- | :---- | :---- |
| 1 | **[Code Modernization](01-code-modernization.md)** | A monolith nobody understands. The board wants it "modernized." |
| 2 | **[Cloud Migration](02-cloud-migration.md)** | On-prem to cloud. The CFO and CTO disagree on how. |
| 3 | **[Data Engineering](03-data-engineering.md)** | Seven systems. Zero agreement on what a "customer" is. |
| 4 | **[Data Analytics](04-data-analytics.md)** | 40 dashboards. One metric. Four different answers. |
| 5 | **[Agentic Solution](05-agentic-solution.md)** (Claude Agent SDK) | 200 requests a day, triaged by hand. Build the agent. |

---

## Techniques to Reach For

These are the patterns the Claude Code Architecture certification tests on. No scenario requires them, and no challenge dictates which to use. They're here because a lot of teams also want the hack to double as cert practice. Pick two or three you want to get reps on, and reach for them inside whichever challenges you pursue.

**Agentic Architecture**

- Coordinator plus specialist subagents via the Task tool, with context passed *explicitly* in each call (Task subagents don't inherit coordinator context).
- Stop conditions that are real signals, not "parse the text" or "iteration cap."
- `fork_session` to try two paths on the same input and compare.

**Tool Design & MCP**

- Tool descriptions that say what the tool *does* and what it *does not*. Input formats, edge cases, example queries.
- Structured error responses (`isError: true` with a reason code and guidance) so the agent can recover gracefully.
- Keep each specialist's tool count small. Reliability tends to drop once an agent has more than a handful.
- An MCP server over whatever system you built, so a fresh Claude session picks the right tool on the first try.

**Claude Code Config**

- Three-level `CLAUDE.md`: user (personal preferences), project (shared, in VCS), directory (per-module specifics).
- Custom slash commands *and* skills, used distinctly. A command runs a playbook; a skill captures reusable guidance.
- Plan Mode for anything reversible-dangerous; direct execution for the safe paths. Defend the default.
- Non-interactive Claude Code in CI, with scoped tools and no write access to production paths.

**Prompt Engineering**

- Explicit criteria in place of vague modifiers. "Material," "significant," and "recent" are usually a signal that the definition needs sharper thresholds.
- Few-shot examples with a negative case and a boundary case. Two sharp examples outperform eight fuzzy ones.
- `tool_use` with a JSON Schema for anything that must parse. Don't prompt-for-JSON.
- Validation-retry loop: structured validator checks the output, errors are fed back, Claude retries up to N times. Log retry count and error type.

**Context Management**

- Hooks for deterministic guardrails (`PreToolUse` to block, `PostToolUse` to redact). Prompts for probabilistic preferences. An ADR on why each is which is worth writing; the distinction shows up repeatedly on the exam.
- Escalation rules that are category plus confidence plus impact, not "when the agent isn't sure."
- Stratified sampling and field-level confidence when humans review.

---

## The Judging

Claude does the first pass. Top teams present live.

**What definitely gets read:**

1. Your `README.md`
2. Your `presentation.html`
3. Your `CLAUDE.md`

These are your pitch. Don't leave them to the end. If Claude only sees those three files, it should still understand what you built, why it matters, how far you got, and how you taught the tool to work your way. We may go deeper into the repo, we may not. Assume those three carry the weight.

**What we're looking for** (final categories will be a surprise!, but think along these lines):

- **Most production-ready.** Could hand it to an ops team Monday.
- **Best architecture thinking.** ADRs, diagrams, decisions someone will thank you for later.
- **Best testing.** Not coverage. Adversarial thinking, edge cases, evals.
- **Best product work.** Stories that are actually stories. Docs that persuade.
- **Most inventive Claude Code use.** Subagents, hooks, skills, something we didn't expect.
- **Wildcards:** best CI/CD, best legacy archaeology, best "what if this goes wrong" thinking, furthest through the challenges with quality intact, team that questioned a scenario requirement and was *right*.

---

## Submission

You need three files:

1. **`README.md`** tells the story. Use the template below.
2. **`CLAUDE.md`** so we can see how you taught Claude Code to work your way.
3. **`presentation.html`**, your HTML deck built with Claude Code, ready to present if called.

**Preferred:** put the three files in a folder named for your table and team (for example `Table1_SonnetSlayers/`) and upload the folder to the link provided at your session.

**Alternative:** if a folder upload isn't supported, zip the three files into an archive with the same naming convention (for example `Table1_SonnetSlayers.zip`) and upload that instead.

Either way, **one submission per team**.

**NO CLIENT OR INTERNAL DATA.** Anything in the submission must be safe to share.

---

## README Template

Copy this into your repo's `README.md` and fill it in as you go, not at the end.

```
# Team <name>

## Participants
- Name (role(s) played today)
- Name (role(s) played today)
- Name (role(s) played today)

## Scenario
Scenario <#>: <title>

## What We Built
A couple of paragraphs. What exists in this repo that didn't exist when you
started. What runs, what's scaffolding, what's faked.

## Challenges Attempted
| # | Challenge | Status | Notes |
|---|---|---|---|
| 1 | The <name> | done / partial / skipped | |
| 2 | | | |

## Key Decisions
Biggest calls you made and why. Link into `/decisions` for the full ADRs.

## How to Run It
Exact commands. Assume the reader has Docker and nothing else.

## If We Had More Time
What you'd tackle next, in priority order. Be honest about what's held
together with tape.

## How We Used Claude Code
What worked. What surprised you. Where it saved the most time.
```

---

**Pick a scenario. Start building.**
