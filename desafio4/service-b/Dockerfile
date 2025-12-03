FROM python:3.11-slim

LABEL maintainer="Desafio 4 - Service B"
LABEL description="Microsserviço que consome Service A e exibe informações combinadas"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5002

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]


