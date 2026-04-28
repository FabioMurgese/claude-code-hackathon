"""
Fixes eval data issues introduced during generation:
  1. Adversarial claims use fake POL-XXXXX policy IDs → maps to real ones by category
  2. Creates data/inbox/ folders for all 60 eval claims (required by fetch_claim)

Run once after 'git pull'. Safe to re-run (idempotent).
"""
import json
from pathlib import Path

EVAL  = Path("data/eval")
INBOX = Path("data/inbox")

_CATEGORY_TO_POLICY = {
    "auto":        "RCA_auto",
    "casa":        "incendio_casa",
    "salute":      "infortuni",
    "infortuni":   "infortuni",
    "professionale": "RC_professionale",
    "vita":        "polizza_vita",
}
_FALLBACK_POLICY = "RCA_auto"


def fix_policy_ids(records: list[dict]) -> tuple[list[dict], int]:
    fixed = 0
    valid = {"RCA_auto", "incendio_casa", "infortuni", "RC_professionale", "polizza_vita"}
    result = []
    for r in records:
        r = dict(r)
        if r.get("policy_id") not in valid:
            new_pid = _CATEGORY_TO_POLICY.get(r.get("category", ""), _FALLBACK_POLICY)
            r["policy_id"] = new_pid
            fixed += 1
        result.append(r)
    return result, fixed


def write_inbox(records: list[dict]) -> int:
    created = 0
    for item in records:
        folder = INBOX / item["id"]
        folder.mkdir(parents=True, exist_ok=True)
        meta = {k: v for k, v in item.items()
                if k not in ("summary_it", "notes", "expected_decision", "adversarial_type", "category")}
        meta["claim_id"] = item["id"]
        (folder / "metadata.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (folder / "summary.txt").write_text(item.get("summary_it", ""), encoding="utf-8")
        created += 1
    return created


def main() -> None:
    normal = [json.loads(l) for l in (EVAL / "normal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    adv    = [json.loads(l) for l in (EVAL / "adversarial.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

    # Fix adversarial policy IDs
    adv_fixed, n_fixed = fix_policy_ids(adv)
    if n_fixed:
        (EVAL / "adversarial.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in adv_fixed), encoding="utf-8"
        )
        print(f"Fixed {n_fixed} adversarial policy IDs")
    else:
        print("Adversarial policy IDs already valid — no changes")

    # Create inbox folders for all eval claims
    n_created = write_inbox(normal) + write_inbox(adv_fixed)
    print(f"Created/updated {n_created} inbox folders")

    # Verify
    missing = [r["id"] for r in normal + adv_fixed if not (INBOX / r["id"] / "metadata.json").exists()]
    print(f"Verification — missing inbox folders: {missing or 'none'}")


if __name__ == "__main__":
    main()
