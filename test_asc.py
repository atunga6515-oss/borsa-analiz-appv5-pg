import yfinance as yf
import numpy as np
df = yf.download("AEFES.IS", period="3mo", interval="1h", progress=False)
timestamps = df.index.astype('int64') // 10**9
diffs = np.diff(timestamps)
if (diffs <= 0).any():
    print("TIMESTAMPS ARE NOT STRICTLY ASCENDING!")
    print(np.where(diffs <= 0))
else:
    print("Strictly ascending.")
