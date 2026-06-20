"""
top_picks_common.compute_risk_position için birim test.

Konviksiyon (V6) ağırlıklı pozisyon boyutunu doğrular:
    Önerilen Ağırlık = (Risk Bütçesi% / Stop Mesafesi%) × (V6/100), maks %25

risk_manager (pandas/yfinance zinciri) sandbox'ta import edilemeyebileceği için,
calculate_position_size'in GERÇEK implementasyonunu stub modül olarak sys.modules'a
enjekte edip compute_risk_position'ı AST ile izole çalıştırıyoruz.
"""
import ast
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(HERE, "..", "top_picks_common.py")


def _real_calculate_position_size(capital, risk_pct, entry_price, stop_loss):
    # risk_manager.calculate_position_size'in birebir kopyası (referans)
    if entry_price <= stop_loss or entry_price <= 0 or capital <= 0:
        return {'max_risk_amount': 0, 'risk_per_share': 0, 'position_size': 0,
                'total_investment': 0, 'portfolio_allocation_pct': 0}
    max_risk_amount = capital * (risk_pct / 100.0)
    risk_per_share = entry_price - stop_loss
    position_size = int(max_risk_amount / risk_per_share)
    total_investment = position_size * entry_price
    allocation_pct = (total_investment / capital) * 100 if capital > 0 else 0
    return {'max_risk_amount': round(max_risk_amount, 2),
            'risk_per_share': round(risk_per_share, 2),
            'position_size': max(position_size, 0),
            'total_investment': round(total_investment, 2),
            'portfolio_allocation_pct': round(allocation_pct, 2)}


def _load_compute_risk_position():
    # Stub risk_manager modülü
    stub = types.ModuleType("risk_manager")
    stub.calculate_position_size = _real_calculate_position_size
    sys.modules["risk_manager"] = stub

    src = open(SRC_PATH, encoding="utf-8").read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "compute_risk_position":
            ns = {}
            exec(ast.get_source_segment(src, node), ns)
            return ns["compute_risk_position"]
    raise RuntimeError("compute_risk_position bulunamadı")


compute_risk_position = _load_compute_risk_position()


def _expected(live_px, sl, v6, risk_budget=1.0, cap=25.0):
    pos = _real_calculate_position_size(100000.0, risk_budget, live_px, sl or 0)
    base = pos["portfolio_allocation_pct"]
    weight = min(cap, base * (max(0.0, float(v6)) / 100.0))
    invest = (weight / 100.0) * 100000.0
    lots = int(invest / live_px) if live_px and live_px > 0 else 0
    return round(weight, 1), lots, pos["risk_per_share"]


def test_conviction_weighting():
    cases = [
        (19.90, 19.01, 89.6),   # BOBET: dar stop + yüksek skor
        (20.48, 19.83, 83.8),   # ISFIN: çok dar stop -> tavana yakın
        (86.30, 83.08, 74.5),   # AKSEN
        (50.35, 48.90, 70.8),   # BASGZ
        (100.0, 95.0, 100.0),   # tam skor
        (100.0, 95.0, 50.0),    # düşük skor -> yarı ağırlık
        (100.0, 95.0, 0.0),     # skor 0 -> ağırlık 0
        (10.0, 11.0, 80.0),     # SL >= fiyat -> 0
        (10.0, 0, 80.0),        # SL yok -> 0
    ]
    for live_px, sl, v6 in cases:
        out = compute_risk_position(live_px, sl, v6)
        exp_w, exp_lots, exp_rps = _expected(live_px, sl, v6)
        assert out["suggested_weight_pct"] == exp_w, f"{live_px}/{sl}/{v6}: {out['suggested_weight_pct']} != {exp_w}"
        assert out["lots_per_100k"] == exp_lots, f"lots {out['lots_per_100k']} != {exp_lots}"
        assert out["suggested_weight_pct"] <= 25.0
        assert out["suggested_weight_pct"] >= 0.0

    # Konviksiyon mantığı: aynı stop, yüksek skor -> daha yüksek ağırlık
    high = compute_risk_position(100.0, 96.0, 90.0)["suggested_weight_pct"]
    low = compute_risk_position(100.0, 96.0, 60.0)["suggested_weight_pct"]
    assert high > low, f"Yüksek skor daha yüksek ağırlık vermeli: {high} !> {low}"


if __name__ == "__main__":
    test_conviction_weighting()
    print("✅ RISK POSITION TESTİ GEÇTİ: konviksiyon (V6) ağırlıklandırma doğru çalışıyor.")
