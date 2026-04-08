End the current session cleanly. Do these steps in order:

1. Run all tests: `cd backend && source .venv/bin/activate && python -m pytest tests/ -v && cd ..`
2. If tests fail, fix them before proceeding
3. For any features completed this session, update feature_list.json — set `"passes": true` ONLY for features with passing tests
4. Append a new session entry to evaluator-progress.txt with:
   - Session number (increment from last)
   - Date
   - Features worked on (by ID)
   - What was accomplished
   - Any issues or incomplete work
   - What the next session should work on
5. Run `git add -A && git status` to review changes
6. Commit with the appropriate [FXXX] prefix: `git commit -m "[FXXX] Description"`
7. Report: features completed, tests passing, what's next
