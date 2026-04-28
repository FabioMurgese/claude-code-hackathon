# ADR 001 — Agent Architecture

## Status
Accepted

## Context
We need to triage Italian insurance claims from a local inbox directory. Each claim requires document parsing, policy lookup, fraud checking, and a final routing decision. The full flow has two distinct knowledge domains (document parsing vs. policy reasoning) and a hard requirement that PII never leaks outside the system. We are using the Claude Agent SDK (Python).

## Decision

### Coordinator + specialist split

```
Coordinator
  │
  ├─ Task → DocumentReader specialist
  │           tools: fetch_claim, parse_attachments
  │           returns: ClaimSummary
  │
  ├─ Task → PolicyChecker specialist
  │           tools: lookup_policy, check_fraud_flags, check_sanctions
  │           receives: ClaimSummary (explicit, in Task prompt)
  │           returns: PolicyResult
  │
  ├─ validate output (retry ≤ 3, schema error fed back each time)
  │
  └─ escalate_claim() OR write_decision()
```

### Coordinator responsibilities
- Ingests `claim_id` from `data/inbox/`
- Launches specialists via Task, passing context explicitly in each prompt
- Runs validation-retry loop on structured output (max 3 retries)
- Applies escalation rules from `src/escalation_rules.py`
- Writes reasoning chain to `data/decisions/<claim_id>.json`

### stop_reason handling
| stop_reason | Action |
|---|---|
| `end_turn` | Return result and log decision |
| `tool_use` | Continue the agent loop |
| `max_tokens` | Escalate (safety default — truncated output is untrustworthy) |

### Context passing
Task subagents in the Claude Agent SDK do NOT inherit the coordinator's context. Every Task prompt must include all context the specialist needs:
- DocumentReader receives: `claim_id`, inbox path, instructions
- PolicyChecker receives: serialized `ClaimSummary`, policy lookup instructions

This is not optional. Omitting context causes silent failures where the specialist hallucinates missing fields.

## Consequences
- Each specialist has ≤ 5 tools, keeping tool-selection reliability high
- DocumentReader has no access to policy data; PolicyChecker has no access to raw files — clear separation of concerns
- The validation-retry loop catches schema errors before they propagate to the decision log
- `max_tokens → escalate` means we never silently produce a truncated decision

## Key Decision
The coordinator + specialist split was chosen over a single monolithic agent because the two knowledge domains (document parsing vs. policy reasoning) have different tool sets and different failure modes. Keeping them separate makes each one easier to test, easier to reason about, and easier to replace if the policy rules change.
