"""
PreToolUse hook — hard stops before any tool call.

Deterministic blocks (no LLM involved):
  - Codice Fiscale pattern in any tool input arg  → GDPR_PII_BLOCKED
  - Partita IVA pattern in any tool input arg     → GDPR_PII_BLOCKED
  - IBAN IT pattern in any tool input arg         → GDPR_PII_BLOCKED
  - write_decision on polizza with frozen=true    → FROZEN_ACCOUNT_BLOCKED
  - write_decision approve + fraud_score > 0      → FRAUD_APPROVE_BLOCKED
  - Any external URL in tool input                → EXTERNAL_ROUTING_BLOCKED

Returns {"isError": true, "code": "<CODE>"} on any match.
These are hard stops — the agent cannot override them via prompt.

Owner: Person C
"""

import re

CF_PATTERN   = r'\b[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]\b'
PIVA_PATTERN = r'\bIT\d{11}\b|\b\d{11}\b'
IBAN_PATTERN = r'\bIT\d{2}[A-Z0-9]{23}\b'


def check_pre_tool_use(tool_name: str, tool_input: dict) -> dict | None:
    """Stub — implemented in Track B (Matteo). Returns None (allow) by default."""
    return None
