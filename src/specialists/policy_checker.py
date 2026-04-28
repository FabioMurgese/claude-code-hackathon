"""
PolicyChecker specialist.

Tools: lookup_policy, check_fraud_flags, check_sanctions.
Returns: PolicyResult(coverage_status, fraud_score, exclusions, sanctions_hit).

Receives a serialized ClaimSummary via Task prompt — never sees raw coordinator
context. Does NOT have access to inbox files.

Owner: Person B
"""

import json
from src.agent.loop import run_agent_loop
from src.hooks.pre_tool_use import check_pre_tool_use
from src.tools.lookup_policy import lookup_policy, LOOKUP_POLICY_SCHEMA
from src.tools.check_fraud_flags import check_fraud_flags, CHECK_FRAUD_SCHEMA
from src.tools.check_sanctions import check_sanctions, CHECK_SANCTIONS_SCHEMA

_SYSTEM = """Sei il PolicyChecker specialist del sistema di triage sinistri.
Ricevi un ClaimSummary JSON e devi verificare copertura, frodi e sanzioni.

STRUMENTI: lookup_policy (verifica polizza), check_fraud_flags (D.Lgs. 231/2001), check_sanctions (EU/UN).
REGOLE: Non hai accesso ai file inbox. Non prendere la decisione finale. Non passare CF, P.IVA, IBAN agli strumenti.
OUTPUT: Restituisci SOLO il JSON PolicyResult, senza testo aggiuntivo.

FORMATO OUTPUT:
{
  "coverage_status": "covered" | "denied" | "ambiguous",
  "fraud_score": 0,
  "triggered_rules": [],
  "sanctions_hit": false,
  "exclusions_matched": [],
  "policy_valid": true,
  "policy_notes": "..."
}"""

_TOOLS = [LOOKUP_POLICY_SCHEMA, CHECK_FRAUD_SCHEMA, CHECK_SANCTIONS_SCHEMA]
_TOOL_FNS = {
    "lookup_policy": lookup_policy,
    "check_fraud_flags": check_fraud_flags,
    "check_sanctions": check_sanctions,
}


def run_policy_checker(claim_summary: dict) -> dict:
    """Run PolicyChecker in isolated context — receives ClaimSummary explicitly, no coordinator state."""
    messages = [
        {
            "role": "user",
            "content": (
                f"Verifica copertura per questo sinistro: {json.dumps(claim_summary, ensure_ascii=False)}. "
                "Usa gli strumenti disponibili e restituisci il JSON PolicyResult."
            ),
        }
    ]
    result_text = run_agent_loop(
        system=_SYSTEM,
        tools=_TOOLS,
        tool_functions=_TOOL_FNS,
        messages=messages,
        pre_tool_hook=check_pre_tool_use,
    )
    return json.loads(result_text)
