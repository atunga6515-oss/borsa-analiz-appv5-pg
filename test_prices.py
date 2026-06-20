import yfinance as yf
df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
if isinstance(df.columns, type(df.index)):
    df.columns = [c[0] for c in df.columns]
print("Last Close:", df['Close'].iloc[-1])
print("Max Close:", df['Close'].max())
