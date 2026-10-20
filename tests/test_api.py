import pytest
from fastapi.testclient import TestClient
from app.main import app, accounts, transactions

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_data():
    accounts.clear()
    transactions.clear()
    yield
    accounts.clear()
    transactions.clear()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_account():
    response = client.post("/accounts", json={
        "account_id": 1001,
        "owner": "Customer One",
        "balance": 5000
    })

    assert response.status_code == 201
    assert response.json()["account_id"] == 1001


def test_duplicate_account():
    account = {
        "account_id": 1001,
        "owner": "Customer One",
        "balance": 5000
    }

    client.post("/accounts", json=account)
    response = client.post("/accounts", json=account)

    assert response.status_code == 409


def test_money_transfer():
    client.post("/accounts", json={
        "account_id": 1001,
        "owner": "Customer One",
        "balance": 5000
    })

    client.post("/accounts", json={
        "account_id": 1002,
        "owner": "Customer Two",
        "balance": 2500
    })

    response = client.post("/transfer", json={
        "from_account": 1001,
        "to_account": 1002,
        "amount": "500.00"
    })

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    sender = client.get("/accounts/1001").json()
    receiver = client.get("/accounts/1002").json()

    assert sender["balance"] == 4500
    assert receiver["balance"] == 3000


def test_insufficient_funds():
    client.post("/accounts", json={
        "account_id": 1001,
        "owner": "Customer One",
        "balance": 100
    })

    client.post("/accounts", json={
        "account_id": 1002,
        "owner": "Customer Two",
        "balance": 250
    })

    response = client.post("/transfer", json={
        "from_account": 1001,
        "to_account": 1002,
        "amount": "500.00"
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"


def test_transaction_history():
    response = client.get("/transactions")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
