# Borsa Analiz App V5 🚀

Bu proje, Borsa İstanbul (BIST) hisse senetleri için gelişmiş teknik ve temel analizler yapan, yatırımcılara yapay zeka destekli stratejik seçkiler sunan modern bir web uygulamasıdır.

Eski Streamlit (V4) yapısı terkedilmiş olup, sistem **FastAPI (Backend)** ve **Next.js (Frontend)** mimarisiyle baştan aşağı yenilenerek kurumsal bir yapıya kavuşturulmuştur.

## 🌟 Yeni V5 Özellikleri (PostgreSQL Destekli)
- **Modüler Vade Ayrışımı:** İndikatörler 0-15 Gün (Kısa), 1-3 Ay (Orta) ve 3-12 Ay (Uzun) vade potansiyellerine göre 3 farklı motor halinde yeniden tasarlandı.
- **Kapsamlı Analiz Modülü:** 101 farklı teknik indikatör (RSI, MACD, Bollinger, Ichimoku, SuperTrend vb.) ile hisse analizi ve vadelerine göre ayrıştırılmış "3'lü Gauge Progress" strateji görünümü.
- **Hibrit Al-Sat Screener:** BIST30, BIST100 veya TÜM hisseleri aynı anda hem temel hem de teknik (Tüm vadeler harmanlanmış) kriterlere göre tarayan, asenkron tarama motoru.
- **Seçki 15G (Kısa Vade):** BIST Tüm hisseleri üzerinden yalnızca 15 günlük patlama potansiyeli arayan, kısa vade indikatör ağırlıklı yepyeni stratejik tarama motoru.
- **Seçki O-U Vade (Orta-Uzun):** Sadece güvenilir orta ve uzun vadeli indikatörlerden yola çıkarak hisseleri analiz eden ana tarama modülü.
- **AlphaRank 15D:** Takip listenizdeki hisseleri Gelişmiş AI modeli ve Kısa Vadeli Motor bonus puanıyla sıralayan sıralama sistemi.
- **Risk Yönetimi ve Graham Değeri:** BIST'in enflasyonist yapısına uygun Graham içsel değeri hesaplamaları ve ATR bazlı dinamik Kar Al/Zarar Kes seviyeleri.
- **Telegram Entegrasyonu:** Bulduğunuz fırsatları veya kendi seçtiğiniz hisseleri tek tıkla (`📤 Telegram'a Gönder`) kişisel botunuza iletme imkanı.
- **Canlı Yama Teknolojisi:** Yfinance gecikmelerine karşı, piyasa saatleri içinde anlık hisse fiyatlarını (live quote) doğrudan grafiğe yamalayan yenilikçi sistem.
- **PostgreSQL Veritabanı:** Tarama geçmişleri, portföy hareketleri ve alarm kayıtları güvenli bir şekilde `postgres` üzerinde tutulur.

---

## 🛠 Kurulum ve Çalıştırma (Çok Kolay!)

Sistemi ayağa kaldırmak için bilgisayarınızın işletim sistemine uygun olan betiği çalıştırmanız yeterlidir. Betikler gerekli olan Python (Sanal Ortam) ve Node.js kurulumlarını otomatik olarak gerçekleştirir.

### 🍎 Mac ve 🐧 Linux İçin
Terminali açıp proje dizinine girin ve aşağıdaki komutu çalıştırın:
```bash
chmod +x start_linux_mac.sh
./start_linux_mac.sh
```

### 🪟 Windows İçin
Proje klasörünün içerisine girip `start_windows.bat` dosyasına **çift tıklayın**. (Komut istemcileri otomatik olarak arka planda sunucuları ayağa kaldıracaktır).

---

## 🐳 Docker ile Kurulum (Gelişmiş Kullanıcılar)
Uygulamayı konteyner (container) yapısı içerisinde tamamen izole çalıştırmak isterseniz:
```bash
docker-compose up --build
```
Bu komut; `Backend` servisini `8000` portundan, `Frontend` arayüzünü ise `3000` portundan dışarıya açacaktır.

---

## 🔑 Telegram Ayarları
Projenin "Telegram'a Gönder" özelliklerinin çalışması için proje kök dizininde `.env` isimli bir dosya oluşturup (veya `.env.example` dosyasının adını değiştirip) içerisine anahtarlarınızı girmelisiniz:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCDefghIJKLmnopQRSTuvwxYZ
TELEGRAM_CHAT_ID=-1001234567890
```

## 🌐 Adresler
Sistem ayağa kalktığında aşağıdaki adreslerden giriş yapabilirsiniz:
- **Arayüz (Frontend):** `http://localhost:3000`
- **Backend API Docs:** `http://localhost:8000/docs`

---
*Yatırım tavsiyesi değildir, sadece algoritmik bir pusuladır.*
