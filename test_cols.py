import yfinance as yf
df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
print("Before flatten:", df.columns)
if isinstance(df.columns, type(df.index)):
    pass
# Actually checking multiindex
import pandas as pd
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]
print("After flatten:", df.columns)
print("Type of df['Close']:", type(df['Close']))
