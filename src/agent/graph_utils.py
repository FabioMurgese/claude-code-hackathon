"""
Shared LangGraph utilities: model factory and MaxTokensError.

Owner: Person B
"""

from langchain_anthropic import ChatAnthropic

MODEL = "claude-sonnet-4-6"


class MaxTokensError(Exception):
    """Raised when stop_reason == max_tokens. Caller must escalate the claim."""


def build_chat_model(model: str = MODEL, max_tokens: int = 4096) -> ChatAnthropic:
    return ChatAnthropic(model=model, max_tokens=max_tokens)
