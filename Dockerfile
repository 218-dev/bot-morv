# لاتعبث بالملف دون فهم ، قد تحدث مشاكل انت في غنى عنها 
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    make \
    g++ \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# إعادة بناء Python مع SQLite
RUN pip install --no-cache-dir pysqlite3-binary

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python3 -c 'import sqlite3; print(\"✓ SQLite OK\")' && python3 bot.py"]
