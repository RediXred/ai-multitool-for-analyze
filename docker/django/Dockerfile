FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    net-tools \
    gcc \
    libpq-dev \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 8000