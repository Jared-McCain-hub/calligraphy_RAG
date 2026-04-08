FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1

WORKDIR /app/backend

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

EXPOSE 8000

CMD ["sh", "-c", "python scripts/bootstrap_mysql.py --with-reference-data --with-rag-knowledge && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
