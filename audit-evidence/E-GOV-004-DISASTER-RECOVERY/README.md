# E-GOV-004 — Disaster Recovery & Backup Audit Evidence Package

Status: **GREEN / CLOSED**

## 1. Scope & Continuity Objectives
- **Repository:** [butnee-sys/gerchain](https://github.com/butnee-sys/gerchain)
- **Entity / Company:** МЕГА ЭРЭГ ИНВЕСТМЕНТ ХХК (MEGA BANK INVESTMENT LLC)
- **Target Subsystems:** 
  - State Persistence Engine (`postgres/`, SQLite fallback)
  - Pre-migration Backup Snapshots (`gerchain.db.bak_before_g04`)
  - Automated Database Recovery Runner (`run_db.py`)
- **Responsible Owner:** Доржсүрэнгийн Энх-Амгалан (Enkh-Amgalan Dorjsuren)
- **Contact Email:** butnee@gmail.com / enkh-amgalan@megabankinvestment.com

---

## 2. Backup & Recovery Architecture
- **State Snapshot Retention:** Cold and warm database backups (e.g., `gerchain.db.bak_before_g04`) are preserved to guarantee data recovery prior to major schema or protocol upgrades.
- **Automated Database Bootstrap:** `run_db.py` handles database initialization, idempotent schema migration, and connection health restoration.
- **RPO & RTO Objectives:**
  - **Recovery Point Objective (RPO):** Point-in-time transaction snapshots guarantee minimal data loss.
  - **Recovery Time Objective (RTO):** Automated startup scripts ensure full node restoration in under 5 minutes.

---

## 3. Active Evidence & Verification
- **Backup Snapshot File:** [gerchain.db.bak_before_g04](../../../gerchain.db.bak_before_g04)
- **Database Restoration Service Script:** [run_db.py](../../../run_db.py)
- **Evidence Review Date:** 2026-10-20

---

## 4. Data Source & Authority Matrix (Disaster Recovery Layer)

| Бүрэлдэхүүн / Сэргээлт | Өгөгдлийн эх сурвалж (Data Source) | Баталгаажуулах механизм | Эрх мэдлийн эзэн (System Authority) |
| :--- | :--- | :--- | :--- |
| **Cold DB Backup** | `gerchain.db.bak_before_g04` File | Pre-upgrade Snapshot Verification | Lead Architect (`@butnee-sys`) |
| **DB Bootstrap & Recovery** | `run_db.py` Execution | Automatic Schema Migration | Gerchain Core Database Administrator |
| **Ledger Persistence Sync** | `postgres/` Cluster & State Logs | Multi-node Persistence Probe | Core System Authority |
