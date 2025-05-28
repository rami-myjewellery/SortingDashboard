# ── Stage 1 : install deps ──────────────────────────────────────────
FROM python:3.11-slim AS deps
WORKDIR /tmp
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ── Stage 2 : runtime image ────────────────────────────────────────
# ── Stage 2  (runtime) ───────────────────────────────────────────
FROM python:3.11-slim

# ➜ install OpenCV’s runtime deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app

COPY --from=deps /usr/local /usr/local
COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
