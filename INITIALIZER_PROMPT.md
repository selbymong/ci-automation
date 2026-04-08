# Initializer Agent Prompt

**Paste this entire prompt into Claude Code for the very first session.**

---

You are the **Initializer Agent** for the Evaluator project. Your job is to scaffold the entire project so that subsequent Coding Agents can pick up features one at a time and make incremental progress.

## Context

Read `CLAUDE.md` first — it contains the full project specification, stack, directory structure, and conventions.

Read `feature_list.json` — it contains 37 features across 9 phases. You are NOT implementing features. You are creating the skeleton that makes feature implementation possible.

## Your Tasks (in this exact order)

### 1. Initialize Git Repository
```bash
git init
git add CLAUDE.md feature_list.json evaluator-progress.txt init.sh .claude/
git commit -m "[INIT] Bootstrap project with CLAUDE.md, feature list, init script, and slash commands"
```

### 2. Create docker-compose.yml
PostgreSQL 16 with:
- Database: `evaluator`
- User: `evaluator`
- Password: `evaluator_dev` (dev only)
- Port: 5432
- Volume for data persistence
- Health check

### 3. Scaffold Backend (FastAPI)
Create the directory structure from CLAUDE.md. Specifically:

**backend/requirements.txt:**
```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
sqlalchemy[asyncio]>=2.0.30
asyncpg>=0.29.0
alembic>=1.13.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
httpx>=0.27.0
resend>=2.0.0
python-multipart>=0.0.9
pytest>=8.2.0
pytest-asyncio>=0.23.0
```

**backend/app/main.py:**
- FastAPI app with title "Evaluator API"
- CORS middleware allowing localhost:3000
- `/health` endpoint returning `{"status": "healthy", "service": "evaluator"}`
- Include routers (initially empty)

**backend/app/config.py:**
- Pydantic Settings class with: DATABASE_URL, JWT_SECRET, HARNESS_API_URL, HARNESS_API_KEY, HARNESS_API_MOCK (bool, default True), RESEND_API_KEY
- Load from environment / .env file

**backend/app/database.py:**
- Async SQLAlchemy engine and session factory
- Base declarative model
- `get_db()` dependency

**backend/app/models/__init__.py:**
- Import all models (empty for now)

**backend/app/models/user.py:**
- User model with: id (UUID), email, hashed_password, full_name, role (StrEnum: analyst, reviewer, admin), is_active, created_at, updated_at

**backend/app/auth/:**
- JWT token creation and verification
- Password hashing utilities
- `get_current_user` dependency
- Role-checking dependency (`require_role("admin")`)

**backend/Dockerfile:**
- Python 3.11-slim base
- Install requirements
- Run uvicorn

**Alembic setup:**
- `alembic init migrations`
- Configure env.py for async SQLAlchemy
- Configure alembic.ini to use DATABASE_URL from environment
- Generate initial migration with User table

### 4. Scaffold Frontend (Next.js)
```bash
cd frontend
npx create-next-app@14 . --typescript --tailwind --app --src-dir --no-import-alias
```

Then add:
- **src/lib/api.ts**: Typed API client with base URL from env, auth header injection, typed fetch wrappers
- **src/app/layout.tsx**: Root layout with basic nav structure
- **src/app/page.tsx**: Dashboard placeholder (just shows "Evaluator" and a login link)
- **src/app/login/page.tsx**: Login form placeholder (email + password fields, submit handler calling API)
- **frontend/Dockerfile**: Node 20-slim, install deps, run next dev

### 5. Create Shared API Contracts
**shared/api_contracts/harness_cra.py:**
```python
from pydantic import BaseModel
from typing import Optional
from datetime import date

class T3010Financial(BaseModel):
    business_number: str
    fiscal_year_end: date
    revenue_total: Optional[float] = None
    revenue_donations: Optional[float] = None
    revenue_government: Optional[float] = None
    expenses_total: Optional[float] = None
    expenses_programs: Optional[float] = None
    expenses_admin: Optional[float] = None
    expenses_fundraising: Optional[float] = None
    assets_total: Optional[float] = None
    liabilities_total: Optional[float] = None
    num_employees: Optional[int] = None
```

**shared/api_contracts/harness_scrape.py** and **evaluator_export.py**: Similar Pydantic models matching the API contracts in CLAUDE.md.

### 6. Create Mock Harness Client
**backend/app/integrations/harness_client.py:**
- `HarnessClient` class with methods: `get_t3010_data(bn)`, `get_scraped_data(bn)`, `get_organization(bn)`
- Real implementation using httpx
- Mock implementation returning test data
- Factory function that reads `HARNESS_API_MOCK` setting

### 7. Create .env.example
```
DATABASE_URL=postgresql+asyncpg://evaluator:evaluator_dev@localhost:5432/evaluator
JWT_SECRET=dev-secret-change-in-production
HARNESS_API_URL=https://api.harnessexchange.com
HARNESS_API_KEY=
HARNESS_API_MOCK=true
RESEND_API_KEY=
```

### 8. Create Backend Test Fixtures
**backend/tests/conftest.py:**
- Test database setup (create/drop test DB)
- Async test client fixture
- Auth fixture (create test user, get JWT token)
- Override `get_db` dependency for test session

**backend/tests/test_health.py:**
- Test that GET /health returns 200 with correct body

### 9. Verify Everything Works
```bash
# Start services
docker compose up -d --wait
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --port 8000 &
sleep 2
curl -s http://localhost:8000/health
# Should return {"status":"healthy","service":"evaluator"}

# Run tests
python -m pytest tests/ -v
# Should pass

# Frontend
cd ../frontend
npm install
npm run dev &
sleep 3
curl -s http://localhost:3000
# Should return HTML
```

### 10. Update Progress and Commit
Update `evaluator-progress.txt`:
```
## Session 1 — Initializer Agent
- Scaffolded FastAPI backend with auth, models, config, database
- Scaffolded Next.js frontend with TypeScript and Tailwind
- Created docker-compose.yml with PostgreSQL 16
- Set up Alembic with initial User migration
- Created shared API contract definitions
- Created mock Harness client
- Created test fixtures and health check test
- All services start and health checks pass
- **Next session**: Start Phase 1 with F001 (but scaffolding is done, so F001 may already pass — verify and move to F002)
```

Commit:
```bash
git add -A
git commit -m "[INIT] Full project scaffold — FastAPI + Next.js + PostgreSQL + Docker Compose + Alembic + auth + test fixtures"
```

## Important Notes
- Do NOT implement any features from feature_list.json. Only create the skeleton.
- The first Coding Agent session will pick up F001 and either verify it passes (since scaffolding covers most of it) or finish the remaining pieces.
- Keep the code minimal but correct. No placeholder comments like "TODO: implement this". If something isn't implemented, don't include it.
- Make sure `init.sh` actually works after scaffolding. The next agent will run it first thing.
