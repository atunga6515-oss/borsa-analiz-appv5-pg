import yfinance as yf
df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
if df.isna().any().any():
    print("Found NaNs in DF!")
    print(df[df.isna().any(axis=1)])
else:
    print("No NaNs.")
