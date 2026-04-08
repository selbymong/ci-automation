Run tests for a specific feature. The user provides a feature ID like F001.

1. Look up the feature in feature_list.json to understand what it covers
2. Identify the relevant test files based on the feature's domain
3. Run those specific tests: `cd backend && source .venv/bin/activate && python -m pytest tests/ -v -k "relevant_test_name"`
4. If frontend E2E tests exist for the feature, run those too
5. Report pass/fail results
