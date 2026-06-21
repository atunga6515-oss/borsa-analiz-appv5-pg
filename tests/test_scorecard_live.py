"""
scorecard.summarize_live için birim test (saf hesaplama, DB/ağ yok).
summarize_live yalnızca builtin kullanır; AST ile izole exec edilir.
"""
import ast
import os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scorecard.py")


def _load():
    src = open(SRC, encoding="utf-8").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name == "summarize_live":
            ns = {}
            exec(ast.get_source_segment(src, node), ns)
            return ns["summarize_live"]
    raise RuntimeError("summarize_live bulunamadı")


summarize_live = _load()

# (cur_return_pct, days_elapsed)
ITEMS = [
    (5.0, 2),    # week1, kârda
    (-2.0, 3),   # week1, zararda
    (8.0, 6),    # week2, kârda
    (1.0, 7),    # week2, kârda
    (-4.0, 12),  # week3, zararda
    (10.0, 14),  # week3, kârda
]


def test_overall():
    s = summarize_live(ITEMS)
    assert s["tracked"] == 6
    assert s["overall"]["count"] == 6
    # ort = (5-2+8+1-4+10)/6 = 18/6 = 3.0
    assert s["overall"]["avg_return"] == 3.0
    # kârda 4/6 = %66.7
    assert s["overall"]["in_profit_pct"] == 66.7


def test_weeks():
    s = summarize_live(ITEMS)
    assert s["week1"]["count"] == 2
    assert s["week1"]["in_profit_pct"] == 50.0      # 1/2
    assert s["week2"]["count"] == 2
    assert s["week2"]["in_profit_pct"] == 100.0     # 2/2
    assert s["week2"]["avg_return"] == 4.5          # (8+1)/2
    assert s["week3"]["count"] == 2
    assert s["week3"]["in_profit_pct"] == 50.0      # 1/2


def test_empty():
    s = summarize_live([])
    assert s["tracked"] == 0
    assert s["overall"]["count"] == 0
    assert s["overall"]["avg_return"] == 0.0
    assert s["week1"]["count"] == 0


if __name__ == "__main__":
    test_overall()
    test_weeks()
    test_empty()
    print("✅ SCORECARD LIVE TESTİ GEÇTİ: anlık ort. getiri, kârda %, hafta gruplaması doğru.")
