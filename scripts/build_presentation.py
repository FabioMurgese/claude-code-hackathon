"""
Assembles presentation.html from documentation and eval results.

Sources:
  docs/mandate.md            → "What the agent does" section
  docs/adr/001-agent-arch.md → "Architecture" section
  evals/scorecard.json       → "Results" section with inline metrics
  data/decisions/*.json      → "Example runs" (3 sampled reasoning chains)

Extracts all '## Key Decision' H2 sections from each doc and renders them
as highlighted callouts in the presentation.

Run after evals/run_evals.py has produced evals/scorecard.json.

Usage:
    python scripts/build_presentation.py
    python scripts/build_presentation.py --out my_presentation.html

Owner: Track A (Fabio)
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

MANDATE_PATH  = Path("docs/mandate.md")
ADR_PATH      = Path("docs/adr/001-agent-arch.md")
SCORECARD_PATH = Path("evals/scorecard.json")
DECISIONS_DIR = Path("data/decisions")
DEFAULT_OUT   = Path("presentation.html")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _extract_key_decisions(md: str) -> list[str]:
    """Return all content under '## Key Decision' headings."""
    blocks: list[str] = []
    for m in re.finditer(r"^## Key Decision\b.*?\n(.*?)(?=\n## |\Z)", md, re.MULTILINE | re.DOTALL):
        text = m.group(1).strip()
        if text:
            blocks.append(text)
    return blocks


def _md_to_html(md: str) -> str:
    """Minimal Markdown → HTML: headings, bold, inline code, tables, paragraphs."""
    lines = md.split("\n")
    out: list[str] = []
    in_table = False
    in_code = False
    code_buf: list[str] = []

    for line in lines:
        # fenced code blocks
        if line.startswith("```"):
            if not in_code:
                in_code = True
                lang = line[3:].strip()
                out.append(f'<pre><code class="language-{lang}">')
                code_buf = []
            else:
                in_code = False
                out.append("\n".join(code_buf) + "\n</code></pre>")
            continue
        if in_code:
            code_buf.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # headings
        if line.startswith("#### "):
            out.append(f"<h4>{line[5:]}</h4>")
        elif line.startswith("### "):
            out.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{line[2:]}</h1>")
        # horizontal rule
        elif line.strip() in ("---", "***", "___"):
            out.append("<hr>")
        # list items
        elif re.match(r"^[-*] ", line):
            out.append(f"<li>{_inline(line[2:])}</li>")
        elif re.match(r"^\d+\. ", line):
            out.append(f"<li>{_inline(re.sub(r'^\d+\. ', '', line))}</li>")
        # table rows
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.match(r"^[-: ]+$", c) for c in cells):
                in_table = True
                continue
            tag = "th" if not in_table else "td"
            row = "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells)
            if not in_table:
                out.append(f"<table><thead><tr>{row}</tr></thead><tbody>")
            else:
                out.append(f"<tr>{row}</tr>")
        else:
            if in_table and not line.startswith("|"):
                out.append("</tbody></table>")
                in_table = False
            if line.strip():
                out.append(f"<p>{_inline(line)}</p>")
            else:
                out.append("")

    if in_table:
        out.append("</tbody></table>")
    return "\n".join(out)


def _inline(text: str) -> str:
    """Handle bold, italic, and inline code in a single line."""
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def _key_decision_callout(text: str, source: str) -> str:
    return f"""
<div class="key-decision">
  <div class="key-decision-label">🔑 Key Decision <span class="key-decision-source">— {source}</span></div>
  <div class="key-decision-body">{_md_to_html(text)}</div>
</div>"""


def _scorecard_html(scorecard: dict) -> str:
    total    = scorecard.get("total", "—")
    correct  = scorecard.get("correct", "—")
    accuracy = scorecard.get("accuracy", None)
    adv_pass = scorecard.get("adversarial_pass_rate", None)
    false_cf = scorecard.get("false_confidence_rate", None)
    esc      = scorecard.get("escalation_rate", {})
    prec     = scorecard.get("precision_per_category", {})

    def pct(v):
        return f"{v:.1%}" if isinstance(v, float) else "—"

    def badge(v, threshold, op="ge"):
        if v is None:
            return ""
        ok = (v >= threshold) if op == "ge" else (v <= threshold)
        cls = "pass" if ok else "fail"
        return f'<span class="badge {cls}">{"PASS" if ok else "FAIL"}</span>'

    prec_rows = "".join(
        f"<tr><td>precision / {cat}</td><td>{pct(p)}</td><td>—</td></tr>"
        for cat, p in prec.items() if p is not None
    )

    return f"""
