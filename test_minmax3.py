import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta

def clean_nans(obj):
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    elif isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(x) for x in obj]
    return obj

def sanitize_layer_data(data_list):
    cleaned = []
    for item in data_list:
        cleaned_item = clean_nans(item)
        if all(v is not None for v in cleaned_item.values()):
            cleaned.append(cleaned_item)
    return cleaned

df = yf.download("ASTOR.IS", period="3mo", interval="1h", progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] for col in df.columns]

timestamps = df.index.astype('int64') // 10**9
candles = []
for i in range(len(df)):
    candles.append({
        "time": int(timestamps[i]),
        "open": float(df['Open'].iloc[i]),
        "high": float(df['High'].iloc[i]),
        "low": float(df['Low'].iloc[i]),
        "close": float(df['Close'].iloc[i]),
    })

auto_trend_data = []
if len(df) > 40:
    df['is_min'] = df['Low'] == df['Low'].rolling(window=20, center=True).min()
    p_indices = np.where(df['is_min'])[0].tolist()
    if len(p_indices) >= 2:
        idx1, idx2 = p_indices[-2], p_indices[-1]
        p1, p2 = float(df['Low'].iloc[idx1]), float(df['Low'].iloc[idx2])
        if (idx2 - idx1) > 0:
            r_slope = (p2 - p1) / (idx2 - idx1)
            for c_idx in range(idx1, len(df)):
                l_val = r_slope * (c_idx - idx1) + p1
                auto_trend_data.append({"time": int(timestamps[c_idx]), "value": float(l_val)})

res = clean_nans({
    "candles": candles,
    "auto": sanitize_layer_data(auto_trend_data)
})

print("Candles min:", min(c['time'] for c in res['candles']))
print("Candles max:", max(c['time'] for c in res['candles']))
if len(res['auto']) > 0:
    print("Auto min:", min(c['time'] for c in res['auto']))
    print("Auto max:", max(c['time'] for c in res['auto']))
