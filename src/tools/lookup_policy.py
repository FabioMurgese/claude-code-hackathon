"""
Reads policy JSON from data/policies/<policy_id>.json.

Returns raw policy text. Does NOT interpret coverage ambiguity — that is
the PolicyChecker specialist's job, not this tool's. Does NOT modify policies.

Error: {"isError": true, "code": "POLICY_NOT_FOUND", "guidance": "check policy_id in data/policies/"}

Owner: Person A
"""
