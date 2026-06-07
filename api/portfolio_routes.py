from fastapi import APIRouter, Depends, HTTPException
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
    elif req.type == "SATIS":
        # Note: SATIS is usually done via /close but if someone hits /transaction with SATIS, we should handle it
        # satis_yap requires trade_id, so a pure transaction endpoint without trade_id might not work directly.
        # But we can try to find an open position or raise an error.
        raise HTTPException(status_code=400, detail="SATIS işlemi için /api/portfolio/close endpoint'ini kullanın veya trade_id belirtin.")
    return {"status": "success"}

@router.post("/close")
def close_position(req: CloseRequest, current_user: str = Depends(get_current_user)):
    try:
        satis_yap(current_user, req.trade_id, req.satis_fiyati)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success"}

from portfolio import pozisyon_guncelle
@router.put("/edit")
def edit_position(req: EditRequest, current_user: str = Depends(get_current_user)):
    try:
        pozisyon_guncelle(current_user, req.trade_id, req.adet, req.fiyat, req.tarih)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success"}
