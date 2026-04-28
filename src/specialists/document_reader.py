"""
DocumentReader specialist.

Tools: fetch_claim, parse_attachments.
Returns: ClaimSummary(text, amount_eur, claim_type, claimant_id, numero_sinistro).

Receives claim_id and instructions via Task prompt from the coordinator.
Does NOT have access to policy data or fraud rules.

Owner: Person B
"""
