#!/usr/bin/env bash
# First-time VPS setup for rumors.90ten.life
# Already on the VPS as root: bash setup.sh
# Required env vars:
#   DATABASE_URL  — Supabase connection string
#   JWT_SECRET    — random secret (generated below if omitted)
#   ANTHROPIC_API_KEY — optional, for Claude enrichment
set -euo pipefail

APP_DIR=/opt/rumors

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: set DATABASE_URL to your Supabase connection string first"
  echo "  export DATABASE_URL='postgresql://postgres:[password]@[host]:5432/postgres'"
  exit 1
fi

echo "=== 1. System deps ==="
apt-get update -q
apt-get install -y -q python3 python3-venv python3-pip nodejs npm git

echo "=== 2. Clone / pull repo ==="
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull
else
  git clone https://github.com/phillyshah/rumors "$APP_DIR"
fi

echo "=== 3. Python venv ==="
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q --upgrade pip
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt"

echo "=== 4. Frontend build ==="
cd "$APP_DIR/frontend"
npm ci --silent
npm run build

echo "=== 5. .env ==="
cat > "$APP_DIR/.env" <<EOF
DATABASE_URL=${DATABASE_URL}
JWT_SECRET=${JWT_SECRET:-$(openssl rand -hex 32)}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
EOF
echo "Wrote $APP_DIR/.env"

echo "=== 6. Migrations + seed ==="
cd "$APP_DIR/backend"
"$APP_DIR/venv/bin/python" -m alembic upgrade head
"$APP_DIR/venv/bin/python" -m seed.seed_all

echo "=== 7. Systemd service ==="
cp "$APP_DIR/deploy/rumors.service" /etc/systemd/system/rumors.service
systemctl daemon-reload
systemctl enable rumors
systemctl restart rumors
sleep 2
systemctl status rumors --no-pager | head -15

echo "=== 8. Traefik config ==="
cp "$APP_DIR/deploy/traefik-rumors.yml" /opt/traefik/dynamic/rumors.yml
echo "Traefik config installed — SSL provisioning via Let's Encrypt (~30s)"

echo ""
echo "=== Done ==="
echo "  App:  https://rumors.90ten.life"
echo "  Logs: journalctl -u rumors -f"
