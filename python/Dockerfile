# ── Stage 1 : install deps ──────────────────────────────────────────
FROM python:3.11-slim AS deps
WORKDIR /tmp
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ── Stage 2 : runtime image ────────────────────────────────────────
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app

# pull site-packages from stage-1
COPY --from=deps /usr/local /usr/local

# copy ONLY your FastAPI package
COPY . /app 

# start the server  (sorting.py contains `app = FastAPI()`)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
