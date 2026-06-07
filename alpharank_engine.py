import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime
from database import engine
from sqlalchemy import text

class AlphaRank15D:
    def __init__(self):
        self.MAX_POOL_SIZE = 10

    def add_to_alpharank(self, username: str, ticker: str):
        """Havuz listesine yeni hisse ekler. Maksimum 10 sınırına tabidir."""
        ticker = ticker.upper()
        if not ticker.endswith(".IS"):
            ticker += ".IS"
            
        with engine.begin() as conn:
            # Güncel sayıyı kontrol et
            count_res = conn.execute(text("SELECT COUNT(*) FROM alpharank_pool WHERE username=:u"), {"u": username}).fetchone()
            count = count_res[0] if count_res else 0
            
            if count >= self.MAX_POOL_SIZE:
                return {"success": False, "message": f"Maksimum sınır olan {self.MAX_POOL_SIZE} hisseye ulaşıldı. Önce bir hisse silmelisiniz."}
            
            # Mükerrer eklemeyi veritabanındaki UNIQUE (username, ticker) kısıtlamasıyla çözüyoruz veya kontrol ediyoruz:
            existing = conn.execute(text("SELECT id FROM alpharank_pool WHERE username=:u AND ticker=:t"), {"u": username, "t": ticker}).fetchone()
            if existing:
                return {"success": False, "message": f"{ticker} zaten takip havuzunuzda bulunuyor."}
                
            conn.execute(text("""
                INSERT INTO alpharank_pool (username, ticker, added_at)
                VALUES (:u, :t, :d)
            """), {"u": username, "t": ticker, "d": datetime.now().strftime('%Y-%m-%d %H:%M')})
            
            return {"success": True, "message": f"{ticker} havuzunuza eklendi."}

    def remove_from_alpharank(self, username: str, ticker: str):
        """Havuzdan hisse siler."""
        ticker = ticker.upper()
        if not ticker.endswith(".IS"):
            ticker += ".IS"
            
        with engine.begin() as conn:
            res = conn.execute(text("DELETE FROM alpharank_pool WHERE username=:u AND ticker=:t"), {"u": username, "t": ticker})
            if res.rowcount > 0:
                return {"success": True, "message": f"{ticker} havuzunuzdan silindi."}
            else:
                return {"success": False, "message": f"{ticker} havuzda bulunamadı."}

    def get_current_pool(self, username: str) -> list:
        """Kullanıcının güncel hisse havuzunu döner."""
        with engine.connect() as conn:
            res = conn.execute(text("SELECT ticker, added_at FROM alpharank_pool WHERE username=:u ORDER BY added_at ASC"), {"u": username}).fetchall()
            return [{"ticker": row[0], "added_at": row[1]} for row in res]

    def clear_pool(self, username: str):
        """Kullanıcının havuzunu tamamen temizler."""
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM alpharank_pool WHERE username=:u"), {"u": username})
            return {"success": True, "message": "Havuz tamamen temizlendi."}

    def analyze_ticker(self, ticker: str) -> dict:
        """Tek bir hisse için teknik hesaplamaları yapar ve skor üretir."""
        df = yf.download(ticker, period="100d", progress=False)
        if df.empty or len(df) < 30:
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        close = df['Close'].squeeze()
        high = df['High'].squeeze()
        low = df['Low'].squeeze()
        volume = df['Volume'].squeeze()
        
        # İndikatörleri Hesapla
        # EMA
        ema9 = ta.ema(close, length=9)
        ema21 = ta.ema(close, length=21)
        
        # MACD (12, 26, 9)
        macd_df = ta.macd(close, fast=12, slow=26, signal=9)
        # macd_df columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        macd_line = macd_df['MACD_12_26_9']
        macd_signal = macd_df['MACDs_12_26_9']
        macd_hist = macd_df['MACDh_12_26_9']
        
        # RSI
        rsi = ta.rsi(close, length=14)
        
        # Bollinger Bands (20, 2)
        bbands = ta.bbands(close, length=20, std=2)
        bb_lower = bbands[[c for c in bbands.columns if c.startswith('BBL')][0]]
        bb_upper = bbands[[c for c in bbands.columns if c.startswith('BBU')][0]]
        
        # Son veriler
        current_price = close.iloc[-1]
        prev_price = close.iloc[-2]
        c_ema9 = ema9.iloc[-1]
        c_ema21 = ema21.iloc[-1]
        c_macd = macd_line.iloc[-1]
        c_signal = macd_signal.iloc[-1]
        c_hist = macd_hist.iloc[-1]
        p_hist = macd_hist.iloc[-2]
        c_rsi = rsi.iloc[-1]
        
        # Skorlama ve Gerekçeler
        score = 0
        evidences = []
        
        # 1. Trend Gücü (EMA Kesişimi) - Maksimum %30
        ema_score = 0
        if current_price > c_ema9 > c_ema21:
            ema_score += 20
            evidences.append("Güçlü Trend: Fiyat kısa ve orta vadeli ortalamaların (EMA9 ve EMA21) üzerinde.")
        elif current_price > c_ema9:
            ema_score += 10
            evidences.append("Pozitif Trend: Fiyat kısa vadeli ortalamanın (EMA9) üzerinde.")
            
        # Son 5 gün içinde Golden Cross (EMA9 > EMA21 kesişimi) kontrolü
        golden_cross = False
        for i in range(-5, 0):
            if ema9.iloc[i-1] <= ema21.iloc[i-1] and ema9.iloc[i] > ema21.iloc[i]:
                golden_cross = True
                break
        if golden_cross:
            ema_score += 10
            evidences.append("Alım Sinyali: Son 5 gün içinde EMA9, EMA21'i yukarı kesti (Golden Cross).")
        
        score += min(ema_score, 30)
        
        # 2. Momentum (MACD) - Maksimum %30
        macd_score = 0
        if c_macd > c_signal:
            macd_score += 15
            evidences.append("Momentum Pozitif: MACD çizgisi sinyal çizgisinin üzerinde (Alım bölgesinde).")
        if c_hist > 0 and c_hist > p_hist:
            macd_score += 15
            evidences.append("Artan Momentum: MACD histogramı sıfırın üzerinde ve büyümeye devam ediyor.")
        elif c_hist < 0 and c_hist > p_hist:
            macd_score += 10
            evidences.append("Toparlanma Sinyali: MACD histogramı negatif bölgede olsa da daralma (pozitife yaklaşma) gösteriyor.")
            
        score += min(macd_score, 30)
        
        # 3. Dip/Dönüş Gücü (RSI) - Maksimum %25
        rsi_score = 0
        if c_rsi < 35:
            rsi_score += 5
            evidences.append(f"Aşırı Satım Bölgesi: RSI ({c_rsi:.1f}) düşük seviyede, tepki alımı gelebilir.")
        elif 35 <= c_rsi <= 65:
            rsi_score += 15
            evidences.append(f"Sağlıklı Bölge: RSI ({c_rsi:.1f}) istikrarlı yükseliş bölgesinde.")
        elif c_rsi > 65:
            rsi_score += 5
            evidences.append(f"Aşırı Alım Yaklaşıyor: RSI ({c_rsi:.1f}) yüksek seviyede, dikkatli olunmalı.")
            
        # Pozitif Uyumsuzluk Kontrolü (Son 15 gün)
        min_price_15 = close.iloc[-15:].min()
        min_price_idx = close.iloc[-15:].idxmin()
        prev_min_price = close.iloc[-30:-15].min()
        
        min_rsi_15 = rsi.loc[min_price_idx]
        prev_min_rsi = rsi.iloc[-30:-15].min()
        
        if min_price_15 < prev_min_price and min_rsi_15 > prev_min_rsi:
            rsi_score += 10
            evidences.append("Güçlü Dönüş: Son 15 günde fiyat düşerken RSI yükseliyor (Pozitif Uyumsuzluk yakalandı).")
            
        score += min(rsi_score, 25)
        
        # 4. Sıkışma/Hacim (Bollinger & Volatilite) - Maksimum %15
        bb_score = 0
        bb_width = (bb_upper.iloc[-1] - bb_lower.iloc[-1]) / current_price
        avg_bb_width = ((bb_upper.iloc[-20:] - bb_lower.iloc[-20:]) / close.iloc[-20:]).mean()
        
        if bb_width < avg_bb_width * 0.8:
            bb_score += 8
            evidences.append("Bant Daralması (Squeeze): Bollinger bantlarında sert bir fiyat hareketine hazırlık (sıkışma) gözlemleniyor.")
            
        # Hacim artışı
        avg_vol_5 = volume.iloc[-5:].mean()
        avg_vol_20 = volume.iloc[-20:].mean()
        if avg_vol_5 > avg_vol_20 * 1.2:
            bb_score += 7
            evidences.append("Hacim Onayı: Son 5 günlük ortalama hacim, 20 günlük ortalamaya göre ciddi bir artış gösteriyor.")
            
        score += min(bb_score, 15)
        
        return {
            "ticker": ticker.replace(".IS", ""),
            "score": round(score, 1),
            "price": round(current_price, 2),
            "evidences": evidences
        }

    def run_analysis(self, username: str) -> list:
        """Kullanıcının havuzundaki tüm hisseleri analiz eder ve skora göre sıralar."""
        pool = self.get_current_pool(username)
        if not pool:
            return []
            
        results = []
        for item in pool:
            analysis = self.analyze_ticker(item["ticker"])
            if analysis:
                results.append(analysis)
                
        # Skora göre en yüksekten en düşüğe sırala
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Sıra numarası (Rank) ekle
        for i, res in enumerate(results):
            res["rank"] = i + 1
            
        return results

# Simülasyon / Test (Doğrudan çalıştırıldığında)
if __name__ == "__main__":
    engine_obj = AlphaRank15D()
    user = "test_user"
    print("--- AlphaRank 15D Simülasyonu ---")
    engine_obj.clear_pool(user)
    
    # 3 adet hisse ekleyelim
    print(engine_obj.add_to_alpharank(user, "THYAO"))
    print(engine_obj.add_to_alpharank(user, "KCHOL"))
    print(engine_obj.add_to_alpharank(user, "GARAN"))
    
    print("\nGüncel Havuz:", engine_obj.get_current_pool(user))
    
    print("\nAnaliz Başlıyor...")
    results = engine_obj.run_analysis(user)
    
    for r in results:
        print(f"\nSıra: {r['rank']} | Hisse: {r['ticker']} | Fiyat: {r['price']} | Yükseliş Olasılığı: %{r['score']}")
        for ev in r['evidences']:
            print(f"  - {ev}")
