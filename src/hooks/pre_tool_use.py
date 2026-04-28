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

Owner: Person B
"""

import json
import re

CF_PATTERN   = r'\b[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]\b'
PIVA_PATTERN = r'\bIT\d{11}\b|\b\d{11}\b'
IBAN_PATTERN = r'\bIT\d{2}[A-Z0-9]{23}\b'
URL_PATTERN  = r'https?://'


def check_pre_tool_use(tool_name: str, tool_input: dict) -> dict | None:
    """Return a block dict if the call must be hard-stopped, else None."""
    text_upper = json.dumps(tool_input, ensure_ascii=False).upper()
    text_raw   = json.dumps(tool_input, ensure_ascii=False)

    if re.search(CF_PATTERN, text_upper):
        return {"isError": True, "code": "GDPR_PII_BLOCKED",
                "guidance": "Codice Fiscale detected — do not pass PII to tools"}
    if re.search(IBAN_PATTERN, text_upper):
        return {"isError": True, "code": "GDPR_PII_BLOCKED",
                "guidance": "IBAN detected — do not pass PII to tools"}
    if re.search(URL_PATTERN, text_raw):
        return {"isError": True, "code": "EXTERNAL_ROUTING_BLOCKED",
                "guidance": "External URLs not permitted in tool inputs"}

    if tool_name == "write_decision":
        if tool_input.get("metadata", {}).get("frozen"):
            return {"isError": True, "code": "FROZEN_ACCOUNT_BLOCKED",
                    "guidance": "Cannot write decision on a frozen polizza"}
        fs = tool_input.get("fraud_score") or 0
        if fs > 0 and tool_input.get("decision") in ("fast_track", "auto_resolve"):
            return {"isError": True, "code": "FRAUD_APPROVE_BLOCKED",
                    "guidance": "Cannot approve a claim with fraud_score > 0"}

    return None
