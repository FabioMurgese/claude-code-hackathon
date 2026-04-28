"""
SafeToolNode: LangGraph-compatible tool executor with pre_tool_use hook.

Wraps check_pre_tool_use before every tool call. Returns ToolMessages.
Replaces the tool-dispatch section of the old run_agent_loop().

Owner: Person B
"""

import json
from langchain_core.messages import ToolMessage
from src.hooks.pre_tool_use import check_pre_tool_use as _default_hook


class SafeToolNode:
    """Callable node for LangGraph that runs tools with the PII/fraud hook."""

    def __init__(self, tools: list, pre_tool_hook=_default_hook):
        self._tool_map = {t.name: t for t in tools}
        self._hook = pre_tool_hook

    def __call__(self, state: dict) -> dict:
        last_msg = state["messages"][-1]
        tool_messages: list[ToolMessage] = []

        for tc in last_msg.tool_calls:
            name, args, tc_id = tc["name"], tc["args"], tc["id"]

            if self._hook:
                blocked = self._hook(name, args)
                if blocked:
                    tool_messages.append(
                        ToolMessage(content=json.dumps(blocked), tool_call_id=tc_id, status="error")
                    )
                    continue

            if name not in self._tool_map:
                err = {"isError": True, "code": "TOOL_NOT_FOUND",
                       "guidance": f"tool '{name}' is not registered"}
                tool_messages.append(
                    ToolMessage(content=json.dumps(err), tool_call_id=tc_id, status="error")
                )
                continue

            result = self._tool_map[name].invoke(args)
            is_err = isinstance(result, dict) and result.get("isError", False)
            tool_messages.append(
                ToolMessage(
                    content=json.dumps(result, ensure_ascii=False),
                    tool_call_id=tc_id,
                    status="error" if is_err else "success",
                )
            )

        return {"messages": tool_messages}
