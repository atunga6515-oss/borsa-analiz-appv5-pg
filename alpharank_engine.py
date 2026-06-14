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
        """Tek bir hisse için top_picks_15d motorunu kullanarak analiz yapar."""
        from top_picks_15d import deep_analyze_stock
        
        # Orijinal motoru kullanarak tam analizi çek
        res = deep_analyze_stock(ticker, market_regime)
        if res.get("error"):
            return None
            
        v6_score = res.get("v6_score", 50)
        current_price = res.get("price", 0)
        details = res.get("details", {})
        
        evidences = []
        
        # 1. Kısa Vade Sinyalleri
        sig = details.get("signals", {})
        short_score = sig.get("short_term", {}).get("score", 50)
        if short_score >= 60:
            evidences.append(f"🚀 Güçlü Kısa Vade Motoru: 15 Günlük indikatörlerin %{short_score:.1f}'si AL sinyali veriyor.")
        elif short_score < 40:
            evidences.append(f"⚠️ Zayıf İvme: Kısa vade indikatörlerin sadece %{short_score:.1f}'si AL veriyor.")
        else:
            evidences.append(f"⚖️ Nötr İvme: Kısa vade indikatörler %{short_score:.1f} ile karar aşamasında.")
            
        # 2. Hacim ve Momentum
        vol_trend = details.get("volume_trend", "")
        if vol_trend == "Hacim Artışıyla Yükseliş":
            evidences.append("🔥 Hacim Onayı: Son günlerde belirgin bir hacim girişi var.")
            
        # 3. Formasyonlar
        patterns = details.get("patterns", [])
        if patterns:
            evidences.append(f"📈 Mum Formasyonu: {', '.join(patterns)} tespit edildi.")
            
        # 4. Dönüş (Reversal)
        is_bottom = details.get("is_bottom_reversal", False)
        if is_bottom:
            evidences.append("🔄 Dipten Dönüş Sinyali: Hisse aşırı satım bölgesinden tepki veriyor.")
            
        # 5. Temel Durum (15 Günlükte Düşük Ağırlıkta Olsa da Belirtmek İyi)
        tem_durum = res.get("tem_durum", "Normal")
        if tem_durum == "Kelepir":
            evidences.append("💎 Temel Analiz: Finansal olarak ucuz / kelepir bölgesinde.")
            
        # 6. Güven Skoru (Walk Forward Başarısı)
        confidence = res.get("confidence", 50)
        if confidence >= 80:
            evidences.append(f"🛡️ Yüksek Tarihsel Güvenilirlik: Geçmiş testlerde başarı oranı %{confidence:.1f}.")

        # V6 Skorunu AlphaRank'in Yükseliş Olasılığı (prob_15d) ve genel Skoru olarak atıyoruz
        return {
            "ticker": ticker.replace(".IS", ""),
            "score": v6_score,
            "prob_15d": v6_score,
            "price": current_price,
            "evidences": evidences if evidences else ["Kısa vadeli osilatörler stabil ilerliyor."]
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
