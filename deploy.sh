#!/bin/bash
# ============================================================
# Borsa Analiz App — Otomatik Deploy Scripti
# Kullanım: ./deploy.sh
# ============================================================

set -e  # Herhangi bir hata olursa dur

# Scriptin çalıştığı dizini otomatik olarak bulur (Absolute path ifşasını önler)
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$APP_DIR/frontend"

echo ""
echo "=========================================="
echo "  🚀 Borsa Analiz Deploy Başlıyor..."
echo "=========================================="
echo ""

# 1. Uygulama dizinine geç
cd "$APP_DIR"

# 2. Yerel değişiklikleri temizle (npm install kaynaklı package.json / lock çakışmasını önler)
echo "📦 Yerel değişiklikler sıfırlanıyor..."
git restore "$FRONTEND_DIR/package-lock.json" 2>/dev/null || true
git restore "$FRONTEND_DIR/package.json" 2>/dev/null || true

# 3. GitHub'dan güncel kodu çek
echo "⬇️  GitHub'dan güncellemeler çekiliyor..."
git pull origin main

# 4. Frontend bağımlılıklarını güncelle
echo "📚 npm bağımlılıkları güncelleniyor..."
cd "$FRONTEND_DIR"
npm install

# 5. Güvenlik kontrolü
echo ""
echo "🔒 Güvenlik denetimi:"
npm audit 2>&1 | tail -3
echo ""

# 6. Production build
echo "🔨 Frontend derleniyor..."
npm run build

# 7. Servisleri yeniden başlat
echo ""
echo "♻️  Servisler yeniden başlatılıyor..."
pm2 restart borsa-backend
pm2 restart borsa-frontend

# 8. Durum özeti
echo ""
echo "✅ Deploy tamamlandı!"
echo ""
pm2 list
