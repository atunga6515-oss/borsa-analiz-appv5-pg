#!/bin/bash
echo "Borsa Analiz App V5 - Başlatılıyor..."

# Backend Kurulumu
if [ ! -d "venv" ]; then
    echo "Sanal ortam (venv) oluşturuluyor..."
    python3 -m venv venv
fi

echo "Bağımlılıklar yükleniyor..."
source venv/bin/activate
pip install -r requirements.txt

# Frontend Kurulumu
echo "Frontend paketleri kontrol ediliyor..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# Başlatma
echo "Sistem ayağa kaldırılıyor..."
echo "Backend: http://127.0.0.1:8000"
echo "Frontend: http://localhost:3000"

# Backend'i arka planda çalıştır
python main.py &
BACKEND_PID=$!

# Frontend'i çalıştır
cd frontend
npm run dev &
FRONTEND_PID=$!

# İşlemleri yakalayıp düzgünce kapatma
trap "echo 'Kapatılıyor...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM EXIT
wait
