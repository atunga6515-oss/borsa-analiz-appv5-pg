import yfinance as yf
from screener import BIST_ALL_SYMBOLS

print(f"Total symbols: {len(BIST_ALL_SYMBOLS)}")
test_syms = BIST_ALL_SYMBOLS[:3]
for sym in test_syms:
    try:
        t = yf.Ticker(sym + ".IS")
        info = t.info
        name = info.get("longName", info.get("shortName", ""))
        print(f"{sym}: {name}")
    except Exception as e:
        print(f"{sym}: ERROR {e}")
