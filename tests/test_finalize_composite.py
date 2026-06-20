"""
top_picks_common.finalize_composite için DENKLİK (equivalence) testi.

Amaç: dedup sonrası ortak finalize_composite fonksiyonunun, top_picks.py (Orta-Uzun)
ve top_picks_15d.py (15 Gün) içindeki ORİJİNAL satır-içi skorlama akışlarıyla
birebir aynı sonucu (composite, rr, alpha_text, karar, summary) verdiğini kanıtlar.

Not: top_picks_common modülü DB/sqlalchemy import ettiği için, sandbox'ta tüm modülü
import etmek yerine SADECE finalize_composite fonksiyonunun kaynağını AST ile çıkarıp
izole exec ederek gerçek kodu test ediyoruz (fonksiyon yalnızca builtin kullanıyor).
"""
import ast
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(HERE, "..", "top_picks_common.py")


def _load_finalize():
    src = open(SRC_PATH, encoding="utf-8").read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "finalize_composite":
            fn_src = ast.get_source_segment(src, node)
            ns = {}
            exec(fn_src, ns)
            return ns["finalize_composite"]
    raise RuntimeError("finalize_composite bulunamadı")


finalize_composite = _load_finalize()


# --- ORİJİNAL satır-içi akışların BİREBİR transkripsiyonu (referans) ---

def ref_pipeline(composite, inp, sent_100, is_bear, pbs, core_decision, summary, mid_clamp):
    alpha_text = "-"
    alpha_bonus = 0
    if inp["has_5d"]:
        xu = inp["xu100_5d_chg"]; s5 = inp["sym_5d"]
        av = s5 - xu
        alpha_text = f"{av:+.1f}%"
        if xu < -1.0 and s5 > -0.5:
            alpha_bonus = 20
            summary.append(f"\n💪 Endeksten Güçlü Ayrışma (Alpha: {alpha_text})")
    composite += alpha_bonus

    if mid_clamp:                       # 15 Gün motoru: alpha'dan sonra min(100)
        composite = min(100.0, composite)

    rr = 0.0
    if inp["rr_has"]:
        risk = inp["live_px"] - inp["rr_sup"]
        reward = inp["rr_res"] - inp["live_px"]
        if risk > 0:
            rr = reward / risk
            if rr < 2.0:
                composite -= 30
                summary.append(f"\n⛔ Risk/Getiri Çok Düşük (R/R: {rr:.2f}). -30 Ceza!")
        elif risk <= 0:
            rr = 5.0

    if inp["rsi_1w"] is not None and inp["rsi_1w"] > 80:
        composite -= 30
        summary.append(f"\n⛔ MTF VETO: Haftalık RSI ({inp['rsi_1w']:.1f}) Çok Şişkin. Düzeltme Riski!")

    if sent_100 < 20:
        composite -= 50
        summary.append("\n🚨 AI VETO: Kara Bulut (Çok Negatif Haberler)")

    if inp["upper_shadow"] is not None and inp["upper_shadow"] > 0.5:
        composite *= 0.85
        summary.append("\n⚠️ Üst fitil baskısı (Zirve Reddi) tespit edildi.")

    if inp["dist_ema20"] is not None and inp["dist_ema20"] > 0.12:
        composite *= 0.9
        summary.append(f"\n🧲 EMA 20'den çok uzak (%{inp['dist_ema20']*100:.1f}), düzeltme riski.")

    if is_bear and pbs:
        composite *= 0.85

    if mid_clamp:
        composite = max(0, round(composite, 1))          # 15 Gün orijinali
    else:
        composite = min(100, max(0, round(composite, 1)))  # Orta-Uzun orijinali

    karar = core_decision
    if composite >= 70 and inp["rsi_last"] is not None and inp["rsi_last"] > 65:
        karar = "🧘 Doygunluk Bölgesi"
        summary.append("\n🧘 RSI Doygunluğu: Kar satışı gelebilir.")
    if inp["daily_chg"] is not None and inp["daily_chg"] < -2.0:
        if any(w in karar for w in ["Trend", "Lideri", "Potansiyeli"]):
            karar = "⚠️ Bekle (Endeks Freni)"

    return composite, rr, alpha_text, karar


def _rand_or_none(rng, lo, hi, none_p=0.25):
    if rng.random() < none_p:
        return None
    return round(rng.uniform(lo, hi), 3)


def _rand_inp(rng):
    has_5d = rng.random() < 0.7
    rr_has = rng.random() < 0.7
    live_px = round(rng.uniform(1, 500), 2)
    return {
        "live_px": live_px,
        "has_5d": has_5d,
        "xu100_5d_chg": round(rng.uniform(-6, 6), 3) if has_5d else None,
        "sym_5d": round(rng.uniform(-8, 8), 3) if has_5d else None,
        "rr_has": rr_has,
        "rr_sup": round(live_px * rng.uniform(0.8, 1.05), 2) if rr_has else None,
        "rr_res": round(live_px * rng.uniform(0.95, 1.4), 2) if rr_has else None,
        "rsi_1w": _rand_or_none(rng, 0, 100),
        "upper_shadow": _rand_or_none(rng, 0, 1),
        "dist_ema20": _rand_or_none(rng, -0.3, 0.4),
        "rsi_last": _rand_or_none(rng, 0, 100),
        "daily_chg": _rand_or_none(rng, -5, 5),
    }


def test_equivalence_both_strategies():
    rng = random.Random(20260620)
    kararlar = ["📈 Pozitif Trend", "🚀 Momentum Lideri", "⚖️ Nötr / Konsolidasyon",
                "🔥 Tepki Potansiyeli", "📉 Negatif Baskı", "Nötr"]
    n = 40000
    for _ in range(n):
        inp = _rand_inp(rng)
        composite0 = round(rng.uniform(-20, 140), 3)
        sent_100 = round(rng.uniform(0, 100), 2)
        is_bear = rng.random() < 0.5
        pbs = rng.random() < 0.5
        core_decision = rng.choice(kararlar)

        for mid_clamp in (False, True):
            s_new, s_ref = [], []
            r_new = finalize_composite(
                composite0, inp, sent_100=sent_100, is_bear=is_bear,
                price_below_sma50=pbs, core_decision=core_decision,
                clamp_100_after_alpha=mid_clamp, summary=s_new,
            )
            r_ref = ref_pipeline(
                composite0, inp, sent_100, is_bear, pbs, core_decision, s_ref, mid_clamp,
            )
            assert r_new == r_ref, f"Sonuç farkı! mid={mid_clamp} inp={inp}\nnew={r_new}\nref={r_ref}"
            assert s_new == s_ref, f"Özet farkı! mid={mid_clamp}\nnew={s_new}\nref={s_ref}"


if __name__ == "__main__":
    test_equivalence_both_strategies()
    print("✅ DENKLİK TESTİ GEÇTİ: finalize_composite, her iki orijinal akışla birebir aynı.")
