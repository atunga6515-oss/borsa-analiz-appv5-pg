from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
import yfinance as yf
from api.auth_routes import get_current_user
import numpy as np

# Core logic imports from root directory
from data_loader import fetch_data
from indicators import get_market_regime, generate_signals_and_score
from support_resistance import calculate_best_zones
from kap_news import get_sentiment_summary
from takas_engine import get_takas_data

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

def clean_nans(obj):
    if isinstance(obj, float) and np.isnan(obj):
        return None
    elif isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(x) for x in obj]
    return obj

@router.get("/{ticker}")
def fetch_comprehensive_analysis(ticker: str, current_user: str = Depends(get_current_user)):
    try:
        # Fetch OHLCV data
        df = fetch_data(ticker, "1d", "1y")
        if df.empty:
            raise HTTPException(status_code=404, detail="Hisse verisi bulunamadı.")
            
        # Market Regime
        xu100_df = fetch_data("XU100", "1d", "1y")
        market_regime = get_market_regime(xu100_df)
        
        # Sentiment Analysis
        try:
            sent_score, news_list = get_sentiment_summary(ticker)
        except Exception as e:
            sent_score, news_list = 0.0, []
            
        # Takas (Foreign Ownership)
        try:
            takas_info = get_takas_data(ticker)
        except:
            takas_info = {}
            
        # Run SSOT Engine
        res = generate_signals_and_score(df, ticker=ticker, market_regime=market_regime, sentiment_score=sent_score)
        
        # Support/Resistance and Risk levels
        sr_data = calculate_best_zones(df)
        
        # Averages for signals terminal
        last_row = df.iloc[-1]
        
        # Some columns might not exist if data is too short
        sma_20 = float(last_row.get('SMA_20', np.nan))
        sma_50 = float(last_row.get('SMA_50', np.nan))
        sma_52 = float(last_row.get('SMA_52', np.nan))
        
        live_px = float(last_row['Close'])
        
        payload = {
            "status": "success",
            "data": {
                "ticker": ticker.upper(),
                "current_price": live_px,
                "sentiment_score": sent_score,
                "news_list": news_list,
                "takas_info": takas_info,
                "ssot_result": res,
                "support_resistance": sr_data,
                "sma": {
                    "sma_20": sma_20,
                    "sma_50": sma_50,
                    "sma_52": sma_52
                }
            }
        }
        
        # Clean NaNs before sending to JSON
        return clean_nans(payload)
        
    except Exception as e:
        import traceback
        print(f"Analysis error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
