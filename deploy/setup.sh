#!/usr/bin/env bash
# First-time VPS setup for rumors.90ten.life
# Run as root on 72.62.174.193: bash setup.sh
set -euo pipefail

APP_DIR=/opt/rumors
DB_NAME=rumors
DB_USER=rumors
DB_PASS=${DB_PASS:-changeme}

echo "=== 1. System deps ==="
apt-get update -q
apt-get install -y -q python3.11 python3.11-venv python3-pip postgresql postgresql-client nodejs npm git

echo "=== 2. PostgreSQL: create user + db ==="
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || true

echo "=== 3. Clone / pull repo ==="
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull
else
  git clone https://github.com/phillyshah/rumors "$APP_DIR"
fi

echo "=== 4. Python venv ==="
python3.11 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q --upgrade pip
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt"
"$APP_DIR/venv/bin/pip" install -q gunicorn

echo "=== 5. Frontend build ==="
cd "$APP_DIR/frontend"
npm ci --silent
npm run build

echo "=== 6. .env ==="
if [ ! -f "$APP_DIR/.env" ]; then
  cat > "$APP_DIR/.env" <<EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
JWT_SECRET=$(openssl rand -hex 32)
ANTHROPIC_API_KEY=
EOF
  echo "Created $APP_DIR/.env — add ANTHROPIC_API_KEY if desired"
fi

echo "=== 7. Migrations + seed ==="
cd "$APP_DIR/backend"
DATABASE_URL="postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME" \
  "$APP_DIR/venv/bin/python" -m alembic upgrade head
DATABASE_URL="postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME" \
  "$APP_DIR/venv/bin/python" -m seed.seed_all

echo "=== 8. Systemd service ==="
cp "$APP_DIR/deploy/rumors.service" /etc/systemd/system/rumors.service
systemctl daemon-reload
systemctl enable rumors
systemctl restart rumors
systemctl status rumors --no-pager

echo "=== 10. Traefik config ==="
cp "$APP_DIR/deploy/traefik-rumors.yml" /opt/traefik/dynamic/rumors.yml
echo "Traefik config installed — rumors.90ten.life should come up within ~30s"

echo ""
echo "=== Setup complete ==="
echo "  App:  https://rumors.90ten.life"
echo "  Logs: journalctl -u rumors -f"
