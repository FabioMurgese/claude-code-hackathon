import json
import pytest
from langchain_core.messages import AIMessage, ToolMessage
from src.agent.tools_node import SafeToolNode
from langchain_core.tools import StructuredTool


def _make_echo_tool():
    def echo(text: str) -> dict:
        return {"echo": text}
    return StructuredTool.from_function(echo, name="echo", description="echoes text")


def test_safe_tool_node_calls_tool():
    tool = _make_echo_tool()
    node = SafeToolNode([tool])
    ai_msg = AIMessage(content="", tool_calls=[{"id": "tc1", "name": "echo", "args": {"text": "hello"}}])
    result = node({"messages": [ai_msg]})
    tool_msgs = result["messages"]
    assert len(tool_msgs) == 1
    assert isinstance(tool_msgs[0], ToolMessage)
    assert json.loads(tool_msgs[0].content) == {"echo": "hello"}


def test_safe_tool_node_blocks_pii():
    tool = _make_echo_tool()

    def always_block(name, args):
        return {"isError": True, "code": "GDPR_PII_BLOCKED", "guidance": "blocked"}

    node = SafeToolNode([tool], pre_tool_hook=always_block)
    ai_msg = AIMessage(content="", tool_calls=[{"id": "tc2", "name": "echo", "args": {"text": "CF123"}}])
    result = node({"messages": [ai_msg]})
    msg = result["messages"][0]
    assert json.loads(msg.content)["isError"] is True


def test_safe_tool_node_unknown_tool():
    node = SafeToolNode([])
    ai_msg = AIMessage(content="", tool_calls=[{"id": "tc3", "name": "ghost", "args": {}}])
    result = node({"messages": [ai_msg]})
    msg = result["messages"][0]
    assert json.loads(msg.content)["code"] == "TOOL_NOT_FOUND"
