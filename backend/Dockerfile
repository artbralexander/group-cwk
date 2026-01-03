FROM node:20-bookworm AS frontend-builder

WORKDIR /workspace
COPY . .
RUN if [ -f frontend/package.json ]; then \
      cd frontend && npm install --no-audit --no-fund && npm run build; \
    else \
      mkdir -p frontend/dist; \
    fi

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    DATABASE_URL=sqlite:///./dev.db \
    FRONTEND_DIST=/app/frontend/dist \
    REPHRASER_URL=http://127.0.0.1:8001

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r backend/requirements.txt

# Rephraser deps
COPY rephraser/requirements.txt rephraser/requirements.txt
RUN pip install -r rephraser/requirements.txt

COPY backend /app/backend
COPY rephraser /app/rephraser
COPY backend/supervisord.conf /app/supervisord.conf
COPY --from=frontend-builder /workspace/frontend/dist /app/frontend/dist

EXPOSE ${PORT}

CMD ["supervisord", "-c", "/app/supervisord.conf"]