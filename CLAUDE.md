# Evaluator — CI Evaluation Workflow System

## Project Identity

You are building **Evaluator**, a standalone web application for managing charity evaluation operations. It replaces the Excel-based workflow currently run by Charity Intelligence Canada (CI) — a 15-sheet workbook tracking ~843 active charity evaluations across 7 analysts in seasonal cycles.

This system is **standalone** — it has its own database, auth, and hosting. It integrates with the Harness Exchange platform via API calls only (no shared database). If the CI relationship ends, Evaluator continues to operate independently.

## Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | FastAPI | 0.111+ |
| Language | Python | 3.11+ |
| Frontend | Next.js (App Router) | 14+ |
| Language | TypeScript | 5+ |
| Database | PostgreSQL | 16 |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Email | Resend | Latest |
| CSS | Tailwind CSS | 3+ |
| Containers | Docker Compose | 3.8+ |
| Testing | pytest + httpx (API), Playwright (E2E) |

## Directory Structure

```
evaluator/
├── CLAUDE.md                    # This file
├── feature_list.json            # Feature tracking (agents: only change "passes" field)
├── evaluator-progress.txt       # Session log (update every session)
├── init.sh                      # Dev environment startup
├── docker-compose.yml           # PostgreSQL + services
├── .claude/
│   └── commands/                # Custom slash commands
│       ├── start-session.md
│       ├── end-session.md
│       ├── test-feature.md
│       ├── import-sheet.md
│       ├── db-migrate.md
│       └── status.md
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── database.py          # Async SQLAlchemy engine + session
│   │   ├── auth/                # JWT auth, role middleware
│   │   ├── models/              # SQLAlchemy models (one file per domain)
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Business logic layer
│   │   └── integrations/        # Harness API client
│   ├── migrations/              # Alembic
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py          # Test fixtures, test DB
│   │   ├── test_auth.py
│   │   └── ...
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   ├── components/          # React components
│   │   ├── lib/                 # API client, utils, types
│   │   └── hooks/               # Custom React hooks
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   ├── data/                    # Source Excel file lives here
│   │   └── Charities_in_Process_2025.xlsx
│   ├── import/                  # Per-sheet import scripts
│   │   ├── import_name_reference.py
│   │   ├── import_jd_charities.py
│   │   ├── import_summer_2025.py
│   │   ├── import_donor_requests.py
│   │   └── import_request_listing.py
│   └── seed.py                  # Dev seed data
└── shared/
    └── api_contracts/           # Harness API contract definitions
        ├── harness_cra.py       # T3010 data schemas
        ├── harness_scrape.py    # Scraped data schemas
        └── evaluator_export.py  # Our export API schemas
```

## Coding Conventions

### Python (Backend)
- **Pydantic models** for ALL API request/response schemas. No raw dicts crossing API boundaries.
- **Async SQLAlchemy** throughout. Use `async_session` context manager.
- **Type hints** on every function signature.
- **Service layer pattern**: Routers call services, services call models. Routers never contain business logic.
- **UUID primary keys**: Use `uuid.uuid4()` defaults, stored as `CHAR(36)`.
- **Enum fields**: Use Python `StrEnum` for workflow stages, roles, etc. Store as VARCHAR in DB.
- **Naming**: `snake_case` for everything. Table names singular (`charity`, not `charities`).

### TypeScript (Frontend)
- **React Server Components** where possible. Client components only when state/interactivity needed.
- **Zod** for form validation, matching backend Pydantic schemas.
- **Exhaustive TypeScript enums** for workflow stages — compiler catches missing cases.
- **API client**: Single `api.ts` module with typed fetch wrappers. No raw fetch calls in components.
- **Tailwind only**: No CSS modules, no styled-components.

### Database
- Field names align with Harness conventions: `snake_case`, `_id` suffix for FKs, `_at` suffix for timestamps.
- Every table has `created_at TIMESTAMP DEFAULT NOW()` and `updated_at TIMESTAMP DEFAULT NOW()`.
- Soft deletes via `deleted_at` column where needed (charities, users). No hard deletes on core data.

### Git
- **Commit prefix**: `[FXXX]` matching the feature ID from feature_list.json.
- **Branch per feature**: `feature/FXXX-short-description`.
- **Clean commits only**: No WIP, no debug code, no console.log. Every commit should pass tests.
- **Commit at feature completion**, not mid-feature. If a feature spans sessions, commit the partial progress as a clean, working intermediate state.

## Session Workflow

**CRITICAL: Follow this sequence every session. Do not skip steps.**

