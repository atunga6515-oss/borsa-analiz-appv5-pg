"""
signals_engine._short_term_weight için birim test.

Kısa vade osilatör ağırlıklandırmasının indikatör sınıflarına doğru atandığını
doğrular. signals_engine ağır importlar içerdiğinden, fonksiyonu AST ile izole
çıkarıp test ediyoruz (yalnızca string işlemleri içerir).
"""
import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "signals_engine.py")


def _load():
    src = open(SRC, encoding="utf-8").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name == "_short_term_weight":
            ns = {}
            exec(ast.get_source_segment(src, node), ns)
            return ns["_short_term_weight"]
    raise RuntimeError("_short_term_weight bulunamadı")


w = _load()


def test_weights():
    # Yüksek (2.0): RSI, Bollinger, Williams
    assert w("RSI 14 Sinyali") == 2.0
    assert w("RSI 7 Sinyali") == 2.0
    assert w("Bollinger 2.0SD Sınırı") == 2.0
    assert w("Williams %R 14") == 2.0

    # Düşük (0.5): MA aileleri, MACD, ADX, Donchian, Vortex, Aroon, VWAP
    assert w("SMA 50 Trend") == 0.5
    assert w("EMA 20 Trend") == 0.5
    assert w("EMA 50/200 Altın Kesişim") == 0.5
    assert w("WMA 20 Trend") == 0.5
    assert w("KAMA 10 Trend") == 0.5
    assert w("MACD 12/26/9 Kesişimi") == 0.5
    assert w("ADX 14 Sinyali") == 0.5
    assert w("Donchian 20 Kanalı") == 0.5
    assert w("Vortex 14 Kesişimi") == 0.5
    assert w("Aroon 25 Oscillator") == 0.5
    assert w("VWAP 20 Fiyat Trendi") == 0.5

    # Orta (1.0): diğer osilatörler
    assert w("Stoch 14 Kesişimi") == 1.0
    assert w("StochRSI 14 Kesişimi") == 1.0   # 'RSI ' ile BAŞLAMAZ -> 1.0
    assert w("CCI 14 Kanalı") == 1.0
    assert w("MFI 14 Para Akışı") == 1.0
    assert w("CMF 20 Para Dağılımı") == 1.0
    assert w("ROC 10 Momentum") == 1.0
    assert w("Awesome Oscillator AO") == 1.0
    assert w("Keltner 2.0 Sınırı") == 1.0
    assert w("Ease of Movement 14") == 1.0


if __name__ == "__main__":
    test_weights()
    print("✅ SHORT-TERM WEIGHT TESTİ GEÇTİ: tüm indikatör sınıfları doğru ağırlıkta.")
