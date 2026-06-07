from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import os
import google.generativeai as genai
from sqlalchemy import text
from database import engine
from portfolio_optimizer import optimize_portfolio
import pandas as pd
from portfolio import alis_yap, satis_yap, acik_pozisyonlar, kapali_pozisyonlar
from api.auth_routes import get_current_user
from screener import get_sector

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

# Load Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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

class OptimizeRequest(BaseModel):
    tickers: List[str]
    risk_profile: str = "Medium" # Low, Medium, High

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

@router.post("/optimize")
def optimize_portfolio_endpoint(req: OptimizeRequest, current_user: str = Depends(get_current_user)):
    if len(req.tickers) < 2:
        raise HTTPException(status_code=400, detail="Optimizasyon için en az 2 hisse seçmelisiniz.")
        
    if len(req.tickers) > 20:
        raise HTTPException(status_code=400, detail="Maksimum 20 hisse seçebilirsiniz.")

    # 1. Kota Kontrolü (Sadece AI kullanılacaksa kotayı düşelim, ama optimizasyon her halükarda çalışsın)
    # Şimdilik sadece başarılı optimizasyon sonrası AI için kota kontrolü yapalım.
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE users SET ai_quota = ai_quota - 1 WHERE username=:u AND ai_quota > 0 RETURNING ai_quota"),
            {"u": current_user}
        ).fetchone()

        if result is None:
            # Kota yetersizse bile matematiksel optimizasyonu yap ama AI yorumu ekleme.
            has_quota = False
        else:
            has_quota = True

    # 2. Matematiksel Optimizasyon
    opt_res = optimize_portfolio(req.tickers, risk_profile=req.risk_profile)
    
    if "error" in opt_res:
        # Hata varsa kotayı iade et
        if has_quota:
            with engine.begin() as conn:
                conn.execute(text("UPDATE users SET ai_quota = ai_quota + 1 WHERE username=:u"), {"u": current_user})
        raise HTTPException(status_code=400, detail=opt_res["error"])

    # 3. AI Yorumu Üretimi
    ai_commentary = "Yapay zeka analiz kotanız kalmadığı için sadece matematiksel dağılım gösterilmektedir."
    
    if has_quota and GEMINI_API_KEY:
        try:
            system_prompt = (
                "Sen kıdemli bir BIST (Borsa İstanbul) Portföy Yöneticisisin. "
                "Kullanıcıya Markowitz Modern Portföy Teorisi kullanılarak hesaplanmış optimum hisse ağırlıkları verilecek. "
                "Lütfen bu dağılımı incele ve Markdown formatında kısa, profesyonel bir değerlendirme yap.\n"
                "1. Neden bu hisselere bu ağırlıklar verilmiş olabilir? (Korelasyon, getiri, volatilite mantığı)\n"
                "2. Seçilen Risk Profiline göre bu dağılımın avantajı nedir?\n"
                "Son olarak küçük puntolarla 'Yatırım tavsiyesi değildir (YTD).' uyarısını ekle."
            )
            
            user_prompt = f"Risk Profili: {req.risk_profile}\nOptimum Dağılım: {opt_res['weights']}\nBeklenen Yıllık Getiri: %{opt_res['metrics']['expected_annual_return_pct']}\nBeklenen Yıllık Volatilite: %{opt_res['metrics']['expected_annual_volatility_pct']}\nSharpe Oranı: {opt_res['metrics']['sharpe_ratio']}"
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                system_prompt + "\n\n" + user_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.7)
            )
            ai_commentary = response.text
        except Exception as e:
            ai_commentary = f"Yapay zeka analizi oluşturulurken hata oluştu. Matematiksel sonuçlar geçerlidir. Hata: {str(e)}"
            # Kotayı iade et
            with engine.begin() as conn:
                conn.execute(text("UPDATE users SET ai_quota = ai_quota + 1 WHERE username=:u"), {"u": current_user})

    return {
        "status": "success",
        "optimization": opt_res,
        "ai_commentary": ai_commentary,
        "has_quota": has_quota
    }

@router.get("/analysis")
def fetch_portfolio_analysis(current_user: str = Depends(get_current_user)):
    df = acik_pozisyonlar(current_user)
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {"data": { "sectors": [], "weighted_pe": 0, "weighted_pb": 0 }}
        
    try:
        from fundamental_analyzer import get_fundamental_data
    except ImportError:
        return {"data": { "sectors": [], "weighted_pe": 0, "weighted_pb": 0 }}
        
    total_value = df['Mevcut_Deger'].sum()
    if total_value == 0:
        return {"data": { "sectors": [], "weighted_pe": 0, "weighted_pb": 0 }}
        
    weighted_pe = 0.0
    weighted_pb = 0.0
    sector_values = {}
    
    for _, row in df.iterrows():
        ticker = row['Hisse']
        val = row['Mevcut_Deger']
        weight = val / total_value
        
        fund_data = get_fundamental_data(ticker)
        pe = fund_data.get('pe', 0)
        pb = fund_data.get('pb', 0)
        
        # Sadece pozitif F/K ve PD/DD değerlerini hesaba kat
        if isinstance(pe, (int, float)) and pe > 0:
            weighted_pe += pe * weight
        if isinstance(pb, (int, float)) and pb > 0:
            weighted_pb += pb * weight
            
        sector = get_sector(ticker)
        sector_values[sector] = sector_values.get(sector, 0) + val
        
    sectors_list = []
    for sec, val in sector_values.items():
        sectors_list.append({
            "name": sec,
            "value": round(val, 2),
            "percentage": round((val / total_value) * 100, 1)
        })
        
    # Sektörleri büyükten küçüğe sırala
    sectors_list.sort(key=lambda x: x['value'], reverse=True)
        
    return {
        "data": {
            "sectors": sectors_list,
            "weighted_pe": round(weighted_pe, 2),
            "weighted_pb": round(weighted_pb, 2)
        }
    }
