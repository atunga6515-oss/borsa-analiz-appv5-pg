"""
scorecard.summarize_rows / _bucket için birim test (saf hesaplama).
scorecard.py DB importları içerdiğinden, fonksiyonları AST ile izole exec ediyoruz.
"""
import ast
import os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scorecard.py")


def _load():
    src = open(SRC, encoding="utf-8").read()
    ns = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name in ("_bucket", "summarize_rows"):
            exec(ast.get_source_segment(src, node), ns)
    return ns["summarize_rows"]


summarize_rows = _load()

# satır formatı: (score, decision, return_pct, win, has_bull_flag)
ROWS = [
    (89.0, "Güçlü Al", 8.0, True, True),    # guclu_al, kazanç, bayrak
    (85.0, "Güçlü Al", -3.0, False, False),  # guclu_al, kayıp
    (75.0, "Al", 4.0, True, True),           # al, kazanç, bayrak
    (72.0, "Al", -1.0, False, False),        # al, kayıp
    (60.0, "Nötr", 2.0, True, False),        # orta, kazanç
    (40.0, "Sat", -5.0, False, False),       # dusuk, kayıp
]


def test_overall():
    s = summarize_rows(ROWS, pending_count=7)
    assert s["scored_count"] == 6
    assert s["pending_count"] == 7
    # 6 satır, 3 kazanç -> %50 isabet
    assert s["overall"]["count"] == 6
    assert s["overall"]["win_rate"] == 50.0
    # ortalama getiri = (8-3+4-1+2-5)/6 = 5/6 = 0.83
    assert abs(s["overall"]["avg_return"] - 0.83) < 0.01


def test_bands():
    s = summarize_rows(ROWS)
    assert s["bands"]["guclu_al"]["count"] == 2
    assert s["bands"]["guclu_al"]["win_rate"] == 50.0
    assert s["bands"]["al"]["count"] == 2
    assert s["bands"]["orta"]["count"] == 1
    assert s["bands"]["orta"]["win_rate"] == 100.0
    assert s["bands"]["dusuk"]["count"] == 1
    assert s["bands"]["dusuk"]["win_rate"] == 0.0


def test_bull_flag_split():
    s = summarize_rows(ROWS)
    # bayraklı 2 sinyal (ikisi de kazanç) -> %100
    assert s["bull_flag"]["count"] == 2
    assert s["bull_flag"]["win_rate"] == 100.0
    # bayraksız 4 sinyal, 1 kazanç -> %25
    assert s["no_bull_flag"]["count"] == 4
    assert s["no_bull_flag"]["win_rate"] == 25.0


def test_empty():
    s = summarize_rows([], 0)
    assert s["overall"]["count"] == 0
    assert s["overall"]["win_rate"] == 0.0
    assert s["scored_count"] == 0


if __name__ == "__main__":
    test_overall()
    test_bands()
    test_bull_flag_split()
    test_empty()
    print("✅ SCORECARD ÖZET TESTİ GEÇTİ: bandlama, isabet, getiri ve bayrak ayrımı doğru.")
