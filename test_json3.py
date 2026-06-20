from api.analysis_routes import fetch_layered_data
import json

res = fetch_layered_data("ASTOR")
print(json.dumps(res['candles'][:2]))
