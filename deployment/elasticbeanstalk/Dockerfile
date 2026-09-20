FROM node:22-alpine AS frontend-build

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/index.html frontend/tsconfig.json frontend/vite.config.mjs ./
COPY frontend/src ./src

# Relative "/api" paths only - no VITE_API_URL is set, so the build never
# embeds a backend URL of any kind, localhost included. The result is
# served by the same FastAPI process below, so requests stay same-origin.
RUN npm run build

FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/alembic.ini ./alembic.ini
COPY backend/migrations ./migrations
COPY pricing /pricing
COPY start.sh ./start.sh
COPY --from=frontend-build /build/dist ./static

EXPOSE 8000

CMD ["sh", "./start.sh"]