1. `pwd` — Confirm you're in the evaluator/ directory.
2. `cat evaluator-progress.txt` — Read what happened last session.
3. `git log --oneline -20` — See recent commits for context.
4. `cat feature_list.json | python3 -c "import json,sys; [print(f['id'],f['description']) for f in json.load(sys.stdin) if not f['passes']]" | head -5` — Find next incomplete features.
5. `bash init.sh` — Start services, verify health. **If health check fails, fix that first before any new work.**
6. Choose ONE feature. Implement it.
7. Write tests. Run tests. Fix failures.
8. Update `feature_list.json` — set `passes: true` ONLY after tests pass.
9. Update `evaluator-progress.txt` — Write what you did this session.
10. `git add -A && git commit -m "[FXXX] Description of what was implemented"`

## Behavioral Rules

**These are non-negotiable. Violations lead to broken agent chains.**

- **Work on ONE feature at a time.** Do not start F002 until F001 passes.
- **Do not skip ahead.** Features within a phase are ordered by dependency.
- **Do not mark features as passing without running tests.** A feature is not done until it has at least one passing integration test.
- **It is unacceptable to remove or edit feature descriptions in feature_list.json.** You may only change the `passes` field from `false` to `true`.
- **Always update evaluator-progress.txt before your final commit.** The next agent depends on this.
- **Always run init.sh at session start.** If the app is broken, fix it before starting new work.
- **Leave the codebase in a clean, working state.** No half-implemented features. If you can't finish a feature, revert to the last working state and document what you attempted in the progress file.
- **Use the Harness API client for external data.** Never hardcode CRA data or mock external calls in production code. Mocking is for tests only.

## Harness API Integration

All Harness API calls go through `backend/app/integrations/harness_client.py`.

```python
# Configuration via environment variables
HARNESS_API_URL=https://api.harnessexchange.com  # or localhost for dev
HARNESS_API_KEY=xxx                                # API key auth
```

**Endpoints consumed:**
- `GET /api/v1/cra/t3010/{bn}` — CRA T3010 financial data by business number
- `GET /api/v1/scrape/charity/{bn}` — Scraped charity website data
- `GET /api/v1/organizations/{bn}` — Canonical organization record

**Endpoints exposed (by Evaluator):**
- `GET /api/v1/evaluations/published` — All published evaluations
- `GET /api/v1/evaluations/updated-since?since=ISO_TIMESTAMP` — Incremental sync
- `GET /api/v1/demand/signals` — Aggregated donor demand data

**In development**, mock the Harness API endpoints. The integrations module should have a `mock_harness_client.py` that returns realistic test data. Toggle via `HARNESS_API_MOCK=true` env var.

## Evaluation Workflow Stages

The 12-stage state machine. Transitions are forward-only except for explicit rejection back to a prior stage.

```
prioritized → assigned → financials_acquisition → federal_corp_check
→ cra_data_pull → financial_analysis → srss_scoring → impact_scoring
→ review → charity_outreach → charity_response → published
```

Each transition is logged in `evaluation_stage_log` with timestamp, actor, and optional note.

## SRSS Scoring

26 questions across 6 categories. Each question scored 0-8 (varies by question). Category totals converted to percentages. Total percentage maps to letter grade:

| Grade | Range |
|-------|-------|
| A+ | 90-100% |
| A | 80-89% |
| B+ | 70-79% |
| B | 60-69% |
| C | 50-59% |
| D | 40-49% |
| F | <40% |

## Priority Scoring Algorithm

Composite score from 4 components, each weighted 1-5:

```
priority = (views_score * 0.3) + (staleness_score * 0.3) + (demand_score * 0.2) + (top100_bonus * 0.2)
```

- **views_score**: Quintile ranking of page views (from GA4 data)
- **staleness_score**: Years since last evaluation (capped at 5)
- **demand_score**: Quintile ranking of donor request votes
- **top100_bonus**: 5 if in Top 100, 0 otherwise

Output is integer 1-5 (1 = highest priority).

## Testing Requirements

- **Every API endpoint**: At least one happy-path and one error-case test via `pytest` + `httpx.AsyncClient`.
- **Every state transition**: Test that valid transitions succeed and invalid transitions raise errors.
- **Data imports**: Test with a small fixture subset of the Excel data, not the full file.
- **No mocking the database in tests**: Use a real test PostgreSQL instance (Docker).
- **Playwright E2E**: Required for Kanban board, financial data entry form, and SRSS scoring form. Not required for every page.

## Useful Commands

```bash
# Start everything
bash init.sh

# Run backend tests
cd backend && python -m pytest tests/ -v

# Run a specific test
cd backend && python -m pytest tests/test_auth.py -v

# Create a migration
cd backend && alembic revision --autogenerate -m "description"

# Run migrations
cd backend && alembic upgrade head

# Frontend dev
cd frontend && npm run dev

# Check types
cd frontend && npx tsc --noEmit
```
