import yfinance as yf
import pandas as pd
import pandas_ta as ta

df = yf.download("THYAO.IS", period="3mo", interval="1h", progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]

sti = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)
print("Supertrend columns:", sti.columns if sti is not None else "None")
