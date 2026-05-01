# app/api/routes/exchanges.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.exchange_account import ExchangeAccount
from app.core.dependencies import get_current_user
from app.schemas.exchange import ExchangeAccountCreate, ExchangeAccountResponse
from app.services.exchange.factory import create_exchange
from typing import List

router = APIRouter()


@router.post("/", response_model=ExchangeAccountResponse, status_code=201)
def add_exchange_account(
    data: ExchangeAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = ExchangeAccount(
        user_id=current_user.id,
        exchange_name=data.exchange_name,
        api_key=data.api_key,
        api_secret=data.api_secret,
        is_testnet=data.is_testnet,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/", response_model=List[ExchangeAccountResponse])
def list_exchange_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(ExchangeAccount).filter(ExchangeAccount.user_id == current_user.id).all()


@router.delete("/{account_id}")
def delete_exchange_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.id == account_id,
        ExchangeAccount.user_id == current_user.id,
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Compte non trouve")
    db.delete(account)
    db.commit()
    return {"detail": "Supprime"}


@router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    exchange = create_exchange()
    try:
        balance = await exchange.get_balance()
        return balance
    finally:
        await exchange.close()


@router.get("/ticker/{base}/{quote}")
async def get_ticker(base: str, quote: str, current_user: User = Depends(get_current_user)):
    symbol = f"{base.upper()}/{quote.upper()}"
    exchange = create_exchange()
    try:
        ticker = await exchange.get_ticker(symbol)
        return ticker
    finally:
        await exchange.close()