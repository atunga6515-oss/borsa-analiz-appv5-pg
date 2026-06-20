"""
Sinyal Karnesi (Model Scorecard)
================================
Üretilen Seçki 15G sinyallerinin vade sonu (15 işlem günü) gerçek getirisini ölçer.
Global (model-düzeyi): aynı (hisse, gün, strateji) bir kez kaydedilir.

Akış:
  1) run_daily_snapshot()  -> Her gün BIST TÜM taranır, AL yönelimli sinyaller kaydedilir.
  2) score_matured_signals() -> Vadesi dolan sinyaller güncel fiyatla puanlanır.
  3) get_scorecard_summary() -> Skor bandı + Boğa Flaması bazında isabet/getiri özeti.

NOT: Saf hesaplama (özetleme/bandlama) test edilebilir; DB/ağ kısmı prod'da çalışır.
"""
import numpy as np
from datetime import datetime
import pytz
from sqlalchemy import text
from database import engine

TR_TZ = pytz.timezone("Europe/Istanbul")
STRATEGY = "15G"
HORIZON_BDAYS = 15  # 15 işlem (iş) günü


def _today_str() -> str:
    return datetime.now(TR_TZ).strftime("%Y-%m-%d")


# ============================================================
# 1) GÜNLÜK SNAPSHOT — sinyalleri kaydet
# ============================================================
def run_daily_snapshot() -> int:
    """BIST TÜM üzerinde Seçki 15G tarar; AL yönelimli sinyalleri karneye (deduplike) kaydeder."""
    from top_picks_15d import find_top_picks
    from screener import BIST_ALL_SYMBOLS

    today = _today_str()
    try:
        # top_n çok yüksek -> tüm uygun (AL yönelimli) adayları getir
        results = find_top_picks(symbol_list=BIST_ALL_SYMBOLS, top_n=100000)
    except Exception as e:
        print(f"[KARNE] Snapshot tarama hatası: {e}")
        return 0

    inserted = 0
    try:
        with engine.begin() as conn:
            for r in results:
                tkr = r.get("ticker")
                price = float(r.get("fiyat", 0) or 0)
                if not tkr or price <= 0:
                    continue

                exists = conn.execute(
                    text("SELECT 1 FROM signal_scorecard WHERE ticker=:t AND signal_date=:d AND strategy=:s"),
                    {"t": tkr, "d": today, "s": STRATEGY},
                ).fetchone()
                if exists:
                    continue

                summary = str(r.get("summary", ""))
                has_flag = "Boğa Flaması" in summary

                conn.execute(text("""
                    INSERT INTO signal_scorecard
                      (ticker, strategy, signal_date, score, decision, entry_price,
                       horizon_days, has_bull_flag, status)
                    VALUES (:t, :s, :d, :sc, :dec, :ep, :h, :bf, 'pending')
                """), {
                    "t": tkr, "s": STRATEGY, "d": today,
                    "sc": float(r.get("kompozit_skor", 0) or 0),
                    "dec": str(r.get("karar", ""))[:100],
                    "ep": price, "h": HORIZON_BDAYS, "bf": bool(has_flag),
                })
                inserted += 1
    except Exception as e:
        print(f"[KARNE] Snapshot kayıt hatası: {e}")
        return inserted

    print(f"[KARNE] {today}: {inserted} sinyal kaydedildi.")
    return inserted


# ============================================================
# 2) PUANLAMA — vadesi dolanları değerlendir
# ============================================================
def score_matured_signals() -> int:
    """Vadesi (15 işlem günü) dolmuş bekleyen sinyalleri güncel fiyatla puanlar."""
    from data_loader import get_live_price

    today = datetime.now(TR_TZ).date()
    scored = 0
    try:
        with engine.begin() as conn:
            pend = conn.execute(text(
                "SELECT id, ticker, signal_date, entry_price FROM signal_scorecard WHERE status='pending'"
            )).fetchall()

            for rid, tkr, sdate, entry in pend:
                try:
                    d0 = datetime.strptime(str(sdate)[:10], "%Y-%m-%d").date()
                except Exception:
                    continue
                # 15 işlem günü dolmadıysa atla
                if int(np.busday_count(d0, today)) < HORIZON_BDAYS:
                    continue

                entry = float(entry or 0)
                if entry <= 0:
                    continue
                px = get_live_price(tkr)
                if not px or px <= 0:
                    continue

                ret = (px - entry) / entry * 100.0
                conn.execute(text("""
                    UPDATE signal_scorecard
                    SET status='scored', eval_date=:ed, exit_price=:xp, return_pct=:r, win=:w
                    WHERE id=:id
                """), {
                    "ed": today.strftime("%Y-%m-%d"), "xp": float(px),
                    "r": round(ret, 2), "w": bool(ret > 0), "id": rid,
                })
                scored += 1
    except Exception as e:
        print(f"[KARNE] Puanlama hatası: {e}")
        return scored

    print(f"[KARNE] {scored} sinyal puanlandı.")
    return scored


# ============================================================
# 3) ÖZET — saf hesaplama (test edilebilir)
# ============================================================
def _bucket(rows) -> dict:
    """rows: (score, decision, return_pct, win, has_bull_flag) tuple listesi."""
    n = len(rows)
    if n == 0:
        return {"count": 0, "win_rate": 0.0, "avg_return": 0.0}
    wins = sum(1 for x in rows if x[3])
    avg = sum((x[2] or 0.0) for x in rows) / n
    return {"count": n, "win_rate": round(wins / n * 100, 1), "avg_return": round(avg, 2)}


def summarize_rows(scored, pending_count: int = 0) -> dict:
    """Puanlanmış satırlardan skor bandı + Boğa Flaması bazında özet üretir (saf fonksiyon)."""
    def sc(r):  # skor güvenli
        return r[0] or 0
    bands = {
        "guclu_al": [r for r in scored if sc(r) >= 80],
        "al":       [r for r in scored if 70 <= sc(r) < 80],
        "orta":     [r for r in scored if 55 <= sc(r) < 70],
        "dusuk":    [r for r in scored if sc(r) < 55],
    }
    return {
        "overall": _bucket(scored),
        "bands": {k: _bucket(v) for k, v in bands.items()},
        "bull_flag": _bucket([r for r in scored if r[4]]),
        "no_bull_flag": _bucket([r for r in scored if not r[4]]),
        "scored_count": len(scored),
        "pending_count": int(pending_count),
    }


def get_scorecard_summary() -> dict:
    """DB'den puanlanmış sinyalleri çekip özet döndürür."""
    try:
        with engine.connect() as conn:
            scored = conn.execute(text("""
                SELECT score, decision, return_pct, win, has_bull_flag
                FROM signal_scorecard WHERE status='scored'
            """)).fetchall()
            pending = conn.execute(text(
                "SELECT COUNT(*) FROM signal_scorecard WHERE status='pending'"
            )).scalar() or 0
        rows = [(r[0], r[1], r[2], r[3], r[4]) for r in scored]
        return summarize_rows(rows, pending)
    except Exception as e:
        print(f"[KARNE] Özet hatası: {e}")
        return summarize_rows([], 0)