<div class="scorecard">
  <h3>Eval Scorecard</h3>
  <p class="scorecard-meta">Total: {total} &nbsp;|&nbsp; Correct: {correct} &nbsp;|&nbsp;
     Run: {scorecard.get("_run_at", "—")}</p>
  <table>
    <thead><tr><th>Metric</th><th>Value</th><th>CI Threshold</th></tr></thead>
    <tbody>
      <tr><td>Accuracy</td><td>{pct(accuracy)}</td><td>—</td></tr>
      <tr><td>Adversarial pass rate</td><td>{pct(adv_pass)}</td>
          <td>≥ 80% {badge(adv_pass, 0.80)}</td></tr>
      <tr><td>False-confidence rate</td><td>{pct(false_cf)}</td>
          <td>≤ 5% {badge(false_cf, 0.05, "le")}</td></tr>
      <tr><td>Escalation correct</td><td>{esc.get("correct", "—")}</td><td>—</td></tr>
      <tr><td>Escalation needless</td><td>{esc.get("needless", "—")}</td><td>—</td></tr>
      {prec_rows}
    </tbody>
  </table>
</div>"""


def _decision_card(record: dict) -> str:
    claim_id  = record.get("claim_id", "—")
    decision  = record.get("decision", "—")
    category  = record.get("category", "—")
    confidence = record.get("confidence", 0)
    rationale  = record.get("rationale", "—")
    retries    = record.get("retry_count", 0)
    ts         = record.get("timestamp", "")[:19]
    dec_class  = {"fast_track": "fast-track", "deny": "deny",
                  "investigate": "investigate", "auto_resolve": "auto-resolve"}.get(decision, "")
    return f"""
<div class="decision-card">
  <div class="decision-header">
    <span class="claim-id">{claim_id}</span>
    <span class="decision-badge {dec_class}">{decision}</span>
    <span class="confidence">confidence: {confidence:.0%}</span>
    {"<span class='retries'>retries: " + str(retries) + "</span>" if retries else ""}
  </div>
  <div class="decision-category">Category: <code>{category}</code> &nbsp;·&nbsp; {ts}</div>
  <div class="decision-rationale">{rationale}</div>
