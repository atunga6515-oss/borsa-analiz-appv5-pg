import yfinance as yf
df = yf.download("AEFES.IS", period="3mo", interval="1h", progress=False)
timestamps = df.index.astype('int64') // 10**9
print("Total rows:", len(timestamps))
dups = timestamps.duplicated()
if dups.any():
    print("DUPLICATE TIMESTAMPS FOUND!")
    print(df[dups])
else:
    print("No duplicates.")
