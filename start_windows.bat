@echo off
echo Borsa Analiz App V5 - Baslatiliyor...

:: Backend Kurulumu
IF NOT EXIST venv (
    echo Sanal ortam (venv) olusturuluyor...
    python -m venv venv
)

echo Bagimliliklar yukleniyor...
call venv\Scripts\activate
pip install -r requirements.txt

:: Frontend Kurulumu
echo Frontend paketleri kontrol ediliyor...
cd frontend
IF NOT EXIST node_modules (
    npm install
)
cd ..

echo Sistem ayaga kaldiriliyor...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:3000

:: Parallel execution in Windows
start cmd /k "call venv\Scripts\activate && python main.py"
start cmd /k "cd frontend && npm run dev"
