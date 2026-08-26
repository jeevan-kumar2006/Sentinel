from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.app.schemas.transaction import TransactionDetail, PaginatedTransactions
from backend.app.services.transaction_service import transaction_service
from backend.app.services.reason_service import generate_reasons

router = APIRouter()

@router.get("/transactions", response_model=PaginatedTransactions)
async def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    risk_decision: Optional[str] = Query(None, regex="^(ALLOW|REVIEW|BLOCK)$"),
    search: Optional[str] = Query(None)
):
    result = transaction_service.get_transactions(page, limit, risk_decision, search)
    return result

@router.get("/transactions/{transaction_id}", response_model=TransactionDetail)
async def get_transaction(transaction_id: str):
    txn = transaction_service.get_transaction(transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    reasons = generate_reasons(txn)
    
    # Pydantic will validate the dict against TransactionDetail
    return {**txn, "reasons": reasons}
