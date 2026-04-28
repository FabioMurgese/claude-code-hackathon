"""
Shared LangGraph utilities: model factory and MaxTokensError.

Uses AWS Bedrock via langchain-aws (ChatBedrockConverse).
Credentials are resolved from the AWS CLI / environment (no Anthropic API key needed).

Owner: Person B
"""

import re

from langchain_aws import ChatBedrockConverse

MODEL = "eu.anthropic.claude-sonnet-4-6"

_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)


class MaxTokensError(Exception):
    """Raised when stop_reason == max_tokens. Caller must escalate the claim."""


def build_chat_model(model: str = MODEL, max_tokens: int = 4096) -> ChatBedrockConverse:
    return ChatBedrockConverse(model=model, max_tokens=max_tokens)


def extract_json_str(content) -> str:
    """Extract JSON from model output, handling prose preambles and markdown fences."""
    if isinstance(content, list):
        content = "".join(
            b.get("text", "") if isinstance(b, dict) else str(b)
            for b in content
            if not isinstance(b, dict) or b.get("type") == "text"
        )
    # Prefer content inside a code fence (may have preamble text before it)
    m = _FENCE_RE.search(content)
    if m:
        return m.group(1).strip()
    # Fall back: find the first JSON object/array in the string
    for opener in ("{", "["):
        idx = content.find(opener)
        if idx >= 0:
            return content[idx:]
    return content
