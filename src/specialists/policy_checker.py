"""
PolicyChecker specialist — LangGraph implementation.

Tools: lookup_policy, check_fraud_flags, check_sanctions.
Returns: PolicyResult dict.

Graph: HumanMessage → llm_node ↔ safe_tools (cycle) → end_turn → return JSON.
Context isolation: fresh state per invocation.

## Key Decision
_llm is initialised lazily (None at import time) so that importing this module
does not require AWS credentials. Credentials are only resolved on the first
actual run_policy_checker() call.

Owner: Person B
"""

import json
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from src.agent.graph_utils import build_chat_model, MaxTokensError
from src.agent.tools_node import SafeToolNode
from src.tools.lookup_policy import lookup_policy
from src.tools.check_fraud_flags import check_fraud_flags
from src.tools.check_sanctions import check_sanctions

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

_tools = [
    StructuredTool.from_function(lookup_policy, name="lookup_policy", description="Verifica polizza"),
    StructuredTool.from_function(check_fraud_flags, name="check_fraud_flags", description="Controlla flag D.Lgs. 231/2001"),
    StructuredTool.from_function(check_sanctions, name="check_sanctions", description="Controlla lista sanzioni EU/UN"),
]
_safe_tools = SafeToolNode(_tools)
_llm = None  # lazy — built on first call to avoid import-time AWS credential check


def _get_llm():
    global _llm
    if _llm is None:
        _llm = build_chat_model().bind_tools(_tools)
    return _llm


class _State(TypedDict):
    messages: Annotated[list, add_messages]


def _llm_node(state: _State) -> dict:
    response = _get_llm().invoke(state["messages"])
    if isinstance(response, AIMessage):
        meta = response.response_metadata or {}
        if meta.get("stop_reason") == "max_tokens":
            raise MaxTokensError("PolicyChecker output truncated")
    return {"messages": [response]}


def _route(state: _State) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


_graph = (
    StateGraph(_State)
    .add_node("llm", _llm_node)
    .add_node("tools", _safe_tools)
    .add_edge("tools", "llm")
    .set_entry_point("llm")
    .add_conditional_edges("llm", _route)
    .compile()
)


def run_policy_checker(claim_summary: dict) -> dict:
    """Run PolicyChecker in isolated context — receives ClaimSummary explicitly."""
    init_messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=(
            f"Verifica copertura per questo sinistro: {json.dumps(claim_summary, ensure_ascii=False)}. "
            "Usa gli strumenti disponibili e restituisci il JSON PolicyResult."
        )),
    ]
    final_state = _graph.invoke({"messages": init_messages})
    last_ai = next(
        m for m in reversed(final_state["messages"]) if isinstance(m, AIMessage)
    )
    return json.loads(last_ai.content)
