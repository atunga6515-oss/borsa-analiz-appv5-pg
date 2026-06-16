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
        from core.analysis_service import run_deep_analysis
        
        final_payload = run_deep_analysis(ticker)
        if final_payload.get("status") == "error":
            raise HTTPException(status_code=404, detail=final_payload.get("detail", "Veri bulunamadı"))
            
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
        
    except HTTPException as he:
        raise he
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
