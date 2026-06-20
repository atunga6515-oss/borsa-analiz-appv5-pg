from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
import yfinance as yf
from api.auth_routes import get_current_user
import numpy as np
import pandas_ta as ta

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

@router.get("/layered-data")
def get_layered_data(ticker: str, current_user: str = Depends(get_current_user)):
    try:
        yf_ticker = f"{ticker}.IS" if not ticker.endswith(".IS") else ticker
        df = yf.download(yf_ticker, period="6mo", interval="1d")
        if df.empty:
            raise HTTPException(status_code=404, detail="Hisse verisi bulunamadı.")
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        timestamps = [int(x.timestamp()) for x in df.index]
        
        # 1. Base Candles Array
        candles = [{"time": int(timestamps[i]), "open": float(df['Open'].iloc[i]), "high": float(df['High'].iloc[i]), "low": float(df['Low'].iloc[i]), "close": float(df['Close'].iloc[i])} for i in range(len(df))]

        # Auto Trend (Macro Support Interpolation)
        auto_trend_data = []
        if len(df) > 40:
            half = len(df) // 2
            # İlk yarının en dip noktası
            first_half = df['Low'].iloc[:half]
            idx1_pos = first_half.argmin()
            # İkinci yarının en dip noktası
            second_half = df['Low'].iloc[half:]
            idx2_pos = half + second_half.argmin()
            
            p1, p2 = float(df['Low'].iloc[idx1_pos]), float(df['Low'].iloc[idx2_pos])
            if (idx2_pos - idx1_pos) > 0:
                r_slope = (p2 - p1) / (idx2_pos - idx1_pos)
                for c_idx in range(idx1_pos, len(df)):
                    l_val = r_slope * (c_idx - idx1_pos) + p1
                    auto_trend_data.append({"time": int(timestamps[c_idx]), "value": float(l_val)})
                    # Breakout termination check
                    if c_idx > idx2_pos and float(df['Close'].iloc[c_idx]) < l_val:
                        break


        # SuperTrend
        supertrend_line = []
        sti = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)
        if sti is not None:
            for i in range(len(df)):
                if not pd.isna(sti['SUPERT_10_3'].iloc[i]):
                    supertrend_line.append({"time": int(timestamps[i]), "value": float(sti['SUPERT_10_3'].iloc[i]), "color": "#26a69a" if sti['SUPERTd_10_3'].iloc[i] == 1 else "#ef5350"})

        # Alpha Signal Engine
        alpha_markers = []
        ema9, ema21 = ta.ema(df['Close'], length=9), ta.ema(df['Close'], length=21)
        last_alpha_al = -10
        last_alpha_sat = -10
        for i in range(1, len(df)):
            if ema9.iloc[i-1] <= ema21.iloc[i-1] and ema9.iloc[i] > ema21.iloc[i]:
                if i - last_alpha_al > 5:
                    alpha_markers.append({"time": int(timestamps[i]), "position": "belowBar", "color": "#00ffcc", "shape": "arrowUp", "text": "ALPHA AL"})
                    last_alpha_al = i
            elif ema9.iloc[i-1] >= ema21.iloc[i-1] and ema9.iloc[i] < ema21.iloc[i]:
                if i - last_alpha_sat > 5:
                    alpha_markers.append({"time": int(timestamps[i]), "position": "aboveBar", "color": "#ff0055", "shape": "arrowDown", "text": "ALPHA SAT"})
                    last_alpha_sat = i

        # SMC FVG (0.5% Volatility Noise Filter Fix)
        fvg_markers = []
        for i in range(2, len(df)):
            c_close = float(df['Close'].iloc[i])
            if df['Low'].iloc[i] > df['High'].iloc[i-2] and ((df['Low'].iloc[i] - df['High'].iloc[i-2]) / c_close) > 0.005:
                fvg_markers.append({"time": int(timestamps[i]), "position": "belowBar", "color": "#22c55e", "shape": "circle", "text": "+FVG"})
            elif df['High'].iloc[i] < df['Low'].iloc[i-2] and ((df['Low'].iloc[i-2] - df['High'].iloc[i]) / c_close) > 0.005:
                fvg_markers.append({"time": int(timestamps[i]), "position": "aboveBar", "color": "#ef4444", "shape": "circle", "text": "-FVG"})

        # Squeeze Momentum
        squeeze_data = []
        bb = ta.bbands(df['Close'], length=20, std=2)
        kc = ta.kc(df['High'], df['Low'], df['Close'], length=20, scalar=1.5)
        sqz_val = ta.linreg(df['Close'] - ta.sma(df['Close'], length=20), length=20)
        
        bb_lower_col = bb.columns[0] if bb is not None else None
        bb_upper_col = bb.columns[2] if bb is not None else None
        kc_lower_col = kc.columns[0] if kc is not None else None
        kc_upper_col = kc.columns[2] if kc is not None else None
        
        for i in range(len(df)):
            is_on = False
            if bb is not None and kc is not None:
                is_on = (bb[bb_lower_col].iloc[i] > kc[kc_lower_col].iloc[i]) and (bb[bb_upper_col].iloc[i] < kc[kc_upper_col].iloc[i])
            val = float(sqz_val.iloc[i]) if sqz_val is not None and not pd.isna(sqz_val.iloc[i]) else None
            squeeze_data.append({"time": int(timestamps[i]), "value": val, "color": "#00e676" if (val and val > 0) else "#ff1744", "dot_color": "#ff1744" if is_on else "#00e676"})

        # WaveTrend Oscillator
        wavetrend_data = []
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        wt1 = ta.ema((tp - ta.ema(tp, length=10)) / (0.015 * ta.ema(abs(tp - ta.ema(tp, length=10)), length=10)), length=21)
        wt2 = ta.sma(wt1, length=4)
        for i in range(len(df)):
            wavetrend_data.append({"time": int(timestamps[i]), "wt1": float(wt1.iloc[i]) if not pd.isna(wt1.iloc[i]) else None, "wt2": float(wt2.iloc[i]) if not pd.isna(wt2.iloc[i]) else None})

        # Divergence Indicator (Pivot-Based)
        div_markers = []
        rsi = ta.rsi(df['Close'], length=14)
        last_bear_div = -10
        last_bull_div = -10
        if rsi is not None:
            for i in range(15, len(df)-2):
                # Bearish Divergence (Tepe uyumsuzluğu)
                if df['High'].iloc[i] == df['High'].iloc[i-5:i+3].max():
                    for j in range(i-30, i-5):
                        if j > 0 and df['High'].iloc[j] == df['High'].iloc[j-5:j+3].max():
                            if df['High'].iloc[i] > df['High'].iloc[j] and rsi.iloc[i] < rsi.iloc[j]:
                                if i - last_bear_div > 5:
                                    div_markers.append({"time": int(timestamps[i]), "position": "aboveBar", "color": "#eab308", "shape": "square", "text": "BEAR DIV"})
                                    last_bear_div = i
                            break

                # Bullish Divergence (Dip uyumsuzluğu)
                if df['Low'].iloc[i] == df['Low'].iloc[i-5:i+3].min():
                    for j in range(i-30, i-5):
                        if j > 0 and df['Low'].iloc[j] == df['Low'].iloc[j-5:j+3].min():
                            if df['Low'].iloc[i] < df['Low'].iloc[j] and rsi.iloc[i] > rsi.iloc[j]:
                                if i - last_bull_div > 5:
                                    div_markers.append({"time": int(timestamps[i]), "position": "belowBar", "color": "#3b82f6", "shape": "square", "text": "BULL DIV"})
                                    last_bull_div = i
                            break

        # Anchored VWAP (Highest Volume Node)
        avwap_line = []
        if len(df) > 0:
            anchor_pos = df.index.get_loc(df['Volume'].idxmax())
            cum_pv, cum_v = 0.0, 0.0
            for i in range(len(df)):
                if i >= anchor_pos:
                    cum_pv += float(df['Close'].iloc[i] * df['Volume'].iloc[i])
                    cum_v += float(df['Volume'].iloc[i])
                    avwap_line.append({"time": int(timestamps[i]), "value": cum_pv / cum_v if cum_v > 0 else float(df['Close'].iloc[i])})
                else:
                    avwap_line.append({"time": int(timestamps[i]), "value": None})

        # Volume Profile POC
        p_min, p_max = float(df['Low'].min()), float(df['High'].max())
        v_bins = np.linspace(p_min, p_max, 24)
        v_counts = np.zeros(len(v_bins)-1)
        for idx in range(len(df)):
            for b in range(len(v_bins)-1):
                if v_bins[b] <= df['Close'].iloc[idx] < v_bins[b+1]:
                    v_counts[b] += df['Volume'].iloc[idx]
                    break
        poc_price_level = float(v_bins[np.argmax(v_counts)])

        # Chandelier Exit
        chandelier_line = []
        atr_22 = ta.atr(df['High'], df['Low'], df['Close'], length=22)
        for i in range(len(df)):
            c_atr = atr_22.iloc[i] if (atr_22 is not None and not pd.isna(atr_22.iloc[i])) else 0.0
            chandelier_line.append({"time": int(timestamps[i]), "value": float(df['High'].iloc[max(0, i-22):i+1].max() - (3 * c_atr))})

        # ADX & DMI
        adx_dmi_list = []
        ta_adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        for i in range(len(df)):
            adx_dmi_list.append({
                "time": int(timestamps[i]),
                "adx": float(ta_adx['ADX_14'].iloc[i]) if ta_adx is not None and not pd.isna(ta_adx['ADX_14'].iloc[i]) else None,
                "plus_di": float(ta_adx['DMP_14'].iloc[i]) if ta_adx is not None and not pd.isna(ta_adx['DMP_14'].iloc[i]) else None,
                "minus_di": float(ta_adx['DMN_14'].iloc[i]) if ta_adx is not None and not pd.isna(ta_adx['DMN_14'].iloc[i]) else None
            })

        # Stochastic RSI
        stoch_rsi_list = []
        ta_stochrsi = ta.stochrsi(df['Close'], length=14, rsi_length=14, k=3, d=3)
        for i in range(len(df)):
            stoch_rsi_list.append({
                "time": int(timestamps[i]),
                "k": float(ta_stochrsi['STOCHRSIk_14_14_3_3'].iloc[i]) if ta_stochrsi is not None and not pd.isna(ta_stochrsi['STOCHRSIk_14_14_3_3'].iloc[i]) else None,
                "d": float(ta_stochrsi['STOCHRSId_14_14_3_3'].iloc[i]) if ta_stochrsi is not None and not pd.isna(ta_stochrsi['STOCHRSId_14_14_3_3'].iloc[i]) else None
            })

        # Chaikin Money Flow (CMF)
        cmf_list = []
        ta_cmf = ta.cmf(df['High'], df['Low'], df['Close'], df['Volume'], length=20)
        if ta_cmf is not None:
            for i in range(len(df)):
                val = float(ta_cmf.iloc[i]) if not pd.isna(ta_cmf.iloc[i]) else None
                cmf_list.append({"time": int(timestamps[i]), "value": val, "color": "rgba(34,197,94,0.5)" if (val and val >= 0) else "rgba(239,68,68,0.5)"})

        # Donchian Channels
        donchian_list = [{"time": int(timestamps[i]), "upper": float(df['High'].iloc[max(0, i-20):i+1].max()), "lower": float(df['Low'].iloc[max(0, i-20):i+1].min())} for i in range(len(df))]

        # Ichimoku Kumo
        ichimoku_list = []
        span_a = ((df['High'].rolling(9).max() + df['Low'].rolling(9).min() + df['High'].rolling(26).max() + df['Low'].rolling(26).min()) / 4).shift(26)
        span_b = ((df['High'].rolling(52).max() + df['Low'].rolling(52).min()) / 2).shift(26)
        for i in range(len(df)):
            ichimoku_list.append({"time": int(timestamps[i]), "span_a": float(span_a.iloc[i]) if not pd.isna(span_a.iloc[i]) else None, "span_b": float(span_b.iloc[i]) if not pd.isna(span_b.iloc[i]) else None})

        # Bollinger Bands
        bb_list = []
        for i in range(len(df)):
            bb_list.append({"time": int(timestamps[i]), "upper": float(bb[bb_upper_col].iloc[i]) if bb is not None and not pd.isna(bb[bb_upper_col].iloc[i]) else None, "lower": float(bb[bb_lower_col].iloc[i]) if bb is not None and not pd.isna(bb[bb_lower_col].iloc[i]) else None})

        # Fetch current quote for frontend display
        try:
            fast_info = yf.Ticker(yf_ticker).fast_info
            last_price = float(fast_info.last_price)
            prev_close = float(fast_info.previous_close)
            change_pct = ((last_price - prev_close) / prev_close) * 100 if prev_close else 0.0
            quote_data = {"price": last_price, "change_pct": change_pct}
        except Exception:
            quote_data = {"price": float(df['Close'].iloc[-1]), "change_pct": 0.0}

        return {
            "status": "success", "ticker": ticker, "candles": candles, "poc_price": poc_price_level,
            "quote": quote_data,
            "layers": {
                "auto_trend": auto_trend_data, "supertrend": supertrend_line, "alpha_signal": alpha_markers, "smc_fvg": fvg_markers,
                "squeeze": squeeze_data, "wavetrend": wavetrend_data, "divergence": div_markers, "anchored_vwap": avwap_line,
                "chandelier": chandelier_line, "adx_dmi": adx_dmi_list, "stoch_rsi": stoch_rsi_list, "cmf": cmf_list,
                "donchian": donchian_list, "ichimoku": ichimoku_list, "bollinger": bb_list
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        print(f"Deep analysis error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Analiz sırasında hata oluştu")

@router.get("/{ticker}/chart")
def fetch_chart_data(ticker: str, period: str = "1y", current_user: str = Depends(get_current_user)):
    try:
        from data_loader import fetch_data
        from indicators import calculate_indicators
        
        sym = ticker.upper().replace(".IS", "")
        # Get historical data
        df = fetch_data(sym, interval="1d", period=period)
        if df.empty:
            raise HTTPException(status_code=404, detail="Veri bulunamadı")
            
        # Ensure chronological order and remove exact duplicate dates to prevent Lightweight Charts crash
        df = df.sort_index()
        df = df[~df.index.duplicated(keep='last')]
        
        # Calculate indicators
        df = calculate_indicators(df, ticker=sym)
        
        # Convert index to string for JSON
        df['time'] = df.index.strftime('%Y-%m-%d')
        
        # Select required columns
        cols_to_export = ['time', 'Open', 'High', 'Low', 'Close', 'Volume']
        
        # Add common indicators
        optional_indicators = ['RSI_14', 'MACD', 'MACDs', 'MACDh', 'SMA_20', 'SMA_50', 'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 'ATR_14', 'MFI_14']
        for col in optional_indicators:
            if col in df.columns:
                cols_to_export.append(col)
                
        # Export only existing columns
        export_df = df[[c for c in cols_to_export if c in df.columns]].copy()
        
        # Replace NaN with None (JSON null) for valid frontend parsing
        export_df = export_df.replace([np.inf, -np.inf, np.nan], None)
        
        chart_data = export_df.to_dict(orient="records")
        return {"status": "success", "data": chart_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
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
