import pandas as pd
import yfinance as yf
import pandas_ta as ta

df = yf.download("THYAO.IS", period="3mo", interval="1h")
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]

ta_adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
print("ADX:", ta_adx.columns.tolist())

ta_stochrsi = ta.stochrsi(df['Close'], length=14, rsi_length=14, k=3, d=3)
print("StochRSI:", ta_stochrsi.columns.tolist())

