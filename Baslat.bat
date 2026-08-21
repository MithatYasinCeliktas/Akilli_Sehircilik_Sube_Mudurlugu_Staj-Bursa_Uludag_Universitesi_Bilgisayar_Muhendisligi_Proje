@echo off
title Bursa Faaliyet Raporu Uygulamasi

echo ===================================================
echo Bursa Faaliyet Raporu Uygulamasi Baslatiliyor...
echo ===================================================
echo.

echo [1/3] Backend (FastAPI) baslatiliyor...
start "Backend" cmd /k "cd backend && call venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [2/3] Frontend (Angular) baslatiliyor...
start "Frontend" cmd /k "cd frontend && npm start -- --host 0.0.0.0"

echo [3/3] Tarayicinin acilmasi icin bilesenlerin hazir olmasi bekleniyor (10 saniye)...
timeout /t 10 /nobreak >nul

echo Tarayici aciliyor: http://localhost:4200
start http://localhost:4200

echo.
echo Islem tamamlandi. 
echo NOT: Arka planda acilan iki siyah konsol penceresini (Backend ve Frontend) 
echo uygulamayi kullandiginiz surece KAPATMAYINIZ.
echo.
pause