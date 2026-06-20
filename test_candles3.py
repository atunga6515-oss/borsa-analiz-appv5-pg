import pandas as pd
import numpy as np
import yfinance as yf

def clean_nans(obj):
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    elif isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(x) for x in obj]
    return obj

df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
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

cleaned_candles = clean_nans(candles)

for c in cleaned_candles:
    if c['open'] is None or c['high'] is None or c['low'] is None or c['close'] is None:
        print("FOUND NONE IN CANDLES!", c)
        break
else:
    print("CANDLES ARE PERFECT. Length:", len(cleaned_candles))
    import json
    try:
        json.dumps(cleaned_candles)
        print("JSON Serialization SUCCESS")
    except Exception as e:
        print("JSON Serialization FAILED:", e)

