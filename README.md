# Evaluator — Bootstrap Package

## Quick Start

1. **Create the repo and copy these files in:**
   ```bash
   mkdir evaluator && cd evaluator
   # Copy all files from this bootstrap package into the evaluator/ directory
   chmod +x init.sh
   ```

2. **Open Claude Code in the evaluator/ directory:**
   ```bash
   claude
   ```

3. **Run the Initializer Agent:**
   Copy the entire contents of `INITIALIZER_PROMPT.md` and paste it as your first prompt. This scaffolds the full project.

4. **Subsequent sessions — use slash commands:**
   ```
   /start-session     # Beginning of every session
   /end-session       # End of every session
   /status            # Check progress anytime
   ```

## Files in This Package

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project spec — agents read this first every session |
| `feature_list.json` | 37 features with pass/fail tracking |
| `evaluator-progress.txt` | Session-by-session progress log |
| `init.sh` | Dev environment startup script |
| `INITIALIZER_PROMPT.md` | Paste into Claude Code for first session |
| `.claude/commands/` | 7 custom slash commands |

## Architecture

Standalone FastAPI + Next.js + PostgreSQL application.
Integrates with Harness Exchange via API calls (no shared DB).
See `CLAUDE.md` for full specification.
