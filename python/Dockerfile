# ── Stage 1: build Python deps ──────────────────────────────────────
FROM python:3.11-slim-bookworm AS python-deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime (uvicorn + Datadog) ────────────────────────────
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# OpenCV runtime deps that the app requires
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Datadog serverless shim + tracer layer
COPY --from=datadog/serverless-init:1 /datadog-init /datadog-init
RUN chmod +x /datadog-init
RUN pip install --no-cache-dir --target /dd_tracer/python ddtrace

# Bring in Python deps from the builder
COPY --from=python-deps /usr/local /usr/local

WORKDIR /app
COPY . /app
ENV PYTHONPATH=/app:/dd_tracer/python

CMD ["/datadog-init", "/dd_tracer/python/bin/ddtrace-run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
