import yfinance as yf
df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
print("Dtype:", df.index.dtype)
print("Raw int64:", df.index.astype('int64')[:5].tolist())
print("Div 10**9:", (df.index.astype('int64') // 10**9)[:5].tolist())
