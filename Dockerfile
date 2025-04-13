FROM python:3.10-slim

ARG ENV=prod
ENV ENV=$ENV

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-all-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 5000

RUN pip install watchdog
CMD ["watchmedo", "auto-restart", "--directory=./", "--pattern=*.py", "--recursive", "--", "python", "main.py"]
