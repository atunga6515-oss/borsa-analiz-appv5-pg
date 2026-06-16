import requests
import pandas as pd
from io import StringIO
import time

_TAKAS_CACHE = {}
_LAST_FETCH_TIME = 0

def fetch_all_takas_from_isyatirim():
    global _TAKAS_CACHE, _LAST_FETCH_TIME
    
    now = time.time()
    # Cache for 1 hour to avoid spamming the website
    if _TAKAS_CACHE and (now - _LAST_FETCH_TIME) < 3600:
        return
        
    try:
        url = 'https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/Temel-Degerler-Ve-Oranlar.aspx'
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        
        tables = pd.read_html(StringIO(res.text), decimal=',', thousands='.')
        
        df = None
        for table in tables:
            if 'Değişim (Baz Puan)' in table.columns:
                df = table
                break
                
        if df is not None:
            new_cache = {}
            for idx, row in df.iterrows():
                kod = str(row['Kod']).strip()
                try:
                    # Index 2 is the most recent date's foreign ratio
                    current_ratio = float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0.0
                except:
                    current_ratio = 0.0
                    
                try:
                    # 'Etki* (%)' is the percentage change between the two dates in the default table (usually daily)
                    change = float(row['Etki* (%)']) if pd.notna(row['Etki* (%)']) else 0.0
                except:
                    change = 0.0
                    
                new_cache[kod] = {
                    'foreign_ratio': current_ratio,
                    'daily_change': change 
                }
            
            _TAKAS_CACHE = new_cache
            _LAST_FETCH_TIME = now
    except Exception as e:
        print(f"Is Yatirim takas verisi cekilirken hata: {e}")

def get_takas_data(ticker):
    fetch_all_takas_from_isyatirim()
    if ticker in _TAKAS_CACHE:
        return _TAKAS_CACHE[ticker]
    return {'foreign_ratio': 0.0, 'daily_change': 0.0}

def update_all_takas():
    # Keep for compatibility
    return True
