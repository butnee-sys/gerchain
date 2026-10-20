# E-GOV-003 — Load & Stress Testing Audit Evidence Package

Status: **GREEN / CLOSED**

## 1. Scope & System Performance Objectives
- **Repository:** [butnee-sys/gerchain](https://github.com/butnee-sys/gerchain)
- **Entity / Company:** МЕГА ЭРЭГ ИНВЕСТМЕНТ ХХК (MEGA BANK INVESTMENT LLC)
- **Target Subsystems:** 
  - Gerchain REST API Core Endpoints (`production_entrypoint.py`)
  - End-to-End Transaction Flow (`test_gerchain_e2e.sh`)
  - Automated Stress Probing Suite (`test_gerchain_api.sh`)
- **Responsible Owner:** Доржсүрэнгийн Энх-Амгалан (Enkh-Amgalan Dorjsuren)
- **Contact Email:** butnee@gmail.com / enkh-amgalan@megabankinvestment.com

---

## 2. Load & Concurrency Architecture
- **Automated API Testing:** `test_gerchain_api.sh` runs concurrent request probes to verify endpoint response consistency and latency limits.
- **End-to-End Stress Validation:** `test_gerchain_e2e.sh` simulates multi-node transaction flows and state transitions under peak load.
- **PostgreSQL Concurrency Protection:** Lock/retry mechanisms inside `postgres/` ensure transactional consistency under concurrent writes.

---

## 3. Active Evidence & Verification
- **API Stress Test Script:** [`/test_gerchain_api.sh`](../../test_gerchain_api.sh)
- **End-to-End Flow Script:** [`/test_gerchain_e2e.sh`](../../test_gerchain_e2e.sh)
- **Evidence Review Date:** 2026-10-20

---

## 4. Data Source & Authority Matrix (Load & Stress Layer)

| Бүрэлдэхүүн / Тест | Өгөгдлийн эх сурвалж (Data Source) | Баталгаажуулах механизм | Эрх мэдлийн эзэн (System Authority) |
| :--- | :--- | :--- | :--- |
| **API Load Testing** | `test_gerchain_api.sh` Execution Log | Automated Shell Probing | Lead Architect (`@butnee-sys`) |
| **E2E Transaction Flow** | `test_gerchain_e2e.sh` Test Runner | Multi-Endpoint E2E Validation | Gerchain Core System Engine |
| **Database Concurrency** | PostgreSQL Lock Logs & Unit Suite | Pytest Parallel Execution | Core Database Administrator |
