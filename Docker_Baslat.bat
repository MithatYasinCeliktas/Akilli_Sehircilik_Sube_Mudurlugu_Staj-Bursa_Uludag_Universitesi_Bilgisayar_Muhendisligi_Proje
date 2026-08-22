@echo off
color 0B

for /f "delims=" %%I in ('powershell -command "(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias Wi-Fi, Ethernet -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress"') do set "IP=%%I"
if "%IP%"=="" set "IP=localhost"

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
echo   Frontend: http://%IP%:4200
echo   Backend API: http://%IP%:8000/docs
echo ===================================================
pause