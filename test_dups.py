import yfinance as yf

df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
timestamps = df.index.astype('int64') // 10**9
dups = timestamps.duplicated()
if dups.any():
    print(f"Found {dups.sum()} duplicate timestamps!")
    print(timestamps[dups][:5])
else:
    print("No duplicates.")
