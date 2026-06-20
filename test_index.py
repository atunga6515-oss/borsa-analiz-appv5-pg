import yfinance as yf
import pandas as pd
df = yf.download("THYAO.IS", period="3mo", interval="1h")
# approach 1
t1 = [int(x.timestamp()) for x in df.index]
print("T1", t1[:5])

# approach 2
t2 = (df.index.astype('int64') // 10**9).tolist()
print("T2", t2[:5])

# approach 3
t3 = df.index.astype(int).tolist()
print("T3", t3[:5])
