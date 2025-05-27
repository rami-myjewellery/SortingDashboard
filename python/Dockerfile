# Stage 1: Install dependencies
FROM python:3.11-slim AS deps
WORKDIR /tmp
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app

# Install packages from stage 1
COPY --from=deps /usr/local /usr/local

# Copy the application code
COPY . /app

EXPOSE 8080

# Run the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
