Create and run a database migration. The user provides a migration name.

1. `cd backend && source .venv/bin/activate`
2. `alembic revision --autogenerate -m "$ARGUMENTS"`
3. Review the generated migration file and fix any issues
4. `alembic upgrade head`
5. Verify with: `alembic current`
