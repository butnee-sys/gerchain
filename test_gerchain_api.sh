#!/usr/bin/env bash

BASE="http://127.0.0.1:8000"

echo "=========================================="
echo " GERCHAIN + NEF RWA API FUNCTIONAL TEST"
echo "=========================================="
echo

echo "[1/9] RWA STATUS"
curl -sS -i "$BASE/api/v1/rwa/status"
echo
echo "------------------------------------------"

echo "[2/9] RWA REGISTER"
curl -sS -i -X POST "$BASE/api/v1/rwa/register" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "TEST-RWA-001",
    "asset_type": "livestock",
    "owner_id": "TEST-OWNER-001",
    "description": "Gerchain integration test asset",
    "quantity": 1,
    "unit": "head"
  }'
echo
echo "------------------------------------------"

echo "[3/9] ESCROW STATUS"
curl -sS -i "$BASE/api/v1/escrow/status"
echo
echo "------------------------------------------"

echo "[4/9] ESCROW CREATE"
curl -sS -i -X POST "$BASE/api/v1/escrow/create" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "TEST-ESCROW-001",
    "owner_id": "TEST-OWNER-001",
    "currency": "MNT"
  }'
echo
echo "------------------------------------------"

echo "[5/9] ESCROW TRANSFER"
curl -sS -i -X POST "$BASE/api/v1/escrow/transfer" \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": "TEST-ESCROW-001",
    "to_account_id": "TEST-ESCROW-002",
    "amount": 100000
  }'
echo
echo "------------------------------------------"

echo "[6/9] EVIDENCE SUBMIT"
curl -sS -i -X POST "$BASE/api/v1/evidence/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_id": "TEST-EVIDENCE-001",
    "asset_id": "TEST-RWA-001",
    "evidence_type": "integration_test",
    "description": "Gerchain integration test evidence"
  }'
echo
echo "------------------------------------------"

echo "[7/9] VERIFY AND RELEASE"
curl -sS -i -X POST "$BASE/api/v1/evidence/verify-and-release" \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_id": "TEST-EVIDENCE-001",
    "asset_id": "TEST-RWA-001"
  }'
echo
echo "------------------------------------------"

echo "[8/9] AUDIT LOGS"
curl -sS -i "$BASE/api/v1/audit/logs"
echo
echo "------------------------------------------"

echo "[9/9] DASHBOARD"
curl -sS -i "$BASE/dashboard"
echo
echo "=========================================="
echo " TEST COMPLETE"
echo "=========================================="
