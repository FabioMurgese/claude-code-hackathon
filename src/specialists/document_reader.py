"""
DocumentReader specialist.

Tools: fetch_claim, parse_attachments.
Returns: ClaimSummary(text, amount_eur, claim_type, claimant_id, numero_sinistro).

Receives claim_id and instructions via Task prompt from the coordinator.
Does NOT have access to policy data or fraud rules.

Owner: Person B
"""

import json
from src.agent.loop import run_agent_loop
from src.hooks.pre_tool_use import check_pre_tool_use
from src.tools.fetch_claim import fetch_claim, FETCH_CLAIM_SCHEMA
from src.tools.parse_attachments import parse_attachments, PARSE_ATTACHMENTS_SCHEMA

_SYSTEM = """Sei il DocumentReader specialist del sistema di triage sinistri.
Il tuo compito è leggere i dati grezzi di un sinistro e restituire un JSON ClaimSummary.

STRUMENTI: fetch_claim (leggi dati testo), parse_attachments (solo se ci sono PDF/immagini).
REGOLE: Non prendere decisioni di copertura. Non passare Codice Fiscale, P.IVA o IBAN agli strumenti.
OUTPUT: Restituisci SOLO il JSON ClaimSummary, senza testo aggiuntivo.

FORMATO:
{
  "claim_id": "...",
  "summary_text": "...",
  "amount_eur": 0.0,
  "claim_type": "...",
  "claimant_id": "...",
  "numero_sinistro": "...",
  "incident_date": "YYYY-MM-DD",
  "policy_id": "...",
  "frozen": false,
  "in_contenzioso": false
}"""

_TOOLS = [FETCH_CLAIM_SCHEMA, PARSE_ATTACHMENTS_SCHEMA]
_TOOL_FNS = {"fetch_claim": fetch_claim, "parse_attachments": parse_attachments}


def run_document_reader(claim_id: str) -> dict:
    """Run DocumentReader in isolated context — Task subagents do NOT inherit coordinator state."""
    messages = [
        {
            "role": "user",
            "content": (
                f"Processa il sinistro claim_id='{claim_id}'. "
                "Usa fetch_claim per leggere i dati, poi restituisci il JSON ClaimSummary."
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
