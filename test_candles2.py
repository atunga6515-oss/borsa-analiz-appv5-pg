import sys
sys.path.append(".")
from api.analysis_routes import fetch_layered_data
import asyncio
import json

res = fetch_layered_data("ASTOR")
if not res:
    print("RES IS NONE")
else:
    for c in res['candles']:
        if c['open'] is None or c['high'] is None or c['low'] is None or c['close'] is None:
            print("FOUND NONE IN CANDLES!", c)
            break
    else:
        print("CANDLES ARE PERFECT. Length:", len(res['candles']))
