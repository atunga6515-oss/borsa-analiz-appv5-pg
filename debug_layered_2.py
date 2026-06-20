import yfinance as yf
import pandas as pd
import numpy as np

ticker = "ASELS.IS"
df = yf.download(ticker, period="3mo", interval="1h", progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]

df['is_min'] = df['Low'] == df['Low'].rolling(window=20, center=True).min()

# Using np.where to get integer indices
p_indices = np.where(df['is_min'])[0]
print("Positional indices:", p_indices)

if len(p_indices) >= 2:
    idx1, idx2 = p_indices[-2], p_indices[-1]
    print(f"idx1={idx1}, idx2={idx2}")
    p1, p2 = float(df['Low'].iloc[idx1]), float(df['Low'].iloc[idx2])
    print(f"p1={p1}, p2={p2}")

