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

from database import engine
from sqlalchemy import text
from datetime import datetime
import pytz
import json

TR_TZ = pytz.timezone("Europe/Istanbul")

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
        
        # Live price using SSOT
        from data_loader import get_batch_live_prices
        ssot = get_batch_live_prices([ticker])
        live_px = ssot.get(ticker, {}).get("price", 0.0)
        if live_px == 0.0:
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
        final_payload = clean_nans(payload)
        
        # Kaydet
        run_date = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M:%S")
        res_json = json.dumps(final_payload)
        
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO analysis_history (username, ticker, run_date, results_json)
                VALUES (:u, :t, :d, :r)
            """), {"u": current_user, "t": ticker.upper(), "d": run_date, "r": res_json})
            
            conn.execute(text("""
                DELETE FROM analysis_history 
                WHERE username = :u AND id NOT IN (
                    SELECT id FROM analysis_history 
                    WHERE username = :u 
                    ORDER BY id DESC LIMIT 30
                )
            """), {"u": current_user})
            
        return final_payload
        
    except Exception as e:
        import traceback
        print(f"Analysis error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Analiz sırasında beklenmeyen bir hata oluştu.")

@router.get("/history/list")
def fetch_analysis_history(current_user: str = Depends(get_current_user)):
    with engine.connect() as conn:
        df = pd.read_sql_query(
            text("SELECT id, ticker, run_date FROM analysis_history WHERE username=:u ORDER BY id DESC"),
            conn, params={"u": current_user}
        )
    return {"data": df.to_dict(orient="records")}

@router.get("/history/{history_id}")
def fetch_analysis_history_detail(history_id: int, current_user: str = Depends(get_current_user)):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT results_json FROM analysis_history WHERE id=:id AND username=:u"),
            {"id": history_id, "u": current_user}
        ).fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
        
    try:
        data = json.loads(result[0])
        return data
    except:
        raise HTTPException(status_code=500, detail="Veri çözümlenemedi.")
