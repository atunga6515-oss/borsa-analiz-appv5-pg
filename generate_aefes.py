import sys
sys.path.append(".")
import yfinance as yf
import pandas as pd
import numpy as np
import json

df = yf.download("AEFES.IS", period="3mo", interval="1h", progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]

timestamps = df.index.astype('int64') // 10**9
candles = []
for i in range(len(df)):
    o = float(df['Open'].iloc[i])
    h = float(df['High'].iloc[i])
    l = float(df['Low'].iloc[i])
    c = float(df['Close'].iloc[i])
    if pd.isna(o) or pd.isna(h) or pd.isna(l) or pd.isna(c):
        continue
    candles.append({
        "time": int(timestamps[i]),
        "open": o,
        "high": h,
        "low": l,
        "close": c,
    })

with open("test_candles.json", "w") as f:
    json.dump(candles, f)
print("Saved to test_candles.json")