</div>"""


# ---------------------------------------------------------------------------
# Main assembler
# ---------------------------------------------------------------------------

def build(out_path: Path) -> None:
    mandate_md = _read_md(MANDATE_PATH)
    adr_md     = _read_md(ADR_PATH)

    scorecard: dict = {}
    if SCORECARD_PATH.exists():
        scorecard = json.loads(SCORECARD_PATH.read_text(encoding="utf-8"))

    decision_records: list[dict] = []
    if DECISIONS_DIR.exists():
        for f in sorted(DECISIONS_DIR.glob("*.json"))[:3]:
            try:
                decision_records.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass

    # Collect all Key Decisions across all docs
    all_kd = (
        [_key_decision_callout(t, "Mandate") for t in _extract_key_decisions(mandate_md)]
        + [_key_decision_callout(t, "Architecture") for t in _extract_key_decisions(adr_md)]
    )

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Insur-gents — Claims Intake Agent</title>
  <style>
    :root {{
      --bg: #0f1117; --bg2: #1a1d27; --bg3: #252836;
      --text: #e2e8f0; --text2: #94a3b8; --text3: #64748b;
      --accent: #6366f1; --accent2: #8b5cf6;
      --green: #10b981; --red: #ef4444; --yellow: #f59e0b; --blue: #3b82f6;
      --border: #2d3148;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: var(--bg); color: var(--text); line-height: 1.6; }}
    .hero {{ background: linear-gradient(135deg, var(--bg2) 0%, #1e1b4b 100%);
             padding: 4rem 2rem; text-align: center; border-bottom: 1px solid var(--border); }}
    .hero h1 {{ font-size: 2.8rem; font-weight: 800; color: #fff; margin-bottom: .5rem; }}
    .hero .subtitle {{ font-size: 1.1rem; color: var(--text2); margin-bottom: 1.5rem; }}
    .hero .meta {{ display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; }}
    .meta-item {{ background: var(--bg3); border: 1px solid var(--border);
                  border-radius: 8px; padding: .5rem 1.2rem; font-size: .85rem; color: var(--text2); }}
    .meta-item strong {{ color: var(--text); }}
    nav {{ background: var(--bg2); border-bottom: 1px solid var(--border);
           padding: .75rem 2rem; display: flex; gap: 1.5rem; flex-wrap: wrap; }}
    nav a {{ color: var(--text2); text-decoration: none; font-size: .9rem; }}
    nav a:hover {{ color: var(--accent); }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
    section {{ margin-bottom: 3rem; }}
    h2 {{ font-size: 1.6rem; color: #fff; margin-bottom: 1rem;
          padding-bottom: .5rem; border-bottom: 2px solid var(--accent); }}
    h3 {{ font-size: 1.2rem; color: var(--text); margin: 1.2rem 0 .6rem; }}
    h4 {{ font-size: 1rem; color: var(--text2); margin: 1rem 0 .4rem; }}
    p {{ color: var(--text2); margin-bottom: .8rem; }}
    code {{ background: var(--bg3); color: #a5b4fc; padding: .15em .4em;
            border-radius: 4px; font-size: .88em; font-family: "SF Mono", monospace; }}
    pre {{ background: var(--bg3); border: 1px solid var(--border); border-radius: 8px;
           padding: 1rem; overflow-x: auto; margin: .8rem 0; }}
    pre code {{ background: none; padding: 0; color: #e2e8f0; }}
    table {{ width: 100%; border-collapse: collapse; margin: .8rem 0; font-size: .9rem; }}
    th {{ background: var(--bg3); color: var(--text); padding: .6rem .9rem;
          text-align: left; border-bottom: 2px solid var(--border); }}
    td {{ padding: .5rem .9rem; border-bottom: 1px solid var(--border); color: var(--text2); }}
    tr:hover td {{ background: var(--bg3); }}
    li {{ color: var(--text2); margin-left: 1.5rem; margin-bottom: .25rem; }}
    hr {{ border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }}
    a {{ color: var(--accent); }}
    .key-decision {{
      background: linear-gradient(135deg, rgba(99,102,241,.12) 0%, rgba(139,92,246,.08) 100%);
      border: 1px solid var(--accent); border-left: 4px solid var(--accent);
      border-radius: 8px; padding: 1rem 1.2rem; margin: 1rem 0;
    }}
    .key-decision-label {{ font-size: .75rem; font-weight: 700; color: var(--accent);
                           text-transform: uppercase; letter-spacing: .08em; margin-bottom: .4rem; }}
    .key-decision-source {{ font-weight: 400; color: var(--text3); text-transform: none; letter-spacing: 0; }}
    .key-decision-body p {{ color: var(--text); margin-bottom: .4rem; }}
    .scorecard {{ background: var(--bg2); border: 1px solid var(--border);
                  border-radius: 10px; padding: 1.5rem; margin: 1rem 0; }}
    .scorecard h3 {{ border: none; padding: 0; font-size: 1.1rem; margin-bottom: .5rem; color: var(--text); }}
    .scorecard-meta {{ font-size: .82rem; color: var(--text3); margin-bottom: .8rem; }}
    .badge {{ display: inline-block; font-size: .72rem; font-weight: 700; padding: .15em .5em;
              border-radius: 4px; margin-left: .4rem; }}
    .badge.pass {{ background: rgba(16,185,129,.2); color: var(--green); }}
    .badge.fail {{ background: rgba(239,68,68,.2); color: var(--red); }}
    .scorecard-placeholder {{ color: var(--text3); font-style: italic; font-size: .9rem;
                               padding: 1rem; border: 1px dashed var(--border); border-radius: 8px; }}
    .decision-card {{ background: var(--bg2); border: 1px solid var(--border);
                       border-radius: 10px; padding: 1rem 1.2rem; margin: .8rem 0; }}
    .decision-header {{ display: flex; align-items: center; gap: .8rem; flex-wrap: wrap; margin-bottom: .4rem; }}
    .claim-id {{ font-family: monospace; font-size: .85rem; color: var(--text3); }}
    .decision-badge {{ font-size: .75rem; font-weight: 700; padding: .2em .6em; border-radius: 4px; }}
    .decision-badge.fast-track {{ background: rgba(16,185,129,.2); color: var(--green); }}
    .decision-badge.deny {{ background: rgba(239,68,68,.2); color: var(--red); }}
    .decision-badge.investigate {{ background: rgba(245,158,11,.2); color: var(--yellow); }}
    .decision-badge.auto-resolve {{ background: rgba(59,130,246,.2); color: var(--blue); }}
    .confidence {{ font-size: .82rem; color: var(--text3); }}
    .retries {{ font-size: .78rem; color: var(--yellow); }}
    .decision-category {{ font-size: .82rem; color: var(--text3); margin-bottom: .4rem; }}
    .decision-rationale {{ font-size: .9rem; color: var(--text2); }}
    .decisions-placeholder {{ color: var(--text3); font-style: italic; font-size: .9rem;
                               padding: 1rem; border: 1px dashed var(--border); border-radius: 8px; }}
    .team-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }}
    .team-card {{ background: var(--bg2); border: 1px solid var(--border); border-radius: 10px;
                  padding: 1rem 1.2rem; }}
    .team-card h4 {{ color: var(--accent); margin-bottom: .3rem; }}
    .team-card p {{ font-size: .85rem; color: var(--text2); margin: 0; }}
    .footer {{ text-align: center; padding: 2rem; color: var(--text3);
               font-size: .82rem; border-top: 1px solid var(--border); }}
    @media (max-width: 700px) {{
      .team-grid {{ grid-template-columns: 1fr; }}
      .hero h1 {{ font-size: 1.8rem; }}
      .meta {{ flex-direction: column; align-items: center; }}
    }}
  </style>
</head>
<body>

<div class="hero">
  <h1>The Insur-gents</h1>
  <p class="subtitle">Insurance Claims Intake Agent — Italian/EU Market &nbsp;·&nbsp; Scenario 5: Agentic Solution</p>
  <div class="meta">
    <div class="meta-item"><strong>Stack</strong> Python · Claude Agent SDK · AWS Bedrock</div>
    <div class="meta-item"><strong>Domain</strong> Insurance Claims (IVASS · GDPR · D.Lgs. 231)</div>
    <div class="meta-item"><strong>Team</strong> Fabio · Matteo · Luca</div>
    <div class="meta-item"><strong>Generated</strong> {generated_at}</div>
  </div>
</div>

<nav>
  <a href="#mandate">Mandate</a>
  <a href="#architecture">Architecture</a>
  <a href="#tools">Tools</a>
  <a href="#guardrails">Guardrails</a>
  <a href="#results">Results</a>
  <a href="#examples">Example Runs</a>
  <a href="#decisions">Key Decisions</a>
  <a href="#team">Team</a>
</nav>

<div class="container">

  <!-- MANDATE -->
  <section id="mandate">
    <h2>What the Agent Does</h2>
    {_md_to_html(mandate_md)}
  </section>

  <!-- ARCHITECTURE -->
  <section id="architecture">
    <h2>Architecture</h2>
    {_md_to_html(adr_md)}
  </section>

  <!-- TOOLS SUMMARY -->
  <section id="tools">
    <h2>Tools</h2>
    <table>
      <thead><tr><th>Tool</th><th>Specialist</th><th>Does</th><th>Does NOT do</th><th>Error code</th></tr></thead>
      <tbody>
        <tr><td><code>fetch_claim</code></td><td>DocumentReader</td>
            <td>Reads summary.txt + metadata.json from inbox</td>
            <td>Parse PDFs or images</td><td><code>CLAIM_NOT_FOUND</code></td></tr>
        <tr><td><code>parse_attachments</code></td><td>DocumentReader</td>
            <td>Extracts text from PDF/image via PyMuPDF</td>
            <td>Make coverage decisions</td><td><code>PARSE_FAILED</code></td></tr>
        <tr><td><code>lookup_policy</code></td><td>PolicyChecker</td>
            <td>Reads policy JSON from data/policies/</td>
            <td>Interpret coverage ambiguity</td><td><code>POLICY_NOT_FOUND</code></td></tr>
        <tr><td><code>check_fraud_flags</code></td><td>PolicyChecker</td>
            <td>D.Lgs. 231/2001 mock fraud rules</td>
            <td>Access Codice Fiscale / Partita IVA</td><td><code>PII_BLOCKED</code></td></tr>
        <tr><td><code>check_sanctions</code></td><td>PolicyChecker</td>
            <td>EU/UN sanctions list check</td>
            <td>Make coverage decisions</td><td><code>SANCTIONS_CHECK_FAILED</code></td></tr>
        <tr><td><code>write_decision</code></td><td>Coordinator</td>
            <td>Writes decision JSON to data/decisions/</td>
            <td>Handle escalations</td><td><code>SCHEMA_INVALID</code></td></tr>
        <tr><td><code>escalate_claim</code></td><td>Coordinator</td>
            <td>Writes to data/escalations/ for human review</td>
            <td>Override a human decision</td><td><code>ESCALATION_FAILED</code></td></tr>
      </tbody>
    </table>
    <p style="margin-top:.6rem;font-size:.85rem;color:var(--text3)">
      All tools return <code>{{"isError": true, "code": "...", "guidance": "..."}}</code> on failure — the agent recovers without parsing raw exceptions.
    </p>
  </section>

  <!-- GUARDRAILS -->
  <section id="guardrails">
    <h2>Guardrails</h2>
    <h3>PreToolUse Hook — hard stops (deterministic, no LLM)</h3>
    <table>
      <thead><tr><th>Pattern</th><th>Block code</th></tr></thead>
      <tbody>
        <tr><td>Codice Fiscale regex in any tool input</td><td><code>GDPR_PII_BLOCKED</code></td></tr>
        <tr><td>Partita IVA / IBAN pattern in any tool input</td><td><code>GDPR_PII_BLOCKED</code></td></tr>
        <tr><td>External URL in any tool input</td><td><code>EXTERNAL_ROUTING_BLOCKED</code></td></tr>
        <tr><td>write_decision on polizza with <code>frozen=true</code></td><td><code>FROZEN_ACCOUNT_BLOCKED</code></td></tr>
        <tr><td>approve decision with <code>fraud_score &gt; 0</code></td><td><code>FRAUD_APPROVE_BLOCKED</code></td></tr>
      </tbody>
    </table>
    <h3>Escalation Rules — slow stops (explicit thresholds)</h3>
    <table>
      <thead><tr><th>Trigger</th><th>Threshold</th></tr></thead>
      <tbody>
        <tr><td>amount_eur</td><td>≥ €5 000</td></tr>
        <tr><td>confidence</td><td>&lt; 0.75</td></tr>
        <tr><td>fraud_score</td><td>&gt; 0</td></tr>
        <tr><td>sanctions_hit</td><td>true</td></tr>
        <tr><td>coverage_status</td><td>ambiguous</td></tr>
        <tr><td>claim_type</td><td>contestazione</td></tr>
      </tbody>
    </table>
  </section>

  <!-- RESULTS -->
  <section id="results">
    <h2>Eval Results</h2>
    {_scorecard_html(scorecard) if scorecard else
     '<div class="scorecard-placeholder">Scorecard not yet generated. Run <code>python evals/run_evals.py</code> to produce evals/scorecard.json, then re-run this script.</div>'}
  </section>

  <!-- EXAMPLE RUNS -->
  <section id="examples">
    <h2>Example Runs</h2>
    {"".join(_decision_card(r) for r in decision_records) if decision_records else
     '<div class="decisions-placeholder">No decision records yet. Process claims with <code>python -m src.agent ingest CLM-001</code>, then re-run this script.</div>'}
  </section>

  <!-- KEY DECISIONS -->
  <section id="decisions">
    <h2>Key Decisions</h2>
    {"".join(all_kd) if all_kd else "<p>No key decisions extracted.</p>"}
  </section>

  <!-- TEAM -->
  <section id="team">
    <h2>Team</h2>
    <div class="team-grid">
      <div class="team-card">
        <h4>Fabio</h4>
        <p>PM/BA · Architect · Tools · Data generation · Presentation pipeline</p>
      </div>
      <div class="team-card">
        <h4>Luca</h4>
        <p>Architect · Agent loop · PolicyChecker specialist · Coordinator · Integration</p>
      </div>
      <div class="team-card">
        <h4>Matteo</h4>
        <p>Quality · PreToolUse hook · Adversarial eval set · Eval harness · Scorecard</p>
      </div>
    </div>
  </section>

</div>

<div class="footer">
  Built with Claude Code · AWS Bedrock · Scenario 5 — Agentic Solution<br>
  Generated {generated_at}
</div>

</body>
</html>
"""

    out_path.write_text(html, encoding="utf-8")
    print(f"presentation.html written to {out_path}")
    print(f"  mandate sections: {len(_extract_key_decisions(mandate_md))} key decisions")
    print(f"  ADR sections: {len(_extract_key_decisions(adr_md))} key decisions")
    print(f"  scorecard: {'loaded' if scorecard else 'not available (placeholder shown)'}")
    print(f"  decision examples: {len(decision_records)} records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assemble presentation.html from docs and eval results")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output path (default: presentation.html)")
    args = parser.parse_args()
    build(args.out)
