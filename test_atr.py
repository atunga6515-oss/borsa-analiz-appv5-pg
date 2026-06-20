import yfinance as yf
import pandas as pd
import pandas_ta as ta

df = yf.download("THYAO.IS", period="3mo", interval="1h", progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [c[0] for c in df.columns]

atr = ta.atr(df['High'], df['Low'], df['Close'], length=22)
print("Type of ATR:", type(atr))
