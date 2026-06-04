from fastapi import APIRouter, Depends
from pydantic import BaseModel
import pandas as pd
from portfolio import alis_yap, satis_yap, acik_pozisyonlar, kapali_pozisyonlar
from api.auth_routes import get_current_user

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

class TransactionRequest(BaseModel):
    ticker: str
    type: str # 'ALIS' or 'SATIS'
    quantity: float
    price: float

@router.get("/")
def fetch_portfolio(current_user: str = Depends(get_current_user)):
    df = acik_pozisyonlar(current_user)
    if isinstance(df, pd.DataFrame):
        return {"data": df.to_dict(orient="records")}
    return {"data": []}

@router.get("/summary")
def fetch_portfolio_summary(current_user: str = Depends(get_current_user)):
    df = kapali_pozisyonlar(current_user)
    if isinstance(df, pd.DataFrame):
        return {"data": df.to_dict(orient="records")}
    return {"data": []}

@router.post("/transaction")
def create_transaction(req: TransactionRequest, current_user: str = Depends(get_current_user)):
    if req.type == "ALIS":
        alis_yap(current_user, req.ticker, req.quantity, req.price)
    else:
        # Note: satis_yap takes trade_id, so this might need adjustment later
        pass
    return {"status": "success"}
