#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Evaluator — Development Environment Init Script
# Run at the start of every Claude Code session.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "  Evaluator — Init"
echo "========================================="

# ── 1. Docker services (PostgreSQL) ──
echo ""
echo "[1/6] Starting Docker services..."
if ! docker compose ps --status running 2>/dev/null | grep -q postgres; then
    docker compose up -d --wait
    echo "  ✓ Docker services started"
else
    echo "  ✓ Docker services already running"
fi

# ── 2. Backend dependencies ──
echo ""
echo "[2/6] Checking backend dependencies..."
if [ -f backend/requirements.txt ]; then
    cd backend
    if [ ! -d .venv ]; then
        python3 -m venv .venv
        echo "  Created virtualenv"
    fi
    source .venv/bin/activate
    pip install -q -r requirements.txt 2>/dev/null
    echo "  ✓ Backend dependencies installed"
    cd "$SCRIPT_DIR"
else
    echo "  ⚠ No requirements.txt yet (expected during scaffolding)"
fi

# ── 3. Database migrations ──
echo ""
echo "[3/6] Running database migrations..."
if [ -f backend/alembic.ini ]; then
    cd backend
    source .venv/bin/activate 2>/dev/null || true
    alembic upgrade head
    echo "  ✓ Migrations applied"
    cd "$SCRIPT_DIR"
else
    echo "  ⚠ No alembic.ini yet (expected during scaffolding)"
fi

# ── 4. Start backend ──
echo ""
echo "[4/6] Starting backend..."
if [ -f backend/app/main.py ]; then
    cd backend
    source .venv/bin/activate 2>/dev/null || true
    # Kill any existing backend process
    pkill -f "uvicorn app.main" 2>/dev/null || true
    sleep 1
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    echo "  ✓ Backend started (PID: $BACKEND_PID)"
    cd "$SCRIPT_DIR"
else
    echo "  ⚠ No main.py yet (expected during scaffolding)"
fi

# ── 5. Start frontend ──
echo ""
echo "[5/6] Starting frontend..."
if [ -f frontend/package.json ]; then
    cd frontend
    if [ ! -d node_modules ]; then
        npm install --silent
    fi
    # Kill any existing frontend process
    pkill -f "next dev" 2>/dev/null || true
    sleep 1
    npm run dev &
    FRONTEND_PID=$!
    echo "  ✓ Frontend started (PID: $FRONTEND_PID)"
    cd "$SCRIPT_DIR"
else
    echo "  ⚠ No package.json yet (expected during scaffolding)"
fi

# ── 6. Health check ──
echo ""
echo "[6/6] Running health checks..."
sleep 3

BACKEND_OK=false
FRONTEND_OK=false

for i in {1..10}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        BACKEND_OK=true
        break
    fi
    sleep 1
done

for i in {1..10}; do
    if curl -sf http://localhost:3000 > /dev/null 2>&1; then
        FRONTEND_OK=true
        break
    fi
    sleep 1
done

echo ""
echo "========================================="
echo "  Health Check Results"
echo "========================================="
if [ "$BACKEND_OK" = true ]; then
    echo "  ✓ Backend:  http://localhost:8000 (healthy)"
else
    echo "  ✗ Backend:  http://localhost:8000 (NOT responding)"
fi
if [ "$FRONTEND_OK" = true ]; then
    echo "  ✓ Frontend: http://localhost:3000 (healthy)"
else
    echo "  ✗ Frontend: http://localhost:3000 (NOT responding)"
fi
echo "========================================="

# Return non-zero if either service is down
if [ "$BACKEND_OK" = false ] || [ "$FRONTEND_OK" = false ]; then
    echo ""
    echo "⚠ Some services are not healthy. Fix before starting new feature work."
    # Don't exit 1 during scaffolding phase — services may not exist yet
fi
