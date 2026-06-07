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
    tickers = []
    ticker_to_sector = {}
    for sector, t_list in BIST_SECTORS.items():
        for t in t_list:
            tickers.append(t)
            ticker_to_sector[t] = sector
            
    tickers_str = " ".join([f"{t}.IS" for t in tickers])
    
    heatmap_data = []
    
    try:
        # Fetch 2 days of data to calculate percentage change
        data = yf.download(tickers_str, period="2d", progress=False)
        
        if data.empty:
            return {"data": heatmap_data}
            
        close_df = data['Close'] if 'Close' in data.columns else data
        volume_df = data['Volume'] if 'Volume' in data.columns else None
        
        for t in tickers:
            t_is = f"{t}.IS"
            if t_is in close_df.columns:
                series = close_df[t_is].dropna()
                vol_series = volume_df[t_is].dropna() if volume_df is not None and t_is in volume_df.columns else None
                
                if len(series) >= 2:
                    curr_price = float(series.iloc[-1])
                    prev_price = float(series.iloc[-2])
                    vol = float(vol_series.iloc[-1]) if vol_series is not None and len(vol_series) > 0 else 0
                    
                    if prev_price > 0:
                        change = ((curr_price - prev_price) / prev_price) * 100
                        heatmap_data.append({
                            "ticker": t,
                            "sector": ticker_to_sector[t],
                            "price": round(curr_price, 2),
                            "change": round(change, 2),
                            "volume": vol
                        })
    except Exception as e:
        print("Heatmap fetch error:", e)
        
    return {"data": heatmap_data}
