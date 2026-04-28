"""
PolicyChecker specialist.

Tools: lookup_policy, check_fraud_flags, check_sanctions.
Returns: PolicyResult(coverage_status, fraud_score, exclusions, sanctions_hit).

Receives a serialized ClaimSummary via Task prompt — never sees raw coordinator
context. Does NOT have access to inbox files.

Owner: Person B
"""
