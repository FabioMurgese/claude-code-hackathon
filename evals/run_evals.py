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
