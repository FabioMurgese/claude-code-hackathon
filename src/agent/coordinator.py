"""
Coordinator agent.

Ingests a claim_id from data/inbox/, launches DocumentReader and PolicyChecker
specialists via Task (passing context explicitly — subagents do NOT inherit
coordinator memory), validates structured output against DecisionSchema with
a retry loop (max 3 attempts), applies escalation rules from
src/escalation_rules.py, and calls write_decision() or escalate_claim().

Owner: Person B
"""

import json
from src.agent.loop import run_agent_loop, MaxTokensError
from src.validator import validate_decision
from src.escalation_rules import should_escalate
from src.hooks.pre_tool_use import check_pre_tool_use
from src.specialists.document_reader import run_document_reader
from src.specialists.policy_checker import run_policy_checker
from src.tools.write_decision import write_decision, WRITE_DECISION_SCHEMA
from src.tools.escalate_claim import escalate_claim, ESCALATE_CLAIM_SCHEMA

_SYSTEM = """Sei il Coordinator del sistema di triage sinistri assicurativi italiani.
Hai il ClaimSummary e il PolicyResult. Sintetizza la decisione finale.

DECISIONI:
- fast_track: copertura chiara, importo <€5000, nessun flag
- investigate: importo >=€5000, copertura ambigua, o necessita revisione
- deny: polizza scaduta, esclusione applicabile, o sinistro duplicato
- auto_resolve: sinistro già liquidato (duplicato confermato)

Chiama write_decision con il JSON di decisione strutturato.
Non includere Codice Fiscale, Partita IVA o IBAN nella motivazione."""

_TOOLS = [WRITE_DECISION_SCHEMA, ESCALATE_CLAIM_SCHEMA]
_TOOL_FNS = {"write_decision": write_decision, "escalate_claim": escalate_claim}


def process_claim(claim_id: str) -> dict:
    """Full coordinator flow. Returns a decision record or escalation record."""
    # 1. Document reading — isolated context (Task subagents do NOT inherit coordinator state)
    try:
        claim_summary = run_document_reader(claim_id)
    except MaxTokensError:
        return escalate_claim(claim_id=claim_id, escalation_reason="max_tokens: DocumentReader truncated")

    # 2. Policy checking — receives ClaimSummary explicitly in prompt
    try:
        policy_result = run_policy_checker(claim_summary)
    except MaxTokensError:
        return escalate_claim(claim_id=claim_id, escalation_reason="max_tokens: PolicyChecker truncated")

    # 3. Synthesis + validation-retry loop (max 3 attempts)
    coord_messages = [
        {
            "role": "user",
            "content": (
                f"Sinistro: {json.dumps(claim_summary, ensure_ascii=False)}\n"
                f"Polizza: {json.dumps(policy_result, ensure_ascii=False)}\n"
                "Sintetizza la decisione finale e chiama write_decision."
            ),
        }
    ]

    decision: dict | None = None
    last_error = ""
    retry_count = 0

    for attempt in range(1, 4):
        if last_error:
            coord_messages = coord_messages + [
                {"role": "user", "content": f"Errore di validazione: {last_error}. Correggi e riprova."}
            ]
        try:
            result_text = run_agent_loop(
                system=_SYSTEM,
                tools=_TOOLS,
                tool_functions=_TOOL_FNS,
                messages=coord_messages,
                pre_tool_hook=check_pre_tool_use,
            )
        except MaxTokensError:
            return escalate_claim(claim_id=claim_id, escalation_reason="max_tokens: Coordinator truncated")

        try:
            decision = json.loads(result_text)
        except json.JSONDecodeError:
            last_error = "output non era JSON valido"
            retry_count = attempt
            continue

        is_valid, error = validate_decision(decision)
        if is_valid:
            break
        last_error = error
        retry_count = attempt

    if decision is None or not validate_decision(decision)[0]:
        return escalate_claim(
            claim_id=claim_id,
            escalation_reason=f"validation_failed_after_3_retries: {last_error}",
        )

    decision["retry_count"] = retry_count

    # 4. Escalation rules (explicit thresholds from escalation_rules.py)
    should_esc, reason = should_escalate(
        amount_eur=claim_summary.get("amount_eur", 0),
        confidence=decision.get("confidence", 0),
        fraud_score=policy_result.get("fraud_score", 0),
        sanctions_hit=policy_result.get("sanctions_hit", False),
        coverage_status=policy_result.get("coverage_status", "unknown"),
        claim_type=claim_summary.get("claim_type", ""),
    )

    if should_esc:
        return escalate_claim(
            claim_id=claim_id,
            escalation_reason=reason,
            decision=decision.get("decision"),
            confidence=decision.get("confidence"),
            rationale=decision.get("rationale"),
        )

    # 5. Write final decision
    return write_decision(
        claim_id=claim_id,
        decision=decision["decision"],
        category=decision["category"],
        confidence=decision["confidence"],
        rationale=decision["rationale"],
        retry_count=retry_count,
    )
