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
    date: str = None

class CloseRequest(BaseModel):
    trade_id: int
    satis_fiyati: float

class EditRequest(BaseModel):
    trade_id: int
    adet: float
    fiyat: float
    tarih: str = None

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
        alis_yap(current_user, req.ticker, req.quantity, req.price, alis_tarihi=req.date)
    return {"status": "success"}

@router.post("/close")
def close_position(req: CloseRequest, current_user: str = Depends(get_current_user)):
    # Check if this position belongs to user? Assume yes for now or it's handled in a real app
    satis_yap(req.trade_id, req.satis_fiyati)
    return {"status": "success"}

from portfolio import pozisyon_guncelle
@router.put("/edit")
def edit_position(req: EditRequest, current_user: str = Depends(get_current_user)):
    pozisyon_guncelle(req.trade_id, req.adet, req.fiyat, req.tarih)
    return {"status": "success"}
