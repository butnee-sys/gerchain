#!/usr/bin/env bash

BASE="http://127.0.0.1:8000"

echo "======================================================"
echo " GERCHAIN + NEF RWA END-TO-END TEST"
echo "======================================================"
echo

echo "[1/8] RWA REGISTER"
RWA=$(curl -sS -X POST "$BASE/api/v1/rwa/register" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_code": "TEST-E2E-RWA-001",
    "asset_type": "Live Animal / Livestock",
    "location": "Dundgovi Province",
    "valuation_nef": 1000000
  }')

echo "$RWA"
echo
echo "------------------------------------------------------"

echo "[2/8] ESCROW CREATE"
ESCROW=$(curl -sS -X POST "$BASE/api/v1/escrow/create" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "TEST-E2E-ESCROW-001",
    "owner_name": "Gerchain E2E Test Owner",
    "initial_balance_nef": 1000000
  }')

echo "$ESCROW"
echo
echo "------------------------------------------------------"

echo "[3/8] ESCROW TRANSFER"
TRANSFER=$(curl -sS -X POST "$BASE/api/v1/escrow/transfer" \
  -H "Content-Type: application/json" \
  -d '{
    "from_account": "NEF-ESCROW-001",
    "to_account": "HERDER-ACC-05",
    "amount_nef": 100,
    "milestone_ref": "TEST-E2E-MILESTONE-001"
  }')

echo "$TRANSFER"
echo
echo "------------------------------------------------------"

echo "[4/8] EVIDENCE SUBMIT"
EVIDENCE=$(curl -sS -X POST "$BASE/api/v1/evidence/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "milestone_ref": "TEST-E2E-MILESTONE-001",
    "asset_code": "TEST-E2E-RWA-001",
    "herder_account": "HERDER-ACC-05",
    "gps_coordinates": "45.1234,106.5678",
    "photo_url": "https://example.com/test-evidence.jpg",
    "commission_act_ref": "TEST-E2E-ACT-001"
  }')

echo "$EVIDENCE"
echo
echo "------------------------------------------------------"

echo "[5/8] VERIFY"
VERIFY=$(curl -sS -X POST "$BASE/api/v1/evidence/verify-and-release" \
  -H "Content-Type: application/json" \
  -d '{
    "milestone_ref": "TEST-E2E-MILESTONE-001",
    "approved": true,
    "amount_nef": 100,
    "verifier_notes": "Gerchain E2E integration test approved"
  }')

echo "$VERIFY"
echo
echo "------------------------------------------------------"

echo "[6/8] AUDIT LOG"
AUDIT=$(curl -sS "$BASE/api/v1/audit/logs")

echo "$AUDIT"
echo
echo "------------------------------------------------------"

echo "[7/8] RWA STATUS"
RWA_STATUS=$(curl -sS "$BASE/api/v1/rwa/status")

echo "$RWA_STATUS"
echo
echo "------------------------------------------------------"

echo "[8/8] DASHBOARD"
DASHBOARD=$(curl -sS -o /tmp/gerchain_dashboard.html \
  -w "HTTP_STATUS=%{http_code}\nCONTENT_TYPE=%{content_type}\n" \
  "$BASE/dashboard")

echo "$DASHBOARD"

echo
echo "======================================================"
echo " END-TO-END TEST COMPLETE"
echo "======================================================"
