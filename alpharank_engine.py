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

    def _calibrate_15d_probability(self, df: pd.DataFrame, technical_score: float) -> float:
        if len(df) < 40: return round(technical_score * 0.6, 1)
        closes = df["Close"].values
        rsi = df["RSI_14"].values if "RSI_14" in df.columns else pd.Series([50]*len(df)).values
        hits = []
        for i in range(25, len(closes) - 15):
            fwd = (closes[i + 15] - closes[i]) / closes[i] * 100
            ema20 = df["EMA_20"].iloc[i] if "EMA_20" in df.columns else closes[i]
            dist = (closes[i] - ema20) / ema20 * 100 if ema20 else 0
            pseudo = 50 + (rsi[i] - 50) * 0.4 + dist * 0.3
            pseudo = max(0, min(100, pseudo))
            if abs(pseudo - technical_score) <= 15:
                hits.append(fwd > 2.0)
        if len(hits) >= 5:
            return round(min(95, max(5, sum(hits) / len(hits) * 100)), 1)
        return round(technical_score * 0.6, 1)

    def analyze_ticker(self, ticker: str, market_regime: dict = None) -> dict:
        """Tek bir hisse için teknik hesaplamaları yapar ve skor üretir."""
        from data_loader import fetch_data
        from indicators import calculate_indicators
        from core.walk_forward import walk_forward_vote
        
        df = fetch_data(ticker, interval="1d", period="1y")
        if df.empty or len(df) < 30:
            return None
            
        df = calculate_indicators(df)
        
        close = df['Close'].squeeze()
        volume = df['Volume'].squeeze()
        
        # Son veriler
        from data_loader import get_batch_live_prices
        ssot = get_batch_live_prices([ticker]).get(ticker, {})
        current_price = ssot.get("price", close.iloc[-1])
        
        c_ema9 = df['EMA_9'].iloc[-1] if 'EMA_9' in df.columns else close.iloc[-1]
        c_ema21 = df['EMA_20'].iloc[-1] if 'EMA_20' in df.columns else close.iloc[-1]
        c_macd = df['MACD_12_26_9'].iloc[-1] if 'MACD_12_26_9' in df.columns else 0
        c_signal = df['MACDs_12_26_9'].iloc[-1] if 'MACDs_12_26_9' in df.columns else 0
        c_hist = df['MACDh_12_26_9'].iloc[-1] if 'MACDh_12_26_9' in df.columns else 0
        p_hist = df['MACDh_12_26_9'].iloc[-2] if 'MACDh_12_26_9' in df.columns else 0
        c_rsi = df['RSI_14'].iloc[-1] if 'RSI_14' in df.columns else 50
        
        # Skorlama ve Gerekçeler
        score = 0
        evidences = []
        
        # 1. Trend Gücü
        ema_score = 0
        if current_price > c_ema9 > c_ema21:
            ema_score += 20
            evidences.append("Güçlü Trend: Fiyat kısa ve orta vadeli ortalamaların üzerinde.")
        elif current_price > c_ema9:
            ema_score += 10
            evidences.append("Pozitif Trend: Fiyat kısa vadeli ortalamanın üzerinde.")
        score += min(ema_score, 30)
        
        # 2. Momentum
        macd_score = 0
        if c_macd > c_signal:
            macd_score += 15
            evidences.append("Momentum Pozitif: MACD sinyal çizgisinin üzerinde.")
        if c_hist > 0 and c_hist > p_hist:
            macd_score += 15
            evidences.append("Artan Momentum: MACD histogramı büyümeye devam ediyor.")
        score += min(macd_score, 30)
        
        # 3. RSI
        rsi_score = 0
        if c_rsi < 35:
            rsi_score += 10
            evidences.append(f"Aşırı Satım: RSI ({c_rsi:.1f}) düşük, tepki gelebilir.")
        elif 35 <= c_rsi <= 65:
            rsi_score += 15
            evidences.append(f"Sağlıklı Bölge: RSI ({c_rsi:.1f}) istikrarlı yükseliş bölgesinde.")
        score += min(rsi_score, 25)
        
        # Walk Forward
        votes = walk_forward_vote(df)
        if votes["buy_vote"] > 60:
            score += 15
            evidences.append(f"Geçmiş Doğrulama: Benzer sinyallerde başarı oranı %{votes['buy_vote']:.1f}")
        elif votes["sell_vote"] > 60:
            score -= 12
            evidences.append(f"Geçmiş Doğrulama (Negatif): Benzer kırılımlar genelde başarısız oldu.")
            
        score = min(100, max(0, score))
        
        # XU100 Regime Penalty
        if market_regime and market_regime.get("is_bear", False):
            score *= 0.92
            
        prob_15d = self._calibrate_15d_probability(df, score)
        
        return {
            "ticker": ticker.replace(".IS", ""),
            "score": round(score, 1),
            "prob_15d": prob_15d,
            "price": round(current_price, 2),
            "evidences": evidences
        }

    def run_analysis(self, username: str) -> list:
        """Kullanıcının havuzundaki tüm hisseleri analiz eder ve skora göre sıralar."""
        pool = self.get_current_pool(username)
        if not pool:
            return []
            
        from indicators import get_market_regime
        from data_loader import fetch_data
        xu100_df = fetch_data("XU100", "1d", "1y")
        market_regime = get_market_regime(xu100_df)
            
        results = []
        for item in pool:
            analysis = self.analyze_ticker(item["ticker"], market_regime)
            if analysis:
                results.append(analysis)
                
        # Skora (prob_15d) göre en yüksekten en düşüğe sırala
        results.sort(key=lambda x: x.get("prob_15d", 0), reverse=True)
        
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
