from fastapi import APIRouter, Depends
from pydantic import BaseModel
import yfinance as yf
from api.auth_routes import get_current_user
import pandas as pd

router = APIRouter(prefix="/api/market", tags=["market"])

BIST_SECTORS = {
    "Bankacılık": ["AKBNK", "GARAN", "ISCTR", "YKBNK", "VAKBN", "HALKB"],
    "Havacılık": ["THYAO", "PGSUS", "TAVHL"],
    "Otomotiv": ["FROTO", "TOASO", "DOAS", "KARSN", "TTRAK"],
    "Holding": ["KCHOL", "SAHOL", "SISE", "ENKAI", "DOHOL", "TKFEN"],
    "Enerji": ["TUPRS", "ASTOR", "ENJSA", "ODAS", "GWIND", "CWENE"],
    "Perakende": ["BIMAS", "MGROS", "SOKM"],
    "Telekomünikasyon": ["TCELL", "TTKOM"],
    "Demir-Çelik": ["EREGL", "KRDMD", "KCAER"],
    "Gıda & İçecek": ["CCOLA", "AEFES", "ULKER"]
}

@router.get("/heatmap")
def fetch_heatmap(current_user: str = Depends(get_current_user)):
    """
    Treemap (Heatmap) için BIST ana hisselerinin anlık performansını ve sektörünü döner.
    """
    from data_loader import get_batch_live_prices
    
    tickers = []
    ticker_to_sector = {}
    for sector, t_list in BIST_SECTORS.items():
        for t in t_list:
            tickers.append(t)
            ticker_to_sector[t] = sector
            
    heatmap_data = []
    
    try:
        ssot_results = get_batch_live_prices(tickers)
        for t in tickers:
            info = ssot_results.get(t, {})
            if info.get("price", 0) > 0:
                heatmap_data.append({
                    "ticker": t,
                    "sector": ticker_to_sector[t],
                    "price": info.get("price", 0),
                    "change": info.get("change", 0),
                    "volume": info.get("volume", 0)
                })
    except Exception as e:
        print("Heatmap fetch error:", e)
        
    return {"data": heatmap_data}

@router.get("/calendar")
def fetch_macro_calendar(current_user: str = Depends(get_current_user)):
    """
    Önemli Makroekonomik takvim verilerini döner (TCMB, FED, Enflasyon).
    Not: Gerçek bir API bağlamadan önce statik bir veri seti ile simüle edilmektedir.
    """
    import datetime
    from dateutil.relativedelta import relativedelta

    now = datetime.datetime.now()
    
    # Her ayın son perşembesi TCMB, ayın 3'ü civarı TÜFE, ortası FED mantığıyla dinamik veri üretimi
    events = []
    
    for i in range(3):
        target_month = now + relativedelta(months=i)
        
        # O ayın 3'ü TÜFE
        tufe_date = target_month.replace(day=3)
        if tufe_date.weekday() >= 5: # Hafta sonuna geliyorsa pazartesiye al
            tufe_date += datetime.timedelta(days=(7 - tufe_date.weekday()))
            
        events.append({
            "id": i*10 + 1, 
            "date": tufe_date.strftime("%Y-%m-%d"), 
            "time": "10:00", 
            "country": "TR", 
            "event": "TÜFE (Yıllık)", 
            "importance": "High", 
            "forecast": "-", 
            "previous": "-"
        })
        
        # O ayın tahmini TCMB toplantısı (genelde ayın 20'leri)
        tcmb_date = target_month.replace(day=23)
        if tcmb_date.weekday() >= 5:
            tcmb_date -= datetime.timedelta(days=(tcmb_date.weekday() - 4))
        
        events.append({
            "id": i*10 + 2, 
            "date": tcmb_date.strftime("%Y-%m-%d"), 
            "time": "14:00", 
            "country": "TR", 
            "event": "TCMB Faiz Kararı", 
            "importance": "High", 
            "forecast": "50.00%", 
            "previous": "50.00%"
        })
        
        # 1. ve 3. aylara tahmini FED toplantısı koy
        if i % 2 == 0:
            fed_date = target_month.replace(day=18)
            if fed_date.weekday() >= 5:
                fed_date -= datetime.timedelta(days=(fed_date.weekday() - 3))
            
            events.append({
                "id": i*10 + 3, 
                "date": fed_date.strftime("%Y-%m-%d"), 
                "time": "21:00", 
                "country": "US", 
                "event": "FED Faiz Kararı", 
                "importance": "High", 
                "forecast": "5.50%", 
                "previous": "5.50%"
            })
            
    # Geçmiş tarihli olanları filtrele (sadece bugün ve sonrasını göster) ve tarihe göre sırala
    today_str = now.strftime("%Y-%m-%d")
    events = [e for e in events if e["date"] >= today_str]
    events = sorted(events, key=lambda x: x["date"])
    
    # En fazla 7 etkinlik göster
    events = events[:7]
    
    return {"data": events}

@router.get("/symbols")
def get_symbols(current_user: str = Depends(get_current_user)):
    """
    Tüm BIST hisselerinin sembollerini ve uzun adlarını döner (bist_symbols tablosundan).
    Eğer tablo boşsa screener.py'daki listeyi fallback olarak kullanır.
    """
    from database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT symbol, name FROM bist_symbols ORDER BY symbol ASC")).fetchall()
            
        if rows:
            return {"symbols": [{"symbol": r[0], "name": r[1]} for r in rows]}
            
        # Fallback (eğer henüz schedule çalışmadıysa)
        from screener import BIST_ALL_SYMBOLS
        return {"symbols": [{"symbol": sym, "name": sym} for sym in sorted(list(set(BIST_ALL_SYMBOLS)))]}
        
    except Exception as e:
        print("Error fetching symbols:", e)
        # Tablo yoksa vs fallback
        from screener import BIST_ALL_SYMBOLS
        return {"symbols": [{"symbol": sym, "name": sym} for sym in sorted(list(set(BIST_ALL_SYMBOLS)))]}
