"""
patterns.detect_bull_flag için birim test.
Sentetik OHLC serileriyle pozitif (gerçek bayrak) ve negatif (bayrak değil)
senaryoları doğrular. patterns.py yalnızca pandas+numpy kullanır.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from patterns import detect_bull_flag


def _ohlc(closes):
    closes = np.array(closes, dtype=float)
    high = closes * 1.01
    low = closes * 0.99
    return pd.DataFrame({"Open": closes, "High": high, "Low": low, "Close": closes})


def test_valid_bull_flag():
    # Yatay taban (14) -> sert direk (+%25, 4 bar) -> sığ konsolidasyon (6 bar)
    base = [100] * 14
    pole = [108, 116, 122, 125]            # ~%25 direk
    flag = [123, 122, 123, 121, 122, 123]  # sığ geri çekilme
    df = _ohlc(base + pole + flag)
    r = detect_bull_flag(df)
    assert r["detected"] is True, r
    assert r["score"] in (12, 18)
    assert r["retrace_pct"] <= 50

    # İdeal sığ (≤%38.2) -> 18 puan
    assert r["score"] == 18


def test_no_pole():
    # Düz/yatay seyir -> direk yok -> bayrak yok
    df = _ohlc([100 + (i % 2) for i in range(20)])
    assert detect_bull_flag(df)["detected"] is False


def test_deep_retrace_rejected():
    # Sert direk ama derin geri çekilme (>%50) -> reddedilmeli
    base = [100] * 14
    pole = [108, 116, 122, 125]
    flag = [120, 114, 110, 109, 108, 107]  # neredeyse direğin dibine dönüş
    df = _ohlc(base + pole + flag)
    assert detect_bull_flag(df)["detected"] is False


def test_short_history():
    df = _ohlc([100, 101, 102])
    assert detect_bull_flag(df)["detected"] is False


if __name__ == "__main__":
    test_valid_bull_flag()
    test_no_pole()
    test_deep_retrace_rejected()
    test_short_history()
    print("✅ BULL FLAG TESTİ GEÇTİ: pozitif ve negatif senaryolar doğru ayrışıyor.")
