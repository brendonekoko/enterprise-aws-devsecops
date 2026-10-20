from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Enterprise Financial Transaction API",
    version="1.0.0"
)

# Temporary in-memory database for local development
accounts = {}


class Account(BaseModel):
    account_id: int
    owner: str
    balance: float = Field(ge=0)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/accounts", status_code=201)
def create_account(account: Account):
    if account.account_id in accounts:
        raise HTTPException(
            status_code=409,
            detail="Account already exists"
        )

    accounts[account.account_id] = account.model_dump()
    return accounts[account.account_id]


@app.get("/accounts/{account_id}")
def get_account(account_id: int):
    if account_id not in accounts:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    return accounts[account_id]
from decimal import Decimal, InvalidOperation
from threading import Lock

transactions = []
transfer_lock = Lock()


class Transfer(BaseModel):
    from_account: int
    to_account: int
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


@app.post("/transfer")
def transfer_money(transfer: Transfer):
    with transfer_lock:
        if transfer.from_account == transfer.to_account:
            raise HTTPException(
                status_code=400,
                detail="Cannot transfer to the same account"
            )

        if transfer.from_account not in accounts:
            raise HTTPException(
                status_code=404,
                detail="Sender account not found"
            )

        if transfer.to_account not in accounts:
            raise HTTPException(
                status_code=404,
                detail="Receiver account not found"
            )

        sender = accounts[transfer.from_account]
        receiver = accounts[transfer.to_account]

        amount = transfer.amount
        sender_balance = Decimal(str(sender["balance"]))
        receiver_balance = Decimal(str(receiver["balance"]))

        if sender_balance < amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient funds"
            )

        sender["balance"] = float(sender_balance - amount)
        receiver["balance"] = float(receiver_balance + amount)

        transaction = {
            "transaction_id": len(transactions) + 1,
            "from_account": transfer.from_account,
            "to_account": transfer.to_account,
            "amount": str(amount),
            "status": "completed"
        }

        transactions.append(transaction)
        return transaction


@app.get("/transactions")
def get_transactions():
    return transactions
