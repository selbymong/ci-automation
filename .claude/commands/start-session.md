Run the session startup sequence. Do these steps in order:

1. Run `pwd` to confirm we're in the evaluator directory
2. Run `cat evaluator-progress.txt` to read the last session's work
3. Run `git log --oneline -20` to see recent commits
4. Run `cat feature_list.json | python3 -c "import json,sys; [print(f['id'],f['description']) for f in json.load(sys.stdin) if not f['passes']]" | head -5` to find the next incomplete features
5. Run `bash init.sh` to start services and verify health
6. If health checks fail, diagnose and fix before proceeding
7. Report: what was done last session, what feature you'll work on next, and any issues from health check
