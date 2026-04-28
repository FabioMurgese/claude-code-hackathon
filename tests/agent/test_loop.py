from unittest.mock import MagicMock, patch
from src.agent.loop import run_agent_loop, MaxTokensError


def _resp(stop_reason, text="", tool_calls=None):
    r = MagicMock()
    r.stop_reason = stop_reason
    content = []
    if text:
        b = MagicMock(); b.type = "text"; b.text = text
        content.append(b)
    for tc in (tool_calls or []):
        b = MagicMock()
        b.type = "tool_use"; b.id = tc["id"]; b.name = tc["name"]; b.input = tc["input"]
        content.append(b)
    r.content = content
    return r


def test_end_turn_returns_text():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _resp("end_turn", text='{"ok": true}')
    with patch("src.agent.loop.client", mock_client):
        result = run_agent_loop("sys", [], {}, [{"role": "user", "content": "go"}])
    assert result == '{"ok": true}'


def test_max_tokens_raises():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _resp("max_tokens")
    with patch("src.agent.loop.client", mock_client):
        try:
            run_agent_loop("sys", [], {}, [{"role": "user", "content": "go"}])
            assert False, "expected MaxTokensError"
        except MaxTokensError:
            pass


def test_tool_use_calls_function_and_loops():
    calls = {"n": 0}

    def create(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _resp("tool_use", tool_calls=[{"id": "t1", "name": "echo", "input": {"msg": "hi"}}])
        return _resp("end_turn", text='{"done": true}')

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = create
    with patch("src.agent.loop.client", mock_client):
        result = run_agent_loop("sys", [], {"echo": lambda msg: {"echo": msg}}, [{"role": "user", "content": "go"}])
    assert calls["n"] == 2
    assert "done" in result


def test_pre_tool_hook_blocks_call():
    calls = {"n": 0}

    def create(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _resp("tool_use", tool_calls=[{"id": "t2", "name": "danger", "input": {"x": 1}}])
        return _resp("end_turn", text="blocked")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = create
    hook = lambda name, inp: {"isError": True, "code": "BLOCKED", "guidance": "stop"}
    reached = {"called": False}

    def danger(x):
        reached["called"] = True
        return {}

    with patch("src.agent.loop.client", mock_client):
        run_agent_loop("sys", [], {"danger": danger}, [{"role": "user", "content": "go"}], pre_tool_hook=hook)
    assert not reached["called"]
