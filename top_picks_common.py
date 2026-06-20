"""
Top Picks ortak yardımcıları (DRY).
Geçmiş kayıt (history) fonksiyonları, top_picks.py ve top_picks_15d.py tarafından
ortak kullanılır; tek fark veritabanı tablo adıdır, o da parametre olarak geçilir.

NOT: `table` argümanı yalnızca kod içinden sabit string'lerle çağrılır
(kullanıcı girdisi DEĞİL), bu yüzden f-string ile tablo adı enterpolasyonu güvenlidir.
"""
import json
from datetime import datetime
import pytz
from sqlalchemy import text
from database import engine

TR_TZ = pytz.timezone("Europe/Istanbul")


def save_picks_history(table: str, username: str, results: list):
    """Tarama sonuçlarını ilgili history tablosuna JSON olarak kaydeder (son 30 kayıt tutulur)."""
    if not results:
        return
    now_str = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M:%S")
    with engine.begin() as conn:
        conn.execute(
            text(f"INSERT INTO {table} (username, run_date, results_json) VALUES (:u, :d, :r)"),
            {"u": username, "d": now_str, "r": json.dumps(results)}
        )
        # Sadece son 30 kalsın
        conn.execute(text(f"""
            DELETE FROM {table}
            WHERE username = :u AND id NOT IN (
                SELECT id FROM {table}
                WHERE username = :u
                ORDER BY id DESC LIMIT 30
            )
        """), {"u": username})


def get_history_dates(table: str, username: str) -> list:
    """Kaydedilmiş analiz tarihlerini id ve run_date olarak döndürür."""
    with engine.connect() as conn:
        cursor = conn.execute(
            text(f"SELECT id, run_date FROM {table} WHERE username=:u ORDER BY id DESC"),
            {"u": username}
        )
        return [{"id": row[0], "run_date": row[1]} for row in cursor.fetchall()]


def get_picks_by_date(table: str, username: str, history_id: int) -> list:
    """Belirli bir ID'deki analiz sonuçlarını döndürür."""
    with engine.connect() as conn:
        cursor = conn.execute(
            text(f"SELECT results_json FROM {table} WHERE username=:u AND id=:id"),
            {"u": username, "id": history_id}
        )
        row = cursor.fetchone()
    return json.loads(row[0]) if row else []
