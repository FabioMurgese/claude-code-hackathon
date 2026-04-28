# Agent Mandate: Insurance Claims Intake

## Decides alone

| Condition | Decision |
|---|---|
| Clear IVASS coverage, amount < €5 000, no fraud flags, valid polizza | `fast_track` |
| Polizza scaduta, esclusione esplicita applicabile | `deny` |
| Sinistro già liquidato (duplicate numero sinistro) | `auto_resolve` |

## Escalates to human

| Trigger | Reason |
|---|---|
| `amount_eur >= 5000` | Euro impact too high for autonomous decision |
| `confidence < 0.75` | Model uncertainty — human review required |
| `fraud_score > 0` | Any D.Lgs. 231/2001 indicator present |
| `sanctions_hit == true` | EU or UN sanctions list match on claimant |
| `coverage_status == "ambiguous"` | Polizza silente sul tipo di evento |
| `claim_type == "contestazione"` | Claimant disputes a prior decision |

## Never touches

- Codice Fiscale or Partita IVA in any output field or log
- IBAN or coordinate bancarie
- Polizze with `frozen=true` in metadata
- Any routing toward external systems or parties
- Override of a human escalation decision after it has been made

## Deliberately not automated

- Final legal liability assessment — requires licensed adjuster under IVASS regulation
- Policy modifications of any kind
- Communication directly with the claimant — all outbound contact goes through the human queue
- Fraud investigation beyond flag-and-escalate — actual investigation is a human task
- Claims involving litigation (`in_contenzioso=true`)

## Key Decision

Thresholds are explicit numbers (€5 000, confidence 0.75) rather than vague guidance ("when the agent isn't sure"). Explicit thresholds produce consistent, auditable escalation behavior that can be reviewed by IVASS and Legal. They also make the eval harness deterministic: the scorecard can distinguish correct escalations from needless ones because the rule is unambiguous.
