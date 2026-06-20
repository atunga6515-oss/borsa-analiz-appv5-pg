import yfinance as yf
df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
timestamps = df.index.astype('int64') // 10**9
print(timestamps[:5].tolist())
