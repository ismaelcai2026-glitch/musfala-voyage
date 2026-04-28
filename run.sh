#!/usr/bin/env bash
# MUSFALA Voyage - Lancement local
# Usage: ./run.sh        (lance backend, suppose le frontend déjà buildé)
#        ./run.sh --build (rebuild frontend puis lance backend)
set -euo pipefail

cd "$(dirname "$0")"

# Option --build : rebuild le frontend avant
if [ "${1:-}" = "--build" ]; then
  ./rebuild.sh
fi

# Vérifie que le bundle frontend existe
if [ ! -f "frontend/build/index.html" ]; then
  echo "⚠️  frontend/build n'existe pas. Lance ./rebuild.sh d'abord (ou ./run.sh --build)"
  exit 1
fi

# Setup venv Python si absent
if [ ! -d ".venv" ]; then
  echo "==> Création du venv Python..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "==> Installation des dépendances Python..."
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt

echo ""
echo "================================================================"
echo "  MUSFALA Voyage - Serveur local"
echo "  URL : http://localhost:10000"
echo "  API health : http://localhost:10000/api/health"
echo "  API stats  : http://localhost:10000/api/stats"
echo "  CTRL+C pour arrêter"
echo "================================================================"
echo ""

cd backend
exec uvicorn main:app --host 127.0.0.1 --port 10000 --reload
