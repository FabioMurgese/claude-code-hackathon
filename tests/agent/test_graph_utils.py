import pytest
from src.agent.graph_utils import MaxTokensError, build_chat_model, MODEL


def test_model_constant_is_string():
    assert isinstance(MODEL, str) and MODEL


def test_build_chat_model_returns_bound_model():
    llm = build_chat_model()
    assert hasattr(llm, "invoke")


def test_max_tokens_error_is_exception():
    with pytest.raises(MaxTokensError):
        raise MaxTokensError("truncated")
