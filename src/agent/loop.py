"""
Agent loop wrapper.

Handles stop_reason dispatch for the coordinator:
  end_turn   → return text
  tool_use   → continue the agent loop
  max_tokens → raise MaxTokensError (caller escalates — truncated output is untrustworthy)

Owner: Track B (Matteo)
"""


class MaxTokensError(Exception):
    """Raised on max_tokens stop_reason — caller must escalate."""


def run_agent_loop(
    system: str,
    tools: list[dict],
    tool_functions: dict,
    messages: list[dict],
    pre_tool_hook=None,
    model: str = "eu.anthropic.claude-sonnet-4-5-20251001-v1:0",
    max_tokens: int = 4096,
) -> str:
    """Run one isolated agent until end_turn or error. Implemented in Track B."""
    raise NotImplementedError("run_agent_loop is implemented in Track B (src/agent/loop.py)")
