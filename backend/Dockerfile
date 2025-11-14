FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# psycopg2 및 대기용 netcat 설치
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends build-essential libpq-dev netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ARG CACHE_BUSTER=1
COPY . .

RUN mkdir -p /app/staticfiles /app/media

EXPOSE 8000

RUN chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"]
