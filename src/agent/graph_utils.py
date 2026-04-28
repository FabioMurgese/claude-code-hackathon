"""
Shared LangGraph utilities: model factory and MaxTokensError.

Uses AWS Bedrock via langchain-aws (ChatBedrockConverse).
Credentials are resolved from the AWS CLI / environment (no Anthropic API key needed).

Owner: Person B
"""

from langchain_aws import ChatBedrockConverse

MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


class MaxTokensError(Exception):
    """Raised when stop_reason == max_tokens. Caller must escalate the claim."""


def build_chat_model(model: str = MODEL, max_tokens: int = 4096) -> ChatBedrockConverse:
    return ChatBedrockConverse(model=model, max_tokens=max_tokens)
