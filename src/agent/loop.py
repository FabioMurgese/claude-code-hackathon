"""
Agent loop wrapper.

Handles stop_reason dispatch for the coordinator:
  end_turn  → return result and log decision
  tool_use  → continue the agent loop
  max_tokens → escalate (safety default — truncated output is untrustworthy)

Owner: Person B
"""
