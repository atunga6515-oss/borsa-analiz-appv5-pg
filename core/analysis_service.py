import numpy as np
import pandas as pd
from data_loader import fetch_data, get_batch_live_prices
from indicators import calculate_indicators, generate_signals_and_score, get_market_regime
from kap_news import get_sentiment_summary
from support_resistance import calculate_best_zones
from takas_engine import get_takas_data

def _clean_nans(obj):
    if isinstance(obj, float) and np.isnan(obj): return None
    if isinstance(obj, dict): return {k: _clean_nans(v) for k, v in obj.items()}
    if isinstance(obj, list): return [_clean_nans(x) for x in obj]
    return obj

def _is_buy_decision(decision: str) -> bool:
    if not decision: return False
    d = decision.lower()
    if any(x in d for x in ("sat", "veto", "bekle", "doygun")): return False
    return any(k in d for k in ("al", "güçlü", "guclu", "lider", "potansiyel", "trend"))

def run_deep_analysis(ticker: str, *, period: str = "1y", market_regime: dict = None, include_sentiment: bool = True) -> dict:
    sym = ticker.upper().replace(".IS", "")
    df = fetch_data(sym, interval="1d", period=period)
    if df.empty or len(df) < 50:
        return {"status": "error", "detail": "Yetersiz veri", "ticker": sym}
        
    if market_regime is None:
        xu100_df = fetch_data("XU100", interval="1d", period=period)
        market_regime = get_market_regime(xu100_df)
        
    sent_score, news_list = 0.0, []
    if include_sentiment:
        try: sent_score, news_list = get_sentiment_summary(sym)
        except Exception: pass
        
    try: takas_info = get_takas_data(sym)
    except Exception: takas_info = {}
    
    # ÖNCE İNDİKATÖRLERİ HESAPLA (V5 Bug düzeltmesi)
    df = calculate_indicators(df.copy(), ticker=sym)
    ssot = generate_signals_and_score(df, ticker=sym, market_regime=market_regime, sentiment_score=sent_score)
    sr_data = calculate_best_zones(df)
    
    last_row = df.iloc[-1]
    live = get_batch_live_prices([sym]).get(sym, {})
    live_px = float(live.get("price") or last_row["Close"])
    
    payload = {
        "status": "success",
        "data": {
            "ticker": sym,
            "current_price": live_px,
            "sentiment_score": sent_score,
            "news_list": news_list,
            "takas_info": takas_info,
            "market_regime": market_regime,
            "ssot_result": ssot,
            "support_resistance": sr_data,
            "is_buy_signal": _is_buy_decision(ssot.get("decision", "")),
            "sma": {
                "sma_20": float(last_row["SMA_20"]) if pd.notna(last_row.get("SMA_20")) else None,
                "sma_50": float(last_row["SMA_50"]) if pd.notna(last_row.get("SMA_50")) else None,
                "sma_52": float(last_row["SMA_52", np.nan]) if pd.notna(last_row.get("SMA_52")) else None,
            }
        }
    }
    return _clean_nans(payload)
