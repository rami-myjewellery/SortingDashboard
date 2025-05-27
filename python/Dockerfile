# ── Stage 1 : install deps ──────────────────────────────────────────
FROM python:3.11-slim AS deps
WORKDIR /tmp
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Stage-2  runtime image
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app

# 1️⃣ copy the whole ‘python’ folder from your repo
COPY python/ /app

# 2️⃣ let Python find /app
ENV PYTHONPATH=/app

# 3️⃣ point uvicorn to the correct module path
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
