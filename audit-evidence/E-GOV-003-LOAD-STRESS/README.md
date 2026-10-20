Skip to content
butnee-sys
gerchain
Repository navigation
Code
Issues
6
 (6)
Pull requests
27
 (27)
Discussions
Actions
Projects
Wiki
Security and quality
Insights
Settings
Commit 4168bb1
butnee-sys
butnee-sys
authored
17 minutes ago
·
·
Verified
Update README.md
main
1 parent 
600c28e
 commit 
4168bb1
1 file changed

+2
-2
Lines changed: 2 additions & 2 deletions
File tree
Filter files…
audit-evidence/E-GOV-003-LOAD-STRESS
README.md
1
Search within code
 
‎audit-evidence/E-GOV-003-LOAD-STRESS/README.md‎
+2
-2
Lines changed: 2 additions & 2 deletions


Original file line number	Diff line number	Diff line change
@@ -1,37 +1,37 @@
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
- **API Stress Test Script:** [`/test_gerchain_api.sh`](../../../test_gerchain_api.sh)
- **End-to-End Flow Script:** [`/test_gerchain_e2e.sh`](../../../test_gerchain_e2e.sh)
Comment on line R26
butnee-sys commented 3 minutes ago
@butnee-sys
butnee-sys
3m ago
Owner
Author
test_gerchain

Write a reply
- **API Stress Test Script:** [test_gerchain_api.sh](../../../test_gerchain_api.sh)
- **End-to-End Flow Script:** [test_gerchain_e2e.sh](../../../test_gerchain_e2e.sh)
- **Evidence Review Date:** 2026-10-20

---

## 4. Data Source & Authority Matrix (Load & Stress Layer)

| Бүрэлдэхүүн / Тест | Өгөгдлийн эх сурвалж (Data Source) | Баталгаажуулах механизм | Эрх мэдлийн эзэн (System Authority) |
| :--- | :--- | :--- | :--- |
| **API Load Testing** | `test_gerchain_api.sh` Execution Log | Automated Shell Probing | Lead Architect (`@butnee-sys`) |
| **E2E Transaction Flow** | `test_gerchain_e2e.sh` Test Runner | Multi-Endpoint E2E Validation | Gerchain Core System Engine |
| **Database Concurrency** | PostgreSQL Lock Logs & Unit Suite | Pytest Parallel Execution | Core Database Administrator |
0 commit comments
Comments
0
 (0)
Comment
You're receiving notifications because you're subscribed to this thread.

