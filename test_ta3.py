import pandas as pd
import yfinance as yf
import pandas_ta as ta

df = yf.download("THYAO.IS", period="3mo", interval="1h")
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]

bb = ta.bbands(df['Close'], length=20, std=2)
print("Bollinger:", bb.columns.tolist())

kc = ta.kc(df['High'], df['Low'], df['Close'], length=20, scalar=1.5)
print("Keltner:", kc.columns.tolist())
