# Multi-stage Dockerfile: python-api (FastAPI) and node-gmail (Express proxy)

# ── Stage 1: Python API ─────────────────────────────────────────────
FROM python:3.11-slim AS python-api
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Stage 2: Node.js builder (compile TypeScript) ───────────────────
FROM node:20-alpine AS node-gmail-builder
WORKDIR /app
COPY node-gmail/package*.json ./node-gmail/
RUN cd node-gmail && npm ci
COPY node-gmail/ ./node-gmail/
RUN cd node-gmail && npm run build

# ── Stage 3: Node.js production image ───────────────────────────────
FROM node:20-alpine AS node-gmail
WORKDIR /app
COPY node-gmail/package*.json ./
RUN npm ci --only=production
COPY --from=node-gmail-builder /app/dist ./dist
EXPOSE 3000
CMD ["node", "dist/gmail-proxy.js"]
