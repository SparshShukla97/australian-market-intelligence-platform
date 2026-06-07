#!/bin/bash
# start.sh — Launch Australian Market Intelligence (API + Frontend)
#
# Usage:
#   bash start.sh
#
# Starts:
#   1. FastAPI backend  → http://localhost:8000
#   2. Frontend server  → http://localhost:3000
#
# Requires: MongoDB running locally, venv set up with pip install -r requirements.txt
#
# ── PIPELINE (fetch fresh articles) ──────────────────────
#
#   Run once manually:
#     PYTHONPATH=src venv/bin/python src/run_full_pipeline.py
#
#   Run on a schedule (every 1 hour, auto-restarts on reboot):
#     PYTHONPATH=src venv/bin/python src/auto_scheduler.py
#
#   The pipeline takes ~9 minutes. It fetches RSS feeds, scrapes
#   articles, runs NLP + GPT enrichment, and upserts into MongoDB.
#   The frontend will show updated articles after the next page refresh.
# ─────────────────────────────────────────────────────────

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# ── Colours ──────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓${NC}  $1"; }
warn() { echo -e "${YELLOW}  !${NC}  $1"; }
fail() { echo -e "${RED}  ✗${NC}  $1"; exit 1; }

echo ""
echo "  Australian Market Intelligence — Starting services"
echo "  ──────────────────────────────────────────────────"
echo ""

# ─────────────────────────────────────────────────────────
# 1. Check venv exists
# ─────────────────────────────────────────────────────────
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
VENV_UVICORN="$PROJECT_ROOT/venv/bin/uvicorn"

if [ ! -f "$VENV_PYTHON" ]; then
  fail "venv not found. Run:  python3 -m venv venv && venv/bin/pip install -r requirements.txt"
fi
ok "venv found"

# ─────────────────────────────────────────────────────────
# 2. Check .env exists
# ─────────────────────────────────────────────────────────
if [ ! -f "$PROJECT_ROOT/.env" ]; then
  warn ".env file missing — OPENAI_API_KEY and MONGO_URI may not be set"
else
  ok ".env found"
fi

# ─────────────────────────────────────────────────────────
# 3. Check MongoDB is reachable
# ─────────────────────────────────────────────────────────
if ! "$VENV_PYTHON" -c "
from pymongo import MongoClient
import os, sys
from dotenv import load_dotenv
load_dotenv()
try:
    c = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'), serverSelectionTimeoutMS=3000)
    c.admin.command('ping')
    print('ok')
except Exception as e:
    print(f'fail: {e}')
    sys.exit(1)
" 2>/dev/null | grep -q "^ok"; then
  fail "MongoDB is not running or not reachable. Start it with:  brew services start mongodb-community"
fi
ok "MongoDB reachable"

# ─────────────────────────────────────────────────────────
# 4. Check required packages are installed
# ─────────────────────────────────────────────────────────
if ! "$VENV_PYTHON" -c "import fastapi, uvicorn, pymongo, yfinance" 2>/dev/null; then
  fail "Missing Python packages. Run:  venv/bin/pip install -r requirements.txt"
fi
ok "Dependencies installed"

# ─────────────────────────────────────────────────────────
# 5. Stop anything already on ports 8000 / 3000
# ─────────────────────────────────────────────────────────
stop_port() {
  local pid
  pid=$(lsof -ti tcp:"$1" 2>/dev/null || true)
  if [ -n "$pid" ]; then
    warn "Port $1 already in use (PID $pid) — stopping it"
    kill "$pid" 2>/dev/null || true
    sleep 1
  fi
}
stop_port 8000
stop_port 3000

# ─────────────────────────────────────────────────────────
# 6. Shut down all background jobs cleanly on Ctrl+C
# ─────────────────────────────────────────────────────────
cleanup() {
  echo ""
  warn "Shutting down..."
  kill 0 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

mkdir -p logs

# ─────────────────────────────────────────────────────────
# 7. Start FastAPI backend
# ─────────────────────────────────────────────────────────
PYTHONPATH="$PROJECT_ROOT/src" \
  "$VENV_UVICORN" api:app --port 8000 \
  --app-dir "$PROJECT_ROOT/src" \
  >> logs/api.log 2>&1 &
API_PID=$!

sleep 2
if ! kill -0 $API_PID 2>/dev/null; then
  fail "FastAPI failed to start — check logs/api.log"
fi
ok "FastAPI started (PID $API_PID)"

# ─────────────────────────────────────────────────────────
# 8. Start frontend static server
# ─────────────────────────────────────────────────────────
"$VENV_PYTHON" -m http.server 3000 \
  --directory "$PROJECT_ROOT/frontend" \
  >> logs/frontend.log 2>&1 &
FE_PID=$!
ok "Frontend started (PID $FE_PID)"

# ─────────────────────────────────────────────────────────
# Done — print URLs
# ─────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  All services running. Press Ctrl+C to stop.${NC}"
echo -e "${GREEN}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Frontend   →  http://localhost:3000"
echo "  API        →  http://localhost:8000/api/articles"
echo "  API docs   →  http://localhost:8000/docs"
echo ""
echo "  Logs:"
echo "    tail -f logs/api.log"
echo "    tail -f logs/frontend.log"
echo ""

open http://localhost:3000 2>/dev/null || true

# Keep process alive until Ctrl+C
wait
