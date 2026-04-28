"""
Assembles presentation.html from documentation and eval results.

Sources:
  docs/mandate.md           → "What the agent does" section
  docs/adr/001-agent-arch.md → "Architecture" section
  evals/scorecard.json      → "Results" section with inline metrics
  data/decisions/*.json     → "Example runs" (3 sampled reasoning chains)

Extracts all '## Key Decision' H2 sections from each doc and renders them
as highlighted callouts in the presentation. This is how architectural choices
and process rationale get surfaced automatically without manual curation.

Run after evals/run_evals.py has produced evals/scorecard.json.

Usage:
    python scripts/build_presentation.py
    python scripts/build_presentation.py --out my_presentation.html

Owner: Person A
"""
