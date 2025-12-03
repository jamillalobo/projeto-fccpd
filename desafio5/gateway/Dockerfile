FROM python:3.11-slim

LABEL maintainer="Desafio 5 - API Gateway"
LABEL description="API Gateway que centraliza acesso aos microsserviços"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]

