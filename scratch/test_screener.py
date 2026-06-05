from screener import _analyze_single_stock
from indicators import get_market_regime
from data_loader import fetch_data
import traceback

xu100 = fetch_data("XU100", interval="1d", period="1y")
mr = get_market_regime(xu100)

try:
    res = _analyze_single_stock("THYAO.IS", market_regime=mr)
    print("Result:", res)
except Exception as e:
    traceback.print_exc()
