# ── 1) Builder ──────────────────────────────────────────────
FROM node:20-bookworm AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci            # deterministic install

COPY . .
RUN npm run build    

# ── Runtime ─────────────────────────────────────────────────────────
FROM node:20-slim
WORKDIR /app
RUN npm i -g serve
COPY --from=builder /app/dist .
ENV NODE_ENV=production PORT=8080
EXPOSE 8080
CMD ["serve", "-s", ".", "-l", "8080"]
