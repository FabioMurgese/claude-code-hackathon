"""
Writes a decision record to data/decisions/<claim_id>.json and appends to the
decision log.

Required schema: {claim_id, decision, category, confidence, rationale, timestamp, retry_count}
decision must be one of: fast_track, investigate, deny, auto_resolve.

Does NOT handle escalations — use escalate_claim() for those.
Does NOT write to frozen polizze (blocked by PreToolUse hook).
Does NOT approve claims with fraud_score > 0 (blocked by PreToolUse hook).

Error: {"isError": true, "code": "SCHEMA_INVALID", "guidance": "required fields: claim_id, decision, category, confidence, rationale"}

Owner: Person A
"""
