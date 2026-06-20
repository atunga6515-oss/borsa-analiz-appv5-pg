import sys
sys.path.append(".")
from api.analysis_routes import fetch_layered_data

res = fetch_layered_data("ASTOR")
if res is None:
    print("RES IS NONE")
    sys.exit(1)

times = []
for c in res['candles']: times.append(c['time'])
for l in res['layers']['auto_trend']: times.append(l['time'])
for l in res['layers']['alpha_signal']: times.append(l['time'])
for l in res['layers']['squeeze']: times.append(l['time'])
for l in res['layers']['smc_fvg']: times.append(l['time'])
for l in res['layers']['wavetrend']: times.append(l['time'])
for l in res['layers']['supertrend']: times.append(l['time'])
for l in res['layers']['divergence']: times.append(l['time'])
for l in res['layers']['anchored_vwap']: times.append(l['time'])
for l in res['layers']['chandelier']: times.append(l['time'])

print(f"Min time: {min(times)}")
print(f"Max time: {max(times)}")
print(f"Candles min: {min(c['time'] for c in res['candles'])}")
print(f"Candles max: {max(c['time'] for c in res['candles'])}")
