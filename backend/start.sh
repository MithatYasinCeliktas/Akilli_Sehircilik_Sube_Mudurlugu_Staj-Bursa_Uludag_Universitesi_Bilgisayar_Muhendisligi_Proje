#!/bin/bash
echo "Veritabanı tabloları oluşturuluyor ve örnek veriler yükleniyor..."
python setup_db.py

echo "FastAPI sunucusu başlatılıyor..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000