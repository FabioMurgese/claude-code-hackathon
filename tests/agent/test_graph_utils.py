import pytest
from unittest.mock import patch, MagicMock
from src.agent.graph_utils import MaxTokensError, build_chat_model, MODEL


def test_model_constant_is_string():
    assert isinstance(MODEL, str) and MODEL


def test_build_chat_model_returns_bound_model():
    with patch("src.agent.graph_utils.ChatBedrockConverse") as mock_cls:
        mock_cls.return_value = MagicMock(spec=["invoke", "bind_tools"])
        llm = build_chat_model()
    assert hasattr(llm, "invoke")


def test_max_tokens_error_is_exception():
    with pytest.raises(MaxTokensError):
        raise MaxTokensError("truncated")
