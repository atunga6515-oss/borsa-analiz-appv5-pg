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
    import yfinance as yf
    
    results = {}
    if not req.tickers:
        return {"data": results}
        
    tickers_str = " ".join([f"{t.upper()}.IS" for t in req.tickers])
    try:
        # Do not use group_by="ticker" as it causes multi-index hell in newer yf versions
        data = yf.download(tickers_str, period="5d", progress=False)
        
        if data.empty:
            return {"data": results}
            
        # Try to get the Close prices. If 'Close' is not in columns, it might be a Series (single ticker)
        if 'Close' in data.columns.levels[0] if isinstance(data.columns, pd.MultiIndex) else 'Close' in data.columns:
            close_data = data['Close']
        else:
            close_data = data # Fallback
            
        for ticker in req.tickers:
            results[ticker] = {"price": 0, "change": 0}
            t_is = f"{ticker.upper()}.IS"
            
            try:
                series = None
                if isinstance(close_data, pd.DataFrame):
                    if t_is in close_data.columns:
                        series = close_data[t_is].dropna()
                elif isinstance(close_data, pd.Series):
                    series = close_data.dropna()
                    
                if series is not None and len(series) >= 2:
                    current_price = float(series.iloc[-1])
                    prev_price = float(series.iloc[-2])
                    
                    if prev_price > 0:
                        pct_change = ((current_price - prev_price) / prev_price) * 100
                        results[ticker] = {
                            "price": round(current_price, 2),
                            "change": round(pct_change, 2)
                        }
            except Exception as inner_e:
                print(f"Error parsing {ticker}: {inner_e}")
                
    except Exception as e:
        print("Batch price error:", e)
        
    return {"data": results}
