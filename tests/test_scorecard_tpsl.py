import ast
import os
import pandas as pd
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))

def _load_fn(file_name, fn_name):
    src_path = os.path.join(HERE, "..", file_name)
    src = open(src_path, encoding="utf-8").read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            fn_src = ast.get_source_segment(src, node)
            ns = {"HORIZON_BDAYS": 15, "pd": pd}
            exec(fn_src, ns)
            return ns[fn_name]
    raise RuntimeError(f"{fn_name} not found in {file_name}")

evaluate_signal_tpsl = _load_fn("scorecard.py", "evaluate_signal_tpsl")
finalize_composite = _load_fn("top_picks_common.py", "finalize_composite")


def test_tpsl_hit_tp():
    """Hisse 3. günde TP (+%10) yaparsa işlem KÂRLI (TP) kapanmalı."""
    dates = pd.date_range(start="2026-01-01", periods=10, freq="D")
    data = {
        "Open": [100.0] * 10,
        "High": [101.0, 102.0, 112.0, 105.0, 103.0, 101.0, 100.0, 99.0, 98.0, 97.0],
        "Low":  [99.0, 99.5, 100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 94.0, 93.0],
        "Close": [100.5, 101.5, 111.0, 104.0, 102.0, 100.0, 98.0, 97.0, 96.0, 95.0],
        "Volume": [1000] * 10
    }
    df = pd.DataFrame(data, index=dates)

    res = evaluate_signal_tpsl(
        df=df,
        signal_date_str="2026-01-01",
        entry_price=100.0,
        take_profit=110.0,
        stop_loss=95.0
    )

    assert res is not None
    assert res['win'] is True
    assert res['exit_reason'] == 'TP'
    assert res['exit_price'] == 110.0
    assert res['return_pct'] == 10.0


def test_tpsl_hit_sl():
    """Hisse 2. günde SL (-%5) düşerse işlem ZARARLA (SL) kapanmalı."""
    dates = pd.date_range(start="2026-01-01", periods=10, freq="D")
    data = {
        "Open": [100.0] * 10,
        "High": [101.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
        "Low":  [99.0, 94.0, 95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0, 102.0],
        "Close": [100.0, 94.5, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0, 102.0, 103.0],
        "Volume": [1000] * 10
    }
    df = pd.DataFrame(data, index=dates)

    res = evaluate_signal_tpsl(
        df=df,
        signal_date_str="2026-01-01",
        entry_price=100.0,
        take_profit=110.0,
        stop_loss=95.0
    )

    assert res is not None
    assert res['win'] is False
    assert res['exit_reason'] == 'SL'
    assert res['exit_price'] == 95.0
    assert res['return_pct'] == -5.0


def test_overbought_protection():
    """RSI >= 70 iken skordan 25 ceza düşülmeli ve skor maks 69.9 ile sınırlanmalı."""
    summary = []
    inp = {
        "has_5d": False,
        "rr_has": False,
        "rsi_1w": None,
        "upper_shadow": None,
        "dist_ema20": None,
        "rsi_last": 75.0,  # Aşırı alım
        "dist_res_pct": 1.5, # Dirence %1.5 yakın (tepe)
        "daily_chg": 0.0,
    }

    comp, rr, alpha, karar = finalize_composite(
        composite=85.0,  # Güçlü Al aday skoru
        inp=inp,
        sent_100=80.0,
        is_bear=False,
        price_below_sma50=False,
        core_decision="Al",
        clamp_100_after_alpha=True,
        summary=summary
    )

    # Skor 69.9'u geçemez, Güçlü Al olamaz
    assert comp <= 69.9
    assert any("Aşırı Alım" in s for s in summary)


if __name__ == "__main__":
    test_tpsl_hit_tp()
    test_tpsl_hit_sl()
    test_overbought_protection()
    print("✅ TÜM TP/SL VE AŞIRI ALIM KORUMASI TESTLERİ BAŞARIYLA GEÇTİ.")
