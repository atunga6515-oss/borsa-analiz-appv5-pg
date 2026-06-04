# Borsa Analiz App V5 🚀

Bu proje, Borsa İstanbul (BIST) hisse senetleri için gelişmiş teknik ve temel analizler yapan, yatırımcılara yapay zeka destekli stratejik seçkiler sunan modern bir web uygulamasıdır.

Eski Streamlit (V4) yapısı terkedilmiş olup, sistem **FastAPI (Backend)** ve **Next.js (Frontend)** mimarisiyle baştan aşağı yenilenerek kurumsal bir yapıya kavuşturulmuştur.

## 🌟 Yeni V5 Özellikleri
- **Kapsamlı Analiz Modülü:** 100+ teknik indikatör (RSI, MACD, Bollinger, Ichimoku, SuperTrend vb.) ile hisse analizi.
- **Yapay Zeka Destekli Özet:** Analiz sonuçlarını sizin için yorumlayan AI entegrasyonu.
- **Risk Yönetimi:** ATR bazlı dinamik Kar Al ve Zarar Kes (Stop Loss) seviyeleri.
- **Stratejik Seçki (Top Picks):** Haftalık bazda algoritmik olarak filtrelenmiş ve güven skoruyla sıralanmış en iyi hisseler listesi.
- **Asenkron Al-Sat Screener:** BIST30, BIST100 veya TÜM hisseleri aynı anda tarayan, arka planda (background tasks) çalışan ve sayfanızı kilitlemeyen gelişmiş tarama motoru.
- **Telegram Entegrasyonu:** Bulduğunuz fırsatları veya kendi seçtiğiniz hisseleri tek tıkla (`📤 Telegram'a Gönder`) kişisel botunuza iletme imkanı.
- **Canlı Yama Teknolojisi:** Yfinance gecikmelerine karşı, piyasa saatleri içinde anlık hisse fiyatlarını (live quote) doğrudan grafiğe yamalayan yenilikçi sistem.

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
