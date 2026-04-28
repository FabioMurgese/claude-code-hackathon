"""
Coordinator agent — LangGraph implementation.

Graph nodes:
  read_documents → check_policy → synthesize → validate → check_escalation → END

Coordinator LLM uses Option B: outputs plain JSON text (no tool binding).
Python code calls write_decision / escalate_claim after validation passes.
MaxTokensError from specialists → escalate immediately.

## Key Decision
Option B chosen for coordinator synthesis: LLM returns plain JSON text rather
than tool calls. This avoids coordinator tool-binding complexity and keeps
write_decision / escalate_claim as pure Python side-effects, making the
validation-retry loop straightforward to implement as a graph cycle.

_llm is initialised lazily (None at import time) so that importing this module
does not require AWS credentials. Credentials are only resolved on the first
actual process_claim() call.

Owner: Person B
"""

import json
from typing import Annotated, Optional
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from src.agent.graph_utils import build_chat_model, MaxTokensError
from src.validator import validate_decision
from src.escalation_rules import should_escalate
from src.specialists.document_reader import run_document_reader
from src.specialists.policy_checker import run_policy_checker
from src.tools.write_decision import write_decision
from src.tools.escalate_claim import escalate_claim

_SYSTEM = """Sei il Coordinator del sistema di triage sinistri assicurativi italiani.
Hai il ClaimSummary e il PolicyResult. Sintetizza la decisione finale.

DECISIONI:
- fast_track: copertura chiara, importo <€5000, nessun flag
- investigate: importo >=€5000, copertura ambigua, o necessita revisione
- deny: polizza scaduta, esclusione applicabile, o sinistro duplicato
- auto_resolve: sinistro già liquidato (duplicato confermato)

Restituisci SOLO un JSON con: claim_id, decision, category, confidence (0.0-1.0), rationale.
Non includere Codice Fiscale, Partita IVA o IBAN nella motivazione."""

_llm = None  # lazy — built on first call to avoid import-time AWS credential check


def _get_llm():
    global _llm
    if _llm is None:
        _llm = build_chat_model()
    return _llm


class CoordinatorState(TypedDict):
    claim_id: str
    claim_summary: Optional[dict]
    policy_result: Optional[dict]
    messages: Annotated[list, add_messages]
    retry_count: int
    last_validation_error: str
    final_result: Optional[dict]


def _read_documents(state: CoordinatorState) -> dict:
    try:
        summary = run_document_reader(state["claim_id"])
        return {"claim_summary": summary}
    except MaxTokensError:
        result = escalate_claim(
            claim_id=state["claim_id"],
            escalation_reason="max_tokens: DocumentReader truncated",
        )
        return {"final_result": result}


def _check_policy(state: CoordinatorState) -> dict:
    if state.get("final_result"):
        return {}
    try:
        policy = run_policy_checker(state["claim_summary"])
        return {"policy_result": policy}
    except MaxTokensError:
        result = escalate_claim(
            claim_id=state["claim_id"],
            escalation_reason="max_tokens: PolicyChecker truncated",
        )
        return {"final_result": result}


def _synthesize(state: CoordinatorState) -> dict:
    if state.get("final_result"):
        return {}
    prompt_parts = [
        f"Sinistro: {json.dumps(state['claim_summary'], ensure_ascii=False)}",
        f"Polizza: {json.dumps(state['policy_result'], ensure_ascii=False)}",
        "Sintetizza la decisione finale.",
    ]
    if state.get("last_validation_error"):
        prompt_parts.append(f"Errore precedente: {state['last_validation_error']}. Correggi.")
    msgs = [SystemMessage(content=_SYSTEM), HumanMessage(content="\n".join(prompt_parts))]
    response = _get_llm().invoke(msgs)
    return {"messages": [response]}


def _strip_json(content) -> str:
    """Strip markdown code fences and extract text from list content."""
    if isinstance(content, list):
        text = " ".join(p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text")
    else:
        text = str(content)
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
    return text


def _validate(state: CoordinatorState) -> dict:
    if state.get("final_result"):
        return {}
    last_ai = next(
        (m for m in reversed(state["messages"]) if isinstance(m, AIMessage)), None
    )
    if last_ai is None:
        return {"last_validation_error": "no AI message found", "retry_count": state.get("retry_count", 0) + 1}
    try:
        decision = json.loads(_strip_json(last_ai.content))
    except json.JSONDecodeError:
        return {"last_validation_error": "output non era JSON valido", "retry_count": state.get("retry_count", 0) + 1}
    is_valid, error = validate_decision(decision)
    if is_valid:
        return {"final_result": decision, "retry_count": state.get("retry_count", 0)}
    return {"last_validation_error": error, "retry_count": state.get("retry_count", 0) + 1}


def _check_escalation(state: CoordinatorState) -> dict:
    decision = state["final_result"]
    claim = state["claim_summary"]
    policy = state["policy_result"]
    should_esc, reason = should_escalate(
        amount_eur=claim.get("amount_eur", 0),
        confidence=decision.get("confidence", 0),
        fraud_score=policy.get("fraud_score", 0),
        sanctions_hit=policy.get("sanctions_hit", False),
        coverage_status=policy.get("coverage_status", "unknown"),
        claim_type=claim.get("claim_type", ""),
    )
    if should_esc:
        result = escalate_claim(
            claim_id=state["claim_id"],
            escalation_reason=reason,
            decision=decision.get("decision"),
            confidence=decision.get("confidence"),
            rationale=decision.get("rationale"),
        )
    else:
        result = write_decision(
            claim_id=state["claim_id"],
            decision=decision["decision"],
            category=decision["category"],
            confidence=decision["confidence"],
            rationale=decision["rationale"],
            retry_count=state.get("retry_count", 0),
        )
    return {"final_result": result}


def _fail(state: CoordinatorState) -> dict:
    result = escalate_claim(
        claim_id=state["claim_id"],
        escalation_reason=f"validation_failed_after_3_retries: {state.get('last_validation_error', '')}",
    )
    return {"final_result": result}


def _route_after_read(state: CoordinatorState) -> str:
    return END if state.get("final_result") else "check_policy"


def _route_after_policy(state: CoordinatorState) -> str:
    return END if state.get("final_result") else "synthesize"


def _route_after_validate(state: CoordinatorState) -> str:
    if state.get("final_result"):
        return "check_escalation"
    if state.get("retry_count", 0) >= 3:
        return "fail"
    return "synthesize"


_graph = (
    StateGraph(CoordinatorState)
    .add_node("read_documents", _read_documents)
    .add_node("check_policy", _check_policy)
    .add_node("synthesize", _synthesize)
    .add_node("validate", _validate)
    .add_node("check_escalation", _check_escalation)
    .add_node("fail", _fail)
    .set_entry_point("read_documents")
    .add_conditional_edges("read_documents", _route_after_read)
    .add_conditional_edges("check_policy", _route_after_policy)
    .add_edge("synthesize", "validate")
    .add_conditional_edges("validate", _route_after_validate)
    .add_edge("check_escalation", END)
    .add_edge("fail", END)
    .compile()
)


def process_claim(claim_id: str) -> dict:
    """Full coordinator flow. Returns a decision record or escalation record."""
    init_state: CoordinatorState = {
        "claim_id": claim_id,
        "claim_summary": None,
        "policy_result": None,
        "messages": [],
        "retry_count": 0,
        "last_validation_error": "",
        "final_result": None,
    }
    final_state = _graph.invoke(init_state)
    return final_state["final_result"]
