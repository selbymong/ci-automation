Show project status. Run:

```bash
echo "=== Feature Completion ==="
python3 -c "
import json
with open('feature_list.json') as f:
    features = json.load(f)
total = len(features)
done = sum(1 for f in features if f['passes'])
phases = {}
for f in features:
    p = f['phase']
    if p not in phases:
        phases[p] = {'total': 0, 'done': 0}
    phases[p]['total'] += 1
    if f['passes']:
        phases[p]['done'] += 1
print(f'Overall: {done}/{total} ({100*done//total}%)')
print()
names = {1:'Foundation',2:'Pipeline',3:'Financial',4:'SRSS',5:'Review',6:'Demand',7:'Analytics',8:'Integration',9:'Migration'}
for p in sorted(phases):
    d = phases[p]
    bar = '█' * d['done'] + '░' * (d['total']-d['done'])
    print(f'  Phase {p} {names.get(p,\"?\"):12s} [{bar}] {d[\"done\"]}/{d[\"total\"]}')
print()
print('Next incomplete features:')
for f in features:
    if not f['passes']:
        print(f'  {f[\"id\"]} - {f[\"description\"]}')
        break
"
```

Then show the last 5 lines of evaluator-progress.txt and the last 5 git commits.
