import yfinance as yf
df = yf.download("AEFES.IS", period="3mo", interval="1h", progress=False)
timestamps = [int(ts.timestamp()) for ts in df.index]
print(timestamps[:5])
