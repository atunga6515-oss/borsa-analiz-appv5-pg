import yfinance as yf
df = yf.download("AEFES.IS", period="1d", progress=False)
print("AEFES last close:", df['Close'].iloc[-1] if len(df) else "No data")
