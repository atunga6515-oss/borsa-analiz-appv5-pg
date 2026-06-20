import sys
sys.path.append(".")
from api.analysis_routes import fetch_layered_data
import json

try:
    res = fetch_layered_data("ASTOR")
    print("Candles:", json.dumps(res['candles'][:2]))
    print("Squeeze:", json.dumps(res['layers']['squeeze'][:2]))
    print("Alpha:", json.dumps(res['layers']['alpha_signal'][:2]))
except Exception as e:
    import traceback
    traceback.print_exc()
