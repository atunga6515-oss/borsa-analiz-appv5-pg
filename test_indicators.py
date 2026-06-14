import pandas as pd
from signals_engine import get_all_indicator_rules
import re

df = pd.DataFrame({'Close': [1]*300, 'Open': [1]*300, 'High': [1]*300, 'Low': [1]*300, 'Volume': [1]*300})
_, rules = get_all_indicator_rules(df)

pools = {"short": [], "medium": [], "long": []}

for name in rules.keys():
    horizon = "medium"
    if "Bollinger" in name or "Keltner" in name:
        period = 20
    elif "Awesome" in name:
        period = 34
    else:
        nums = [int(x) for x in re.findall(r'\d+', name)]
        period = max(nums) if nums else 20
        
    if period <= 15:
        horizon = "short"
    elif period >= 75:
        horizon = "long"
    else:
        horizon = "medium"
        
    pools[horizon].append((name, period))

print(f"Total Indicators: {len(rules)}")
print(f"Short Term (<=15 days): {len(pools['short'])}")
print(f"Medium Term (16-74 days): {len(pools['medium'])}")
print(f"Long Term (>=75 days): {len(pools['long'])}")
print("\n--- SHORT TERM ---")
for n, p in pools['short'][:5]: print(f"- {n} (Periyot: {p})")
print("...")
print("\n--- MEDIUM TERM ---")
for n, p in pools['medium'][:5]: print(f"- {n} (Periyot: {p})")
print("...")
print("\n--- LONG TERM ---")
for n, p in pools['long']: print(f"- {n} (Periyot: {p})")

