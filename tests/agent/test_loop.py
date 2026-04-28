"""
loop.py was removed in the LangGraph migration.
MaxTokensError moved to src.agent.graph_utils.
This file is kept as a placeholder so the test directory remains consistent.
"""
from src.agent.graph_utils import MaxTokensError
import pytest


def test_max_tokens_error_importable():
    with pytest.raises(MaxTokensError):
        raise MaxTokensError("truncated")
