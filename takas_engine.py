import requests
from bs4 import BeautifulSoup
import re
import os
from database import engine
from sqlalchemy import text
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz
from io import StringIO

TR_TZ = pytz.timezone("Europe/Istanbul")



class TakasScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_all(self):
        """Mynet Finans Yabanci Takas Paylari sayfasından verileri çeker."""
        url = "https://finans.mynet.com/borsa/hisseler/yabanci-takas-paylari/"
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            if response.status_code != 200: return {}
            
            tables = pd.read_html(StringIO(response.text), decimal=',', thousands='.')
            if not tables: return {}
            
            df = tables[0]
            results = {}
            
            for _, row in df.iterrows():
                try:
                    # Mynet formatı: Hisse | Yabancı Payı | ...
                    raw_ticker = str(row.iloc[0]).strip()
                    if not raw_ticker or raw_ticker == "nan": continue
                    
                    ticker = raw_ticker.split()[0].upper()
                    ticker = re.sub(r'[^A-Z0-9]', '', ticker)
                    if not ticker or len(ticker) < 3: continue

                    # Yabancı oranını bul (genelde 2. veya 3. sütun)
                    ratio = 0.0
                    # DataFrame içindeki sayısal değerleri tara
                    for ci in range(1, len(row)):
                        try:
                            s_val = str(row.iloc[ci]).replace("%", "").replace(",", ".").replace(".", "").strip()
                            # Binlik ayracı temizlendiği için tekrar virgül kontrolü
                            s_val = str(row.iloc[ci]).replace("%", "").replace(",", ".").strip()
                            f_val = float(s_val)
                            if 0.0 <= f_val <= 100.0:
                                ratio = f_val
                                break
                        except: continue
                    
                    results[ticker] = ratio
                except: continue
            
            return results
        except Exception:
            return {}


def update_all_takas():
    today = datetime.now(TR_TZ).strftime('%Y-%m-%d')
    try:
        with engine.begin() as conn:
            # Bugünün verisi zaten var mı?
            cur = conn.execute(text("SELECT COUNT(*) FROM takas_data WHERE date=:d"), {"d": today})
            if cur.fetchone()[0] > 100:
                return True
                
            scraper = TakasScraper()
            data = scraper.fetch_all()
            
            if not data:
                return False
                
            for ticker, ratio in data.items():
                # Günlük değişimi hesapla (Önceki en son veriyi bul)
                cur = conn.execute(text("SELECT foreign_ratio FROM takas_data WHERE ticker=:t AND date < :d ORDER BY date DESC LIMIT 1"), {"t": ticker, "d": today})
                prev_row = cur.fetchone()
                daily_change = 0.0
                if prev_row:
                    daily_change = round(ratio - prev_row[0], 3)

                if engine.name == 'postgresql':
                    conn.execute(text("""
                        INSERT INTO takas_data (ticker, date, foreign_ratio, daily_change) 
                        VALUES (:t, :d, :f, :c)
                        ON CONFLICT (ticker, date) DO UPDATE 
                        SET foreign_ratio = EXCLUDED.foreign_ratio, daily_change = EXCLUDED.daily_change
                    """), {"t": ticker, "d": today, "f": ratio, "c": daily_change})
                else:
                    conn.execute(text("""
                        INSERT OR REPLACE INTO takas_data (ticker, date, foreign_ratio, daily_change) 
                        VALUES (:t, :d, :f, :c)
                    """), {"t": ticker, "d": today, "f": ratio, "c": daily_change})
        return True
    except Exception as e:
        print(f"Error in takas update: {e}")
        return False

def get_takas_data(ticker):
    today = datetime.now(TR_TZ).strftime('%Y-%m-%d')
    try:
        with engine.connect() as conn:
            cur = conn.execute(text("SELECT foreign_ratio, daily_change FROM takas_data WHERE ticker=:t AND date=:d"), {"t": ticker, "d": today})
            row = cur.fetchone()
            if row:
                return {'foreign_ratio': row[0], 'daily_change': row[1]}
        
        # Veri yoksa bir kereye mahsus güncellemeyi dene
        update_all_takas()
        
        with engine.connect() as conn:
            cur = conn.execute(text("SELECT foreign_ratio, daily_change FROM takas_data WHERE ticker=:t AND date=:d"), {"t": ticker, "d": today})
            row = cur.fetchone()
            if row:
                return {'foreign_ratio': row[0], 'daily_change': row[1]}
                
        return {'foreign_ratio': 0.0, 'daily_change': 0.0}
    except Exception:
        return {'foreign_ratio': 0.0, 'daily_change': 0.0}
