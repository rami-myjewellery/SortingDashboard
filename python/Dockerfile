# ── Stage 1: build Python deps ──────────────────────────────────────
FROM python:3.11-slim AS python-deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ── Stage 2: runtime  (Chrome + uvicorn) ────────────────────────────
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# Chrome & friends (headless)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg \
        fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
        libdrm-dev libgbm-dev libgtk-3-0 libnss3 libx11-xcb1 libxcomposite1 \
        libxdamage1 libxext6 libxfixes3 libxrandr2 libxss1 xdg-utils \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Python libs from first stage
COPY --from=python-deps /usr/local /usr/local
# Your FastAPI code
COPY . /app                 
WORKDIR /app

CMD ["uvicorn", "sorting:app", "--host", "0.0.0.0", "--port", "8080"]
