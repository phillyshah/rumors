#!/usr/bin/env bash
# Deploy latest main to rumors.90ten.life
# Run locally: bash deploy/deploy.sh
set -euo pipefail

VPS=root@72.62.174.193
APP_DIR=/opt/rumors

echo "==> Deploying to $VPS..."
ssh "$VPS" bash -s <<'REMOTE'
set -euo pipefail
APP_DIR=/opt/rumors

echo "--- pull ---"
git -C "$APP_DIR" pull

echo "--- frontend build ---"
cd "$APP_DIR/frontend"
npm ci --silent
npm run build

echo "--- pip sync ---"
"$APP_DIR/venv/bin/pip" install -q --upgrade pip
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt"

echo "--- migrate ---"
cd "$APP_DIR/backend"
source "$APP_DIR/.env" 2>/dev/null || true
"$APP_DIR/venv/bin/python" -m alembic upgrade head

echo "--- restart ---"
systemctl restart rumors
sleep 2
systemctl status rumors --no-pager | head -10

echo "--- done ---"
REMOTE

echo "==> Deployed. https://rumors.90ten.life"
