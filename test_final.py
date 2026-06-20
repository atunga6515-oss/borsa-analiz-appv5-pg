from fastapi import FastAPI
import sys
import traceback
sys.path.append(".")
from api.analysis_routes import fetch_layered_data
try:
    res = fetch_layered_data("THYAO")
    print("Success. Ticker:", res['ticker'])
except Exception as e:
    print("Failed")
    traceback.print_exc()
