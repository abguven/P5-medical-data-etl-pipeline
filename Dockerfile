FROM python:3.11-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


# LIBRARY INSTALLATION LAYER
COPY requirements.txt .
# Mettre à jour pip et installer les dépendances
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ETL PREPARATION LAYER
RUN mkdir -p /app/data /app/scripts /app/config

COPY ./scripts/etl.py /app/scripts/

COPY ./config/ /app/config/

CMD ["python", "-m", "scripts.etl"]