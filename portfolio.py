import pandas as pd
from datetime import datetime
import os
from database import engine
from sqlalchemy import text

def alis_yap(username: str, ticker: str, adet: float, fiyat: float, not_text: str = "", sl: float = None, tp: float = None, var_risk: float = None, alis_tarihi: str = None):
    """Sanal portföye hisse alımı ekler."""
    if alis_tarihi is None:
        alis_tarihi = datetime.now().strftime("%Y-%m-%d %H:%M")
        
    with engine.begin() as conn:
        # Check if an open position already exists
        existing = conn.execute(text("""
            SELECT id, adet, alis_fiyati FROM portfolio 
            WHERE username=:u AND ticker=:t AND durum='ACIK'
        """), {"u": username, "t": ticker.upper()}).fetchone()
        
        if existing:
            # Merge logic
            trade_id = existing[0]
            eski_adet = float(existing[1])
            eski_fiyat = float(existing[2])
            
            yeni_adet = eski_adet + adet
            yeni_ortalama_fiyat = ((eski_adet * eski_fiyat) + (adet * fiyat)) / yeni_adet
            
            conn.execute(text("""
                UPDATE portfolio 
                SET adet=:a, alis_fiyati=:f, alis_tarihi=:d, not_text=:n, sl=:sl, tp=:tp, var=:var 
                WHERE id=:id
            """), {
                "a": round(yeni_adet, 2), "f": round(yeni_ortalama_fiyat, 4), "d": alis_tarihi,
                "n": not_text, "sl": sl, "tp": tp, "var": var_risk, "id": trade_id
            })
        else:
            conn.execute(text("""
                INSERT INTO portfolio (username, ticker, adet, alis_fiyati, alis_tarihi, durum, not_text, sl, tp, var)
                VALUES (:u, :t, :a, :f, :d, 'ACIK', :n, :sl, :tp, :var)
            """), {
                "u": username, "t": ticker.upper(), "a": adet, "f": fiyat, 
                "d": alis_tarihi, "n": not_text,
                "sl": sl, "tp": tp, "var": var_risk
            })

def satis_yap(trade_id: int, satis_fiyati: float):
    """Açık pozisyonu kapatır (sanal satış)."""
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE portfolio SET durum='KAPALI', satis_fiyati=:s, satis_tarihi=:d
            WHERE id=:id
        """), {
            "s": satis_fiyati, 
            "d": datetime.now().strftime("%Y-%m-%d %H:%M"), 
            "id": trade_id
        })

def acik_pozisyonlar(username: str) -> pd.DataFrame:
    """Belirli kullanıcıya ait tüm açık (satılmamış) pozisyonları döndürür."""
    with engine.connect() as conn:
        query = text("SELECT id, ticker, adet, alis_fiyati, alis_tarihi, not_text, sl, tp, var FROM portfolio WHERE durum='ACIK' AND username=:u ORDER BY alis_tarihi DESC")
        df = pd.read_sql_query(query, conn, params={"u": username})
    return df

def kapali_pozisyonlar(username: str) -> pd.DataFrame:
    """Belirli kullanıcıya ait tüm kapatılmış (satılmış) pozisyonları döndürür."""
    with engine.connect() as conn:
        query = text("SELECT id, ticker, adet, alis_fiyati, alis_tarihi, satis_fiyati, satis_tarihi, not_text, sl, tp, var FROM portfolio WHERE durum='KAPALI' AND username=:u ORDER BY satis_tarihi DESC")
        df = pd.read_sql_query(query, conn, params={"u": username})
    return df

def tum_islemler(username: str) -> pd.DataFrame:
    """Kullanıcıya ait açık ve kapalı tüm işlemleri döndürür."""
    with engine.connect() as conn:
        query = text("SELECT * FROM portfolio WHERE username=:u ORDER BY alis_tarihi DESC")
        df = pd.read_sql_query(query, conn, params={"u": username})
    return df

def islemi_sil(trade_id: int):
    """Bir işlemi tamamen siler."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM portfolio WHERE id=:id"), {"id": trade_id})

def portfoy_temizle(username: str):
    """Kullanıcının tüm portföy verilerini siler."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM portfolio WHERE username=:u"), {"u": username})

def pozisyon_guncelle(trade_id: int, yeni_adet: float, yeni_fiyat: float, yeni_tarih: str = None):
    """Mevcut bir pozisyonun adet, maliyet ve tarih bilgilerini günceller."""
    with engine.begin() as conn:
        trade = conn.execute(text("SELECT sl, alis_tarihi FROM portfolio WHERE id=:id"), {"id": trade_id}).fetchone()
        
        new_var = None
        current_date = yeni_tarih
        
        if trade:
            if current_date is None:
                current_date = trade[1]
            if trade[0] is not None:
                sl = trade[0]
                new_var = round((yeni_fiyat - sl) * yeni_adet, 2)
            
        if new_var is not None:
            conn.execute(text("""
                UPDATE portfolio SET adet=:a, alis_fiyati=:f, alis_tarihi=:d, var=:v WHERE id=:id
            """), {"a": yeni_adet, "f": yeni_fiyat, "d": current_date, "v": new_var, "id": trade_id})
        else:
            conn.execute(text("""
                UPDATE portfolio SET adet=:a, alis_fiyati=:f, alis_tarihi=:d WHERE id=:id
            """), {"a": yeni_adet, "f": yeni_fiyat, "d": current_date, "id": trade_id})
