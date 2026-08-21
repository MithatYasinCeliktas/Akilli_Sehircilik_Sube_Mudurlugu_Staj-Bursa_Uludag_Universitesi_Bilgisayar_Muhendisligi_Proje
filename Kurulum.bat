@echo off
color 0A

echo ===================================================
echo   Bursa Faaliyet Raporu - Ilk Kurulum Sihirbazi
echo ===================================================
echo.

:: Python Kontrolu
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [HATA] Python yuklu degil veya PATH'e eklenmemis!
    echo Lutfen python.org adresinden Python 3.10 veya uzeri bir surum yukleyin.
    pause
    exit /b
)

:: Node.js Kontrolu
node --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [HATA] Node.js yuklu degil veya PATH'e eklenmemis!
    echo Lutfen nodejs.org adresinden Node.js yukleyin.
    pause
    exit /b
)

echo [1/4] Backend (Python) Sanal Ortam Kuruluyor...
cd backend
IF NOT EXIST "venv" (
    python -m venv venv
)
call venv\Scripts\activate
echo [2/4] Backend Gerekli Kutuphaneler Yukleniyor (Bu islem biraz surebilir)...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt >nul

echo [3/4] Gerekli Ayar Dosyalari (.env) Hazirlaniyor...
IF NOT EXIST ".env" (
    copy .env.example .env >nul
)
cd ..

echo [4/4] Frontend (Angular) Bagimliliklari Yukleniyor (Bu islem biraz surebilir)...
cd frontend
call npm install
cd ..

echo.
echo ===================================================
echo   KURULUM TAMAMLANDI!
echo   Artik "Baslat.bat" dosyasina tiklayarak
echo   uygulamayi sorunsuzca calistirabilirsiniz.
echo ===================================================
pause