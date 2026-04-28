"""
DocumentReader specialist — LangGraph implementation.

Tools: fetch_claim, parse_attachments.
Returns: ClaimSummary dict.

Graph: HumanMessage → llm_node ↔ safe_tools (cycle) → end_turn → return JSON.
Context isolation: fresh state per invocation (no shared coordinator context).

## Key Decision
_llm is initialised lazily (None at import time) so that importing this module
does not require AWS credentials. Credentials are only resolved on the first
actual run_document_reader() call.

Owner: Person B
"""

import json
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from src.agent.graph_utils import build_chat_model, MaxTokensError, extract_json_str
from src.agent.tools_node import SafeToolNode
from src.tools.fetch_claim import fetch_claim
from src.tools.parse_attachments import parse_attachments

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

_tools = [
    StructuredTool.from_function(fetch_claim, name="fetch_claim", description="Reads summary.txt and metadata.json"),
    StructuredTool.from_function(parse_attachments, name="parse_attachments", description="Extracts text from PDFs/images"),
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
            raise MaxTokensError("DocumentReader output truncated")
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


def run_document_reader(claim_id: str) -> dict:
    """Run DocumentReader in isolated context — fresh state, no coordinator memory."""
    init_messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=(
            f"Processa il sinistro claim_id='{claim_id}'. "
            "Usa fetch_claim per leggere i dati, poi restituisci il JSON ClaimSummary."
        )),
    ]
    final_state = _graph.invoke({"messages": init_messages})
    last_ai = next(
        m for m in reversed(final_state["messages"]) if isinstance(m, AIMessage)
    )
    return json.loads(extract_json_str(last_ai.content))
