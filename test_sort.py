import yfinance as yf
df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
timestamps = df.index.astype('int64') // 10**9
is_sorted = (timestamps[1:] > timestamps[:-1]).all()
print("Strictly ascending:", is_sorted)
if not is_sorted:
    import numpy as np
    diffs = timestamps[1:] - timestamps[:-1]
    bad_idx = np.where(diffs <= 0)[0]
    print("Bad indices:", bad_idx)
    for idx in bad_idx:
        print(f"Index {idx}: {timestamps[idx]} -> {timestamps[idx+1]}")
