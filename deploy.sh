#!/usr/bin/env bash
set -e

REPO_DIR="/path/to/your/repo"  # <- поправьте, или запускайте скрипт внутри репо
cd "$REPO_DIR"

echo "Pulling latest code..."
git pull origin main

echo "Building and starting containers..."
docker compose build --pull
docker compose up -d --remove-orphans

echo "Pruning unused images..."
docker image prune -f

echo "Done. Showing bot logs (last 100 lines):"
docker compose logs --tail=100 bot