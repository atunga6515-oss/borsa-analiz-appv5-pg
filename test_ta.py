import pandas as pd
import yfinance as yf
import pandas_ta as ta

df = yf.download("THYAO.IS", period="3mo", interval="1h")
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]

sti = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)
print(sti.columns.tolist())
