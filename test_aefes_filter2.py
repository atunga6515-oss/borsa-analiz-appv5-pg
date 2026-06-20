import yfinance as yf
import pandas as pd
df = yf.download("AEFES.IS", period="3mo", interval="1h", progress=False)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]

print("Type of iloc:", type(df['Open'].iloc[0]))
