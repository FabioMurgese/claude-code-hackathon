"""Creates 15 deterministic development inbox fixtures."""
import json
from pathlib import Path

INBOX = Path("data/inbox")
INBOX.mkdir(parents=True, exist_ok=True)

FIXTURES = [
    # Fast-track (5)
    {"id": "CLM-001", "policy_id": "RCA_auto", "amount_eur": 800.0, "claim_type": "sinistro_auto",
     "claimant_id": "CLT-001", "frozen": False, "numero_sinistro": "NS-2024-001",
     "incident_date": "2024-11-10", "in_contenzioso": False,
     "summary": "Tamponamento lieve in via Roma 12. Danno paraurti posteriore €800. Polizza RCA valida, nessuna esclusione applicabile."},
    {"id": "CLM-002", "policy_id": "infortuni", "amount_eur": 1200.0, "claim_type": "infortunio_lavoro",
     "claimant_id": "CLT-002", "frozen": False, "numero_sinistro": "NS-2024-002",
     "incident_date": "2024-10-05", "in_contenzioso": False,
     "summary": "Distorsione caviglia durante attività lavorativa ordinaria. Certificato medico allegato. Polizza infortuni attiva."},
    {"id": "CLM-003", "policy_id": "RC_professionale", "amount_eur": 3000.0, "claim_type": "rc_professionale",
     "claimant_id": "CLT-003", "frozen": False, "numero_sinistro": "NS-2024-003",
     "incident_date": "2024-09-20", "in_contenzioso": False,
     "summary": "Errore nella relazione tecnica. Danno quantificato €3.000. Nessuna violazione del segreto professionale."},
    {"id": "CLM-004", "policy_id": "RCA_auto", "amount_eur": 2400.0, "claim_type": "sinistro_auto",
     "claimant_id": "CLT-004", "frozen": False, "numero_sinistro": "NS-2024-004",
     "incident_date": "2024-08-14", "in_contenzioso": False,
     "summary": "Incidente in parcheggio. Danno carrozzeria lato destro €2.400. Patente valida, polizza RCA attiva."},
    {"id": "CLM-005", "policy_id": "polizza_vita", "amount_eur": 500.0, "claim_type": "rimborso_spese",
     "claimant_id": "CLT-005", "frozen": False, "numero_sinistro": "NS-2024-005",
     "incident_date": "2024-07-01", "in_contenzioso": False,
     "summary": "Rimborso spese mediche post-intervento €500. Polizza vita con copertura spese mediche attiva."},
    # Deny (4)
    {"id": "CLM-006", "policy_id": "incendio_casa", "amount_eur": 12000.0, "claim_type": "incendio",
     "claimant_id": "CLT-006", "frozen": False, "numero_sinistro": "NS-2024-006",
     "incident_date": "2024-06-15", "in_contenzioso": False,
     "summary": "Incendio in cucina. Polizza incendio_casa scaduta al 31/05/2025. Sinistro avvenuto dopo la scadenza."},
    {"id": "CLM-007", "policy_id": "RCA_auto", "amount_eur": 4500.0, "claim_type": "sinistro_auto",
     "claimant_id": "CLT-007", "frozen": False, "numero_sinistro": "NS-2024-007",
     "incident_date": "2024-05-20", "in_contenzioso": False,
     "summary": "Incidente stradale. Conducente sprovvisto di patente al momento del sinistro. Esclusione guida_senza_patente applicabile."},
    {"id": "CLM-008", "policy_id": "infortuni", "amount_eur": 8000.0, "claim_type": "infortunio_lavoro",
     "claimant_id": "CLT-008", "frozen": False, "numero_sinistro": "NS-2024-008",
     "incident_date": "2024-04-01", "in_contenzioso": False,
     "summary": "Infortunio durante pratica di paracadutismo (sport estremo). Esclusione sport_estremi applicabile."},
    {"id": "CLM-009", "policy_id": "RCA_auto", "amount_eur": 1100.0, "claim_type": "sinistro_auto",
     "claimant_id": "CLT-009", "frozen": False, "numero_sinistro": "NS-2024-001",
     "incident_date": "2024-11-10", "in_contenzioso": False,
     "summary": "Sinistro numero NS-2024-001 già liquidato in precedenza. Richiesta duplicata."},
    # Investigate / borderline (4)
    {"id": "CLM-010", "policy_id": "RC_professionale", "amount_eur": 6500.0, "claim_type": "rc_professionale",
     "claimant_id": "CLT-010", "frozen": False, "numero_sinistro": "NS-2024-010",
     "incident_date": "2024-03-10", "in_contenzioso": False,
     "summary": "Errore professionale con danno a terzi €6.500. Importo sopra soglia. Clausola interpretabile."},
    {"id": "CLM-011", "policy_id": "polizza_vita", "amount_eur": 7200.0, "claim_type": "sinistro_vita",
     "claimant_id": "CLT-011", "frozen": False, "numero_sinistro": "NS-2024-011",
     "incident_date": "2024-02-14", "in_contenzioso": False,
     "summary": "Richiesta liquidazione parziale €7.200. Importo sopra soglia €5.000."},
    {"id": "CLM-012", "policy_id": "RCA_auto", "amount_eur": 4800.0, "claim_type": "contestazione",
     "claimant_id": "CLT-012", "frozen": False, "numero_sinistro": "NS-2024-012",
     "incident_date": "2024-01-25", "in_contenzioso": False,
     "summary": "Assicurato contesta liquidazione parziale precedente. Richiesta revisione €4.800."},
    {"id": "CLM-013", "policy_id": "incendio_casa", "amount_eur": 2200.0, "claim_type": "incendio",
     "claimant_id": "CLT-013", "frozen": False, "numero_sinistro": "NS-2024-013",
     "incident_date": "2023-12-01", "in_contenzioso": False,
     "summary": "Danno da incendio €2.200. Data sinistro prima della scadenza polizza — copertura da verificare."},
    # Edge cases (2)
    {"id": "CLM-014", "policy_id": "RCA_auto", "amount_eur": 3300.0, "claim_type": "sinistro_auto",
     "claimant_id": "CLT-014", "frozen": True, "numero_sinistro": "NS-2024-014",
     "incident_date": "2024-11-30", "in_contenzioso": False,
     "summary": "Sinistro auto €3.300. Attenzione: polizza contrassegnata come frozen nel sistema."},
    {"id": "CLM-015", "policy_id": "RC_professionale", "amount_eur": 15000.0, "claim_type": "rc_professionale",
     "claimant_id": "CLT-FRAUD-001", "frozen": False, "numero_sinistro": "NS-2024-015",
     "incident_date": "2024-11-05", "in_contenzioso": True,
     "summary": "Richiesta RC professionale €15.000. Pratica in contenzioso. Claimant ha segnalazioni precedenti."},
]

for f in FIXTURES:
    folder = INBOX / f["id"]
    folder.mkdir(parents=True, exist_ok=True)
    metadata = {k: v for k, v in f.items() if k not in ("id", "summary")}
    metadata["claim_id"] = f["id"]
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "summary.txt").write_text(f["summary"], encoding="utf-8")

print(f"Created {len(FIXTURES)} fixtures in data/inbox/")
