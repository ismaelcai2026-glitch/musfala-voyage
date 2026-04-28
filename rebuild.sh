#!/usr/bin/env bash
# MUSFALA Voyage - Rebuild du frontend React
# Usage: ./rebuild.sh
set -euo pipefail

cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
  echo "==> Installation des dépendances npm (1ère fois, ~1-2 min)..."
  npm install
fi

echo "==> Build du frontend..."
CI=true npm run build

echo ""
echo "✅ Build terminé. Le bundle est dans frontend/build/"
echo "Lance ./run.sh pour démarrer le serveur."
