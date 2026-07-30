FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV HF_HOME=/root/.cache/huggingface

WORKDIR /app/backend

# Install build deps + curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Model will be loaded from mounted local cache at runtime
COPY backend /app/backend

EXPOSE 8000

CMD ["sh", "-c", "python scripts/bootstrap_mysql.py --with-reference-data --with-rag-knowledge && python scripts/seed_qdrant.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
