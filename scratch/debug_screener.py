import os
os.environ["DATABASE_URL"] = "sqlite:///test.db"

from database import engine, Base
from sqlalchemy import text

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                ticker TEXT, date TEXT, interval TEXT, open REAL, high REAL, low REAL, close REAL, adj_close REAL, volume REAL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS takas_data (
                ticker TEXT, date TEXT, foreign_ratio REAL, daily_change REAL
            )
        """))
        conn.commit()
except Exception as e:
    pass

import sys
import traceback
from screener import _analyze_single_stock
from indicators import get_market_regime
import yfinance as yf

# mock xu100
df = yf.download("XU100.IS", period="1y", progress=False)
mr = get_market_regime(df)

try:
    res = _analyze_single_stock("THYAO.IS", market_regime=mr)
    print("Result:", res)
except Exception as e:
    traceback.print_exc()
