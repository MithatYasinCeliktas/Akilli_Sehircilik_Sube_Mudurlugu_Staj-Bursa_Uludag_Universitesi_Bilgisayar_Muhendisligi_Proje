@echo off
chcp 65001 >nul
color 0B

echo ===================================================
echo   Bursa Faaliyet Raporu - Docker Başlatıcı
echo ===================================================
echo.
echo [1/2] Eski kapsayıcılar (varsa) durduruluyor...
docker-compose down

echo.
echo [2/2] Tüm sistem sıfırdan derlenip başlatılıyor...
echo (Bu işlem ilk seferde 3-5 dakika sürebilir)
docker-compose up -d --build

echo.
echo ===================================================
echo   SİSTEM BAŞARIYLA AYAĞA KALDIRILDI!
echo   Frontend: http://localhost:4200
echo   Backend API: http://localhost:8000/docs
echo ===================================================
pause