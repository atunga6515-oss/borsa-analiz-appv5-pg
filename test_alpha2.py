import yfinance as yf
import pandas as pd
import pandas_ta as ta

df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]

timestamps = df.index.astype('int64') // 10**9

alpha_markers = []
ema_fast = ta.ema(df['Close'], length=9)
ema_slow = ta.ema(df['Close'], length=21)
for i in range(1, len(df)):
    if pd.isna(ema_fast.iloc[i]) or pd.isna(ema_slow.iloc[i]): continue
    if ema_fast.iloc[i-1] <= ema_slow.iloc[i-1] and ema_fast.iloc[i] > ema_slow.iloc[i]:
        alpha_markers.append({"time": int(timestamps[i]), "position": "belowBar"})
    elif ema_fast.iloc[i-1] >= ema_slow.iloc[i-1] and ema_fast.iloc[i] < ema_slow.iloc[i]:
        alpha_markers.append({"time": int(timestamps[i]), "position": "aboveBar"})

print("Alpha markers count:", len(alpha_markers))
print("First 5 times:", [m['time'] for m in alpha_markers[:5]])
