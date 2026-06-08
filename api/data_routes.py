from fastapi import APIRouter, Depends
from data_loader import fetch_data, get_live_price
from indicators import calculate_indicators
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api/data", tags=["data"])

from api.auth_routes import get_current_user

@router.get("/ohlcv/{ticker}")
def fetch_ohlcv(ticker: str, interval: str = "1d", period: str = "1y", current_user: str = Depends(get_current_user)):
    df = fetch_data(ticker.upper(), interval, period)
    if df is not None and not df.empty:
        # Veriyi tarihe göre sırala ve tekrarları temizle (Lightweight charts fail verir)
        df = df.sort_index()
        df = df[~df.index.duplicated(keep='first')]
        
        # Indikatörleri hesapla
        df = calculate_indicators(df)
        
        # JSON parsing error önlemi (Infinity to NaN)
        import numpy as np
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        records = []
        for idx, row in df.iterrows():
            date_str = str(idx.date()) if hasattr(idx, 'date') else str(idx)[:10]
            # Lightweight Charts expects unix timestamp if timeframe < 1d
            if interval in ["1h", "4h"]:
                date_str = int(idx.timestamp()) if hasattr(idx, 'timestamp') else date_str
            
            records.append({
                "time": date_str,
                "open": float(row.get('Open', 0)),
                "high": float(row.get('High', 0)),
                "low": float(row.get('Low', 0)),
                "close": float(row.get('Close', 0)),
                "volume": float(row.get('Volume', 0)),
                "sma20": float(row.get('SMA_20', 0)) if not pd.isna(row.get('SMA_20')) else None,
                "ema50": float(row.get('EMA_50', 0)) if not pd.isna(row.get('EMA_50')) else None,
            })
        return {"data": records}

@router.get("/v1/charts/{ticker}")
def fetch_tradingview_charts(ticker: str, interval: str = "1d", period: str = "1y", current_user: str = Depends(get_current_user)):
    """TradingView Lightweight Charts için Epoch saniye cinsinden grafik verisi."""
    df = fetch_data(ticker.upper(), interval, period)
    if df is None or df.empty:
        return []
        
    df = df.sort_index()
    df = df[~df.index.duplicated(keep='first')]
    
    # NaN and Inf handling
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)
    
    records = []
    for idx, row in df.iterrows():
        # Epoch (Unix timestamp in seconds)
        if isinstance(idx, pd.Timestamp):
            unix_time = int(idx.timestamp())
        else:
            unix_time = int(pd.to_datetime(idx).timestamp())
            
        records.append({
            "time": unix_time,
            "open": float(row.get('Open', 0)),
            "high": float(row.get('High', 0)),
            "low": float(row.get('Low', 0)),
            "close": float(row.get('Close', 0)),
            "volume": float(row.get('Volume', 0))
        })
    return records

@router.get("/price/{ticker}")
def fetch_live_price(ticker: str, current_user: str = Depends(get_current_user)):
    price = get_live_price(ticker.upper())
    return {"price": price}

from pydantic import BaseModel
class BatchPriceRequest(BaseModel):
    tickers: list[str]

@router.post("/prices/batch")
def fetch_batch_prices(req: BatchPriceRequest, current_user: str = Depends(get_current_user)):
    from data_loader import get_batch_live_prices
    
    results = {}
    if not req.tickers:
        return {"data": results}
        
    try:
        ssot_results = get_batch_live_prices(req.tickers)
        for ticker in req.tickers:
            results[ticker] = {
                "price": ssot_results.get(ticker, {}).get("price", 0.0),
                "change": ssot_results.get(ticker, {}).get("change", 0.0)
            }
    except Exception as e:
        print("Batch price error:", e)
        
    return {"data": results}
