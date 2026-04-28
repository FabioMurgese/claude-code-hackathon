"""
CLI entry point for the eval harness.

Runs the full eval suite (normal + adversarial) and prints the scorecard
to stdout using Rich formatting. Exits with code 1 if adversarial_pass_rate
drops below 0.80 or false_confidence_rate exceeds 0.05.

Usage:
    python evals/run_evals.py
    python evals/run_evals.py --only adversarial
    python evals/run_evals.py --only normal

Owner: Person C
"""
import argparse
import sys
from rich.console import Console
from rich.table import Table
from evals.harness import run_harness

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Run claims agent eval suite")
    parser.add_argument("--only", choices=["normal", "adversarial"], default=None)
    args = parser.parse_args()

    console.print("[bold blue]Running eval harness...[/bold blue]")
    metrics = run_harness(only=args.only)

    table = Table(title="Claims Agent Scorecard", show_lines=True)
    table.add_column("Metric",       style="cyan",   min_width=30)
    table.add_column("Value",        style="green",  min_width=10)
    table.add_column("CI Threshold", style="yellow", min_width=12)
    table.add_column("Status",       style="bold",   min_width=6)

    def fmt(v):
        return f"{v:.1%}" if isinstance(v, float) else str(v)

    failed = False
    rows = [
        ("accuracy",              metrics.get("accuracy", 0),              None),
        ("adversarial_pass_rate", metrics.get("adversarial_pass_rate", 0), ">= 80%"),
        ("false_confidence_rate", metrics.get("false_confidence_rate", 0), "<= 5%"),
    ]
    for name, value, threshold in rows:
        if name == "adversarial_pass_rate":   ok = value >= 0.80
        elif name == "false_confidence_rate": ok = value <= 0.05
        else:                                 ok = True
        if not ok:
            failed = True
        table.add_row(name, fmt(value), threshold or "—", "[green]PASS[/green]" if ok else "[red]FAIL[/red]")

    for cat, prec in (metrics.get("precision_per_category") or {}).items():
        if prec is not None:
            table.add_row(f"precision/{cat}", fmt(prec), "—", "—")

    esc = metrics.get("escalation_rate", {})
    table.add_row("escalation_rate/correct",  str(esc.get("correct",  0)), "—", "—")
    table.add_row("escalation_rate/needless", str(esc.get("needless", 0)), "—", "—")

    console.print(table)
    console.print(f"[dim]Total: {metrics.get('total', 0)} | Correct: {metrics.get('correct', 0)} | Scorecard → evals/scorecard.json[/dim]")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
