import sys
sys.path.append(".")
from api.analysis_routes import fetch_layered_data
import json

res = fetch_layered_data("AEFES")
with open("test_aefes_output.json", "w") as f:
    json.dump(res, f)

print("Candles len:", len(res['candles']))
print("Status:", res['status'])
