import yfinance as yf
import pandas as pd
df = yf.download("AEFES.IS", period="3mo", interval="1h", progress=False)

candles = []
for i in range(len(df)):
    o = float(df['Open'].iloc[i])
    h = float(df['High'].iloc[i])
    l = float(df['Low'].iloc[i])
    c = float(df['Close'].iloc[i])
    if pd.isna(o) or pd.isna(h) or pd.isna(l) or pd.isna(c):
        continue
    candles.append(c)

print("Original length:", len(df))
print("Filtered length:", len(candles))
