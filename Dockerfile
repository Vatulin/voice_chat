FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    portaudio19-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY server.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 12345

CMD ["python", "server.py"]