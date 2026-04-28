# ----- Stage 1 : build du frontend React -----
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund --silent

COPY frontend/ ./
RUN CI=true npm run build

# ----- Stage 2 : backend FastAPI + frontend statique -----
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /frontend/build/ ./frontend/build/

# Le module main.py utilise `from models import ...` (import direct), donc
# on lance uvicorn depuis le dossier backend pour que Python trouve le module.
WORKDIR /app/backend

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
