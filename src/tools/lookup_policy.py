import json
from pathlib import Path

POLICIES_PATH = Path("data/policies")

LOOKUP_POLICY_SCHEMA = {
    "name": "lookup_policy",
    "description": (
        "Reads the policy JSON from data/policies/<policy_id>.json. "
        "Returns coverage type, exclusions, limits, valid dates, and status. "
        "Does NOT interpret coverage ambiguity — that is PolicyChecker's job, not this tool. "
        "Does NOT modify policies. "
        "Example: lookup_policy(policy_id='RCA_auto')"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "policy_id": {
                "type": "string",
                "description": "Policy ID matching a filename in data/policies/ (without .json). "
                               "E.g. 'RCA_auto', 'infortuni'.",
            }
        },
        "required": ["policy_id"],
    },
}


def lookup_policy(policy_id: str) -> dict:
    path = POLICIES_PATH / f"{policy_id}.json"
    if not path.exists():
        available = [f.stem for f in POLICIES_PATH.glob("*.json")]
        return {"isError": True, "code": "POLICY_NOT_FOUND",
                "guidance": f"check policy_id in data/policies/ — available: {available}"}
    return json.loads(path.read_text(encoding="utf-8"))
