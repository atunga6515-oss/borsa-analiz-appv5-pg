with open("api/analysis_routes.py", "r") as f:
    content = f.read()

old_st = """        # IND 6: SuperTrend
        supertrend_line = []
        sti = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)
        if sti is not None:
            for i in range(len(df)):
                if not pd.isna(sti['SUPERT_10_3.0'].iloc[i]):
                    supertrend_line.append({
                        "time": int(timestamps[i]),
                        "value": float(sti['SUPERT_10_3.0'].iloc[i]),
                        "color": "#26a69a" if sti['SUPERTd_10_3.0'].iloc[i] == 1 else "#ef5350"
                    })"""

new_st = """        # IND 6: SuperTrend
        supertrend_line = []
        sti = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)
        if sti is not None:
            st_col = [col for col in sti.columns if 'SUPERT_' in col][0]
            dir_col = [col for col in sti.columns if 'SUPERTd_' in col][0]
            for i in range(len(df)):
                if not pd.isna(sti[st_col].iloc[i]):
                    supertrend_line.append({
                        "time": int(timestamps[i]),
                        "value": float(sti[st_col].iloc[i]),
                        "color": "#26a69a" if sti[dir_col].iloc[i] == 1 else "#ef5350"
                    })"""

content = content.replace(old_st, new_st)

with open("api/analysis_routes.py", "w") as f:
    f.write(content)

print("SuperTrend Patched")
