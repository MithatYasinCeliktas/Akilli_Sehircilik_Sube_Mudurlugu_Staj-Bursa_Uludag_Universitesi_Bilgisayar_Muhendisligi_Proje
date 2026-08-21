@echo off
color 0B

echo ===================================================
echo   Bursa Faaliyet Raporu - Docker Baslatici
echo ===================================================
echo.
echo [1/2] Eski kapsayicilar (varsa) durduruluyor...
docker-compose down

echo.
echo [2/2] Tum sistem sifirdan derlenip baslatiliyor...
echo (Bu islem ilk seferde 3-5 dakika surebilir)
docker-compose up -d --build

echo.
echo ===================================================
echo   SISTEM BASARIYLA AYAGA KALDIRILDI!
echo   Frontend: http://192.168.1.152:4200
echo   Backend API: http://192.168.1.152:8000/docs
echo ===================================================
pause