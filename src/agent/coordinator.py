"""
Coordinator agent.

Ingests a claim_id from data/inbox/, launches DocumentReader and PolicyChecker
specialists via Task (passing context explicitly — subagents do NOT inherit
coordinator memory), validates structured output against DecisionSchema with
a retry loop (max 3 attempts), applies escalation rules from
src/escalation_rules.py, and calls write_decision() or escalate_claim().

Owner: Person B
"""
