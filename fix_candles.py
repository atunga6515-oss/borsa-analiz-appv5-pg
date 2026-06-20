with open("api/analysis_routes.py", "r") as f:
    content = f.read()

old_candles = """        candles = []
        for i in range(len(df)):
            candles.append({
                "time": int(timestamps[i]),
                "open": float(df['Open'].iloc[i]),
                "high": float(df['High'].iloc[i]),
                "low": float(df['Low'].iloc[i]),
                "close": float(df['Close'].iloc[i]),
            })"""

new_candles = """        candles = []
        for i in range(len(df)):
            o = float(df['Open'].iloc[i])
            h = float(df['High'].iloc[i])
            l = float(df['Low'].iloc[i])
            c = float(df['Close'].iloc[i])
            # Filter out NaNs to prevent lightweight-charts null crash
            if pd.isna(o) or pd.isna(h) or pd.isna(l) or pd.isna(c):
                continue
            candles.append({
                "time": int(timestamps[i]),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
            })"""
content = content.replace(old_candles, new_candles)

old_return = """        return clean_nans({
            "status": "success",
            "ticker": ticker,
            "candles": candles,
            "poc_price": poc_price_level,
            "layers": {
                "auto_trend": sanitize_layer_data(auto_trend_data),
                "alpha_signal": sanitize_layer_data(alpha_markers),
                "squeeze": sanitize_layer_data(squeeze_data),
                "smc_fvg": sanitize_layer_data(fvg_markers),
                "wavetrend": sanitize_layer_data(wavetrend_data),
                "supertrend": sanitize_layer_data(supertrend_line),
                "divergence": sanitize_layer_data(div_markers),
                "anchored_vwap": sanitize_layer_data(avwap_line),
                "chandelier": sanitize_layer_data(chandelier_line)
            }
        })"""

new_return = """        return {
            "status": "success",
            "ticker": ticker,
            "candles": candles,
            "poc_price": float(poc_price_level) if not pd.isna(poc_price_level) else 0.0,
            "layers": {
                "auto_trend": sanitize_layer_data(auto_trend_data),
                "alpha_signal": sanitize_layer_data(alpha_markers),
                "squeeze": sanitize_layer_data(squeeze_data),
                "smc_fvg": sanitize_layer_data(fvg_markers),
                "wavetrend": sanitize_layer_data(wavetrend_data),
                "supertrend": sanitize_layer_data(supertrend_line),
                "divergence": sanitize_layer_data(div_markers),
                "anchored_vwap": sanitize_layer_data(avwap_line),
                "chandelier": sanitize_layer_data(chandelier_line)
            }
        }"""
content = content.replace(old_return, new_return)

with open("api/analysis_routes.py", "w") as f:
    f.write(content)

print("Fix applied")
