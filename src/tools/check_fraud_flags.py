"""
Checks claimant_id and incident_date against D.Lgs. 231/2001 mock fraud rules.

Returns fraud_score (0 = clean, >0 = flag present) and a list of triggered rules.
Does NOT access Codice Fiscale, Partita IVA, or IBAN directly — those fields
are blocked by the PreToolUse hook before this tool is ever called.
Does NOT make the final fraud determination — only returns signals.

Error: {"isError": true, "code": "PII_BLOCKED", "guidance": "do not pass Codice Fiscale or IBAN to this tool"}

Owner: Person A
"""
