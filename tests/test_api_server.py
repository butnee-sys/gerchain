import pytest
from fastapi.testclient import TestClient
from network.api_server import app

client = TestClient(app)

def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

def test_api_transaction_lifecycle():
    tx_id = "api_tx_999"
    amount = 250.0

    # 1. Гүйлгээ үүсгэх хүсэлт илгээх
    response = client.post(f"/transaction/create?tx_id={tx_id}&amount={amount}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["tx_status"] == "PENDING"

    # 2. Гүйлгээний төлөвийг шалгах
    status_response = client.get(f"/transaction/{tx_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "PENDING"
