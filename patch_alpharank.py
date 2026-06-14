import re

with open("alpharank_engine.py", "r", encoding="utf-8") as f:
    code = f.read()

# We will replace the entire analyze_ticker method.
new_method = """    def analyze_ticker(self, ticker: str, market_regime: dict = None) -> dict:
        \"\"\"Tek bir hisse için top_picks_15d motorunu kullanarak analiz yapar.\"\"\"
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
        }"""

# Replace the method using regex
pattern = r'    def analyze_ticker\(self, ticker: str, market_regime: dict = None\) -> dict:.*?(?=    def run_analysis)'
code = re.sub(pattern, new_method + "\n\n", code, flags=re.DOTALL)

with open("alpharank_engine.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Patch applied to alpharank_engine.py")
