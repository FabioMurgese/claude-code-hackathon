"""
Agent loop wrapper with stop_reason dispatch.

Runs one isolated Claude agent until end_turn or error.
Task subagents are isolated by constructing a fresh messages list —
they do NOT inherit the coordinator's context (see ADR 001).

stop_reason handling (ADR 001):
  end_turn   → return text output
  tool_use   → call tools (with optional pre_tool_hook), loop
  max_tokens → raise MaxTokensError (caller must escalate — truncated output is untrustworthy)

Owner: Person B
"""

import json
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


class MaxTokensError(Exception):
    """Raised when stop_reason == max_tokens. Caller must escalate the claim."""


def run_agent_loop(
    system: str,
    tools: list[dict],
    tool_functions: dict,
    messages: list[dict],
    pre_tool_hook=None,
    model: str = MODEL,
    max_tokens: int = 4096,
) -> str:
    messages = list(messages)  # local copy — do not mutate caller's list

    while True:
        kwargs: dict = dict(model=model, max_tokens=max_tokens, system=system, messages=messages)
        if tools:
            kwargs["tools"] = tools
        response = client.messages.create(**kwargs)

        if response.stop_reason == "end_turn":
            return "\n".join(b.text for b in response.content if hasattr(b, "text"))

        if response.stop_reason == "max_tokens":
            raise MaxTokensError("agent output truncated — escalating for safety")

        # tool_use — process every tool call in this turn
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if pre_tool_hook:
                blocked = pre_tool_hook(block.name, block.input)
                if blocked:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(blocked),
                        "is_error": True,
                    })
                    continue

            if block.name not in tool_functions:
                err = {"isError": True, "code": "TOOL_NOT_FOUND",
                       "guidance": f"tool '{block.name}' is not registered"}
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(err),
                    "is_error": True,
                })
                continue

            result = tool_functions[block.name](**block.input)
            is_err = isinstance(result, dict) and result.get("isError", False)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False),
                "is_error": is_err,
            })

        messages = messages + [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_results},
        ]
