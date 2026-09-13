// SHUUD frontend API adapter.
// The SHUUD UI stays product-facing; the underlying infrastructure is intentionally hidden.
// Set window.SHUUD_API_BASE before loading this module when the backend is not same-origin.
const SHUUD_API_BASE = window.SHUUD_API_BASE || '/api/v1';

async function shuudApi(path, options = {}) {
  const response = await fetch(`${SHUUD_API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `SHUUD API ${response.status}`);
  return body;
}

export async function createPaymentEscrow({ escrowId, sender, receiver, amount, condition }) {
  return shuudApi('/escrows/create', {
    method: 'POST',
    body: JSON.stringify({
      escrow_id: escrowId,
      sender_address: sender,
      receiver_address: receiver,
      amount,
      condition_desc: condition,
    }),
  });
}

export async function getPaymentEscrow(escrowId) {
  return shuudApi(`/escrows/${encodeURIComponent(escrowId)}`);
}

export async function lockPaymentEscrow(escrowId, actor = 'SHUUD') {
  return shuudApi(`/escrows/${encodeURIComponent(escrowId)}/action`, {
    method: 'POST',
    body: JSON.stringify({ action: 'LOCK', actor }),
  });
}

export async function releasePaymentEscrow(escrowId, actor = 'SHUUD_CLEARANCE') {
  return shuudApi(`/escrows/${encodeURIComponent(escrowId)}/action`, {
    method: 'POST',
    body: JSON.stringify({ action: 'RELEASE', actor }),
  });
}
