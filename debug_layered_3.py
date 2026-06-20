import sys
import traceback
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import numpy as np

def clean_nans(obj):
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    elif isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(x) for x in obj]
    return obj

def sanitize_layer_data(data_list):
    cleaned = []
    for item in data_list:
        cleaned_item = clean_nans(item)
        if all(v is not None for v in cleaned_item.values()):
            cleaned.append(cleaned_item)
    return cleaned

def fetch_layered_data(ticker):
    try:
        yf_ticker = f"{ticker}.IS" if not ticker.endswith(".IS") else ticker
        df = yf.download(yf_ticker, period="3mo", interval="1h", progress=False)
        if df.empty:
            print("EMPTY")
            return
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        timestamps = df.index.astype('int64') // 10**9
        
        candles = []
        for i in range(len(df)):
            candles.append({
                "time": int(timestamps[i]),
                "open": float(df['Open'].iloc[i]),
                "high": float(df['High'].iloc[i]),
                "low": float(df['Low'].iloc[i]),
                "close": float(df['Close'].iloc[i]),
            })

        auto_trend_data = []
        if len(df) > 40:
            df['is_min'] = df['Low'] == df['Low'].rolling(window=20, center=True).min()
            p_indices = np.where(df['is_min'])[0].tolist()
            if len(p_indices) >= 2:
                idx1, idx2 = p_indices[-2], p_indices[-1]
                p1, p2 = float(df['Low'].iloc[idx1]), float(df['Low'].iloc[idx2])
                if (idx2 - idx1) > 0:
                    r_slope = (p2 - p1) / (idx2 - idx1)
                    for c_idx in range(idx1, len(df)):
                        l_val = r_slope * (c_idx - idx1) + p1
                        auto_trend_data.append({"time": int(timestamps[c_idx]), "value": float(l_val)})

        alpha_markers = []
        ema_fast = ta.ema(df['Close'], length=9)
        ema_slow = ta.ema(df['Close'], length=21)
        for i in range(1, len(df)):
            if ema_fast.iloc[i-1] <= ema_slow.iloc[i-1] and ema_fast.iloc[i] > ema_slow.iloc[i]:
                alpha_markers.append({"time": int(timestamps[i]), "position": "belowBar", "color": "#00ffcc", "shape": "arrowUp", "text": "ALPHA AL"})
            elif ema_fast.iloc[i-1] >= ema_slow.iloc[i-1] and ema_fast.iloc[i] < ema_slow.iloc[i]:
                alpha_markers.append({"time": int(timestamps[i]), "position": "aboveBar", "color": "#ff0055", "shape": "arrowDown", "text": "ALPHA SAT"})

        squeeze_data = []
        bb = ta.bbands(df['Close'], length=20, std=2)
        kc = ta.kc(df['High'], df['Low'], df['Close'], length=20, scalar=1.5)
        sqz_val = ta.linreg(df['Close'] - ta.sma(df['Close'], length=20), length=20)
        
        if bb is not None and kc is not None:
            bbl_col = [col for col in bb.columns if 'BBL_' in col][0]
            bbu_col = [col for col in bb.columns if 'BBU_' in col][0]
            kcl_col = [col for col in kc.columns if 'KCL' in col][0]
            kcu_col = [col for col in kc.columns if 'KCU' in col][0]
            
            for i in range(len(df)):
                is_on = (bb[bbl_col].iloc[i] > kc[kcl_col].iloc[i]) and (bb[bbu_col].iloc[i] < kc[kcu_col].iloc[i])
                val = float(sqz_val.iloc[i]) if not pd.isna(sqz_val.iloc[i]) else 0.0
                squeeze_data.append({
                    "time": int(timestamps[i]), 
                    "value": val, 
                    "color": "#00e676" if val > 0 else "#ff1744",
                    "dot_color": "#ff1744" if is_on else "#00e676"
                })

        fvg_markers = []
        for i in range(2, len(df)):
            c_close = float(df['Close'].iloc[i])
            if df['Low'].iloc[i] > df['High'].iloc[i-2]:
                gap_pct = (df['Low'].iloc[i] - df['High'].iloc[i-2]) / c_close
                if gap_pct > 0.004:
                    fvg_markers.append({"time": int(timestamps[i]), "position": "belowBar", "color": "#22c55e", "shape": "arrowUp", "text": "FVG"})
            elif df['High'].iloc[i] < df['Low'].iloc[i-2]:
                gap_pct = (df['Low'].iloc[i-2] - df['High'].iloc[i]) / c_close
                if gap_pct > 0.004:
                    fvg_markers.append({"time": int(timestamps[i]), "position": "aboveBar", "color": "#ef4444", "shape": "arrowDown", "text": "FVG"})

        wavetrend_data = []
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        esa = ta.ema(tp, length=10)
        d = ta.ema(abs(tp - esa), length=10)
        wt1 = ta.ema((tp - esa) / (0.015 * d), length=21)
        wt2 = ta.sma(wt1, length=4)
        for i in range(len(df)):
            wavetrend_data.append({
                "time": int(timestamps[i]),
                "wt1": float(wt1.iloc[i]) if not pd.isna(wt1.iloc[i]) else 0.0,
                "wt2": float(wt2.iloc[i]) if not pd.isna(wt2.iloc[i]) else 0.0
            })

        supertrend_line = []
        sti = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)
        if sti is not None:
            for i in range(len(df)):
                if not pd.isna(sti['SUPERT_10_3.0'].iloc[i]):
                    supertrend_line.append({
                        "time": int(timestamps[i]),
                        "value": float(sti['SUPERT_10_3.0'].iloc[i]),
                        "color": "#26a69a" if sti['SUPERTd_10_3.0'].iloc[i] == 1 else "#ef5350"
                    })

        div_markers = []
        rsi = ta.rsi(df['Close'], length=14)
        if rsi is not None:
            for i in range(15, len(df)):
                if df['High'].iloc[i] > df['High'].iloc[i-10] and rsi.iloc[i] < rsi.iloc[i-10]:
                    div_markers.append({"time": int(timestamps[i]), "position": "aboveBar", "color": "#eab308", "shape": "circle", "text": "BEAR DIV"})
                elif df['Low'].iloc[i] < df['Low'].iloc[i-10] and rsi.iloc[i] > rsi.iloc[i-10]:
                    div_markers.append({"time": int(timestamps[i]), "position": "belowBar", "color": "#3b82f6", "shape": "circle", "text": "BULL DIV"})

        avwap_line = []
        anchor_idx = max(0, len(df) - 60)
        cum_pv = 0.0
        cum_v = 0.0
        for i in range(len(df)):
            if i >= anchor_idx:
                cum_pv += float(df['Close'].iloc[i] * df['Volume'].iloc[i])
                cum_v += float(df['Volume'].iloc[i])
                val = cum_pv / cum_v if cum_v > 0 else float(df['Close'].iloc[i])
                avwap_line.append({"time": int(timestamps[i]), "value": val})

        p_min, p_max = float(df['Low'].min()), float(df['High'].max())
        v_bins = np.linspace(p_min, p_max, 24)
        v_counts = np.zeros(len(v_bins)-1)
        for idx in range(len(df)):
            for b in range(len(v_bins)-1):
                if v_bins[b] <= df['Close'].iloc[idx] < v_bins[b+1]:
                    v_counts[b] += df['Volume'].iloc[idx]
                    break
        poc_price_level = float(v_bins[np.argmax(v_counts)])

        chandelier_line = []
        atr_22 = ta.atr(df['High'], df['Low'], df['Close'], length=22)
        for i in range(len(df)):
            c_atr = atr_22.iloc[i] if (atr_22 is not None and not pd.isna(atr_22.iloc[i])) else 0.0
            highest_high = float(df['High'].iloc[max(0, i-22):i+1].max())
            chan_val = highest_high - (3 * c_atr)
            chandelier_line.append({"time": int(timestamps[i]), "value": chan_val})

        print("SUCCESS")
    except Exception as e:
        traceback.print_exc()

for t in ["THYAO"]:
    fetch_layered_data(t)

