FROM python:3.11-slim

WORKDIR /app

# Sistem baÄŸÄ±mlÄ±lÄ±klarÄ±nÄ± yÃ¼kle
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# BaÄŸÄ±mlÄ±lÄ±klarÄ± kopyala ve yÃ¼kle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

EXPOSE 8000

CMD ["bash", "start.sh"]