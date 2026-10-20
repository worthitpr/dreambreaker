# Copyright 2026 Kritsia Quiñones (XXSELENEPRXX). Licensed under the Apache License, Version 2.0.
"""Leave-one-out backtest over the graveyard: each case is evaluated WITHOUT itself in the graveyard.
WARNING: profiles were scored knowing the outcome. This measures engine coherence, not predictive accuracy."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dreambreaker_core import Dreambreaker as Core, KILL_DIMENSIONS as K
from dreambreaker import Dreambreaker
db, avg = Dreambreaker(), Core()
ALARM = ('KILLED', 'CRITICAL_REPAIR', 'HOLD')
stats = {'avg': [0, 0], 'new': [0, 0]}; nf = ns = 0
print(f"{'CASE':24}{'REAL':9}{'AVERAGE ONLY':27}{'DREAMBREAKER':28}CLOSEST PRECEDENT")
for c in db.graveyard['cases']:
    s = {**{d: db.default for d in K}, **c['risks']}
    v1 = avg.kill_score(s)['verdict']
    r = db.evaluate(s, {d: ['public historical record'] for d in c['risks']}, exclude=c['id'])
    v2, near = r['verdict'], r['precedents'][0]
    if c['outcome'] == 'FAILURE':
        nf += 1; stats['avg'][0] += v1.startswith(ALARM); stats['new'][0] += v2.startswith(ALARM)
    else:
        ns += 1; stats['avg'][1] += not v1.startswith('KILLED'); stats['new'][1] += not v2.startswith('KILLED')
    print(f"{c['name'][:23]:24}{c['outcome']:9}{v1:27}{v2:28}{near['name']} ({near['outcome']})")
print(f"\nFailures flagged (kill/repair/hold):  average-only {stats['avg'][0]}/{nf}   DREAMBREAKER {stats['new'][0]}/{nf}")
print(f"Successes not killed:                 average-only {stats['avg'][1]}/{ns}   DREAMBREAKER {stats['new'][1]}/{ns}")
