# Copyright 2026 Kritsia Quiñones (XXSELENEPRXX). Licensed under the Apache License, Version 2.0.
"""DREAMBREAKER engine — adversarial idea evaluation with weakest-link verdicts and an idea graveyard.

Usage (CLI):
    python3 dreambreaker.py input.json          # prints a readable report and the JSON result
Input JSON:
    {"idea": "name", "scores": {"substitutes": 90, ...}, "evidence": {"substitutes": ["source ..."]},
     "fatal_assumptions": 0}

Truth boundary: graveyard profiles are approximate and retrospective; similarity is a question, not a prediction.
"""
from __future__ import annotations
import json, math, os, sys
from typing import Any, Dict, List, Optional
from dreambreaker_core import Dreambreaker as _Core, KILL_DIMENSIONS

CRITICAL = 90
WARNING = 80
_HERE = os.path.dirname(os.path.abspath(__file__))


class Dreambreaker(_Core):
    def __init__(self, graveyard: Optional[Dict[str, Any]] = None, graveyard_path: Optional[str] = None):
        if graveyard is None:
            with open(graveyard_path or os.path.join(_HERE, 'graveyard.json'), encoding='utf-8') as fh:
                graveyard = json.load(fh)
        self._validate_graveyard(graveyard)
        self.graveyard = graveyard
        self.default = float(graveyard.get('default_risk', 40))

    @staticmethod
    def _validate_graveyard(g: Any) -> None:
        """Fail with a clear ValueError on any malformed graveyard (never a confusing crash later)."""
        if not isinstance(g, dict) or not isinstance(g.get('cases'), list):
            raise ValueError('graveyard: must be an object with a "cases" list')
        dr = g.get('default_risk', 40)
        if isinstance(dr, bool) or not isinstance(dr, (int, float)) or not (0 <= dr <= 100):
            raise ValueError('graveyard: default_risk must be a number between 0 and 100')
        seen = set()
        for i, c in enumerate(g['cases']):
            if not isinstance(c, dict):
                raise ValueError(f'graveyard: case #{i} is not an object')
            for k in ('id', 'name', 'year', 'outcome', 'cause', 'risks'):
                if k not in c:
                    raise ValueError(f'graveyard: case #{i} is missing "{k}"')
            if not isinstance(c['id'], str) or c['id'] in seen:
                raise ValueError(f'graveyard: case #{i} has an invalid or duplicate id')
            seen.add(c['id'])
            if c['outcome'] not in ('FAILURE', 'SUCCESS'):
                raise ValueError(f"graveyard: {c['id']} outcome must be FAILURE or SUCCESS")
            if c['outcome'] == 'SUCCESS' and not c.get('lever'):
                raise ValueError(f"graveyard: success {c['id']} needs a lever")
            if not isinstance(c['risks'], dict):
                raise ValueError(f"graveyard: {c['id']} risks must be an object")
            for d, v in c['risks'].items():
                if d not in KILL_DIMENSIONS:
                    raise ValueError(f"graveyard: unknown dimension in {c['id']}: {d}")
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not (0 <= v <= 100):
                    raise ValueError(f"graveyard: invalid risk value in {c['id']}.{d}")

    @staticmethod
    def _has_evidence(refs: Any, d: str) -> bool:
        """Evidence must be a list with at least one non-empty text reference."""
        if not isinstance(refs, dict):
            return False
        v = refs.get(d)
        return isinstance(v, list) and any(isinstance(x, str) and x.strip() for x in v)

    @staticmethod
    def validate_scores(scores: Any) -> List[str]:
        if not isinstance(scores, dict):
            return ['SCORES_NOT_OBJECT']
        errors = []
        for d, v in scores.items():
            if d not in KILL_DIMENSIONS:
                errors.append(f'UNKNOWN_DIMENSION:{d}')
            elif isinstance(v, bool) or not isinstance(v, (int, float)):
                errors.append(f'NOT_NUMERIC:{d}')
            elif not math.isfinite(v):
                errors.append(f'NOT_FINITE:{d}')
            elif v < 0 or v > 100:
                errors.append(f'OUT_OF_RANGE:{d}')
        return errors

    def kill_score(self, dimension_scores, fatal_assumptions: int = 0, single_point_failures: int = 0,
                   evidence_refs: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        errors = self.validate_scores(dimension_scores)
        for name, val in (('fatal_assumptions', fatal_assumptions), ('single_point_failures', single_point_failures)):
            if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                errors.append(f'INVALID_COUNT:{name}')
        if errors:
            return {'risk_score': None, 'verdict': 'INVALID_SCORES', 'errors': errors}
        r = super().kill_score(dimension_scores, fatal_assumptions, single_point_failures)
        crit = sorted(d for d, v in dimension_scores.items() if v >= CRITICAL)
        warn = sorted(d for d, v in dimension_scores.items() if WARNING <= v < CRITICAL)
        unscored = [d for d in KILL_DIMENSIONS if d not in dimension_scores]
        r.update(critical_dimensions=crit, warning_dimensions=warn, average_verdict=r['verdict'], unscored=unscored)
        if r['verdict'].startswith(('KILLED_FATAL', 'UNKNOWN')):
            return r
        evidenced = [d for d in crit if self._has_evidence(evidence_refs, d)]
        if crit and not evidenced:
            r['verdict'] = 'HOLD_CRITICAL_UNEVIDENCED'
            r['required'] = 'Provide evidence for: ' + ', '.join(crit)
        elif evidenced:
            r['verdict'] = 'KILLED_CRITICAL_DIMENSION'
            r['killed_by'] = evidenced
        elif warn and r['verdict'] in ('SURVIVES_KILL_TEST', 'SURVIVES_WITH_MAJOR_RISK'):
            r['verdict'] = 'CRITICAL_REPAIR_REQUIRED'
            r['repair'] = warn
        # An idea cannot "survive" by leaving dangerous dimensions unscored.
        if r['verdict'].startswith('SURVIVES') and unscored:
            r['verdict'] = 'HOLD_UNSCORED_DIMENSIONS'
            r['required'] = 'Score (or justify skipping) these dimensions: ' + ', '.join(unscored)
        return r

    def _vector(self, scores):
        return [float(scores.get(d, self.default)) for d in KILL_DIMENSIONS]

    @staticmethod
    def _similarity(a, b):
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        ca, cb = [x - ma for x in a], [x - mb for x in b]
        na, nb = math.sqrt(sum(x * x for x in ca)), math.sqrt(sum(x * x for x in cb))
        return 0.0 if na == 0 or nb == 0 else sum(x * y for x, y in zip(ca, cb)) / (na * nb)

    def precedents(self, scores, k: int = 3, exclude: Optional[str] = None):
        v = self._vector(scores)
        out = [{'id': c['id'], 'name': c['name'], 'year': c['year'], 'outcome': c['outcome'],
                'similarity': round(self._similarity(v, self._vector(c['risks'])), 3),
                'cause': c['cause'], 'lever': c.get('lever')}
               for c in self.graveyard['cases'] if c['id'] != exclude]
        out.sort(key=lambda x: x['similarity'], reverse=True)
        return out[:k]

    def precedent_appeal(self, r, scores, exclude: Optional[str] = None):
        if r.get('verdict') != 'KILLED_CRITICAL_DIMENSION':
            return r
        v = self._vector(scores)
        cases = [c for c in self.graveyard['cases'] if c['id'] != exclude]
        sim = {c['id']: self._similarity(v, self._vector(c['risks'])) for c in cases}
        best_failure = max((sim[c['id']] for c in cases if c['outcome'] == 'FAILURE'), default=-1.0)
        killers = r['killed_by']
        # The precedent must have survived ALL killing dimensions, at (almost) the same severity.
        # Without the severity check, inflating a risk could buy an appeal (non-monotonic escape).
        survivors = [c for c in cases if c['outcome'] == 'SUCCESS'
                     and all(c['risks'].get(d, 0) >= CRITICAL and c['risks'].get(d, 0) >= scores[d] - 5
                             for d in killers)]
        if not survivors:
            return r
        best = max(survivors, key=lambda c: sim[c['id']])
        if sim[best['id']] > best_failure:
            r = dict(r)
            r['verdict'] = 'HOLD_PRECEDENT_APPEAL'
            r['appeal'] = {'dimensions': killers, 'precedent': best['name'], 'required_lever': best.get('lever'),
                           'success_similarity': round(sim[best['id']], 3), 'best_failure_similarity': round(best_failure, 3)}
        return r

    def evaluate(self, scores, evidence_refs=None, fatal_assumptions: int = 0, single_point_failures: int = 0,
                 exclude: Optional[str] = None):
        r = self.kill_score(scores, fatal_assumptions, single_point_failures, evidence_refs)
        if r['verdict'] == 'INVALID_SCORES':
            return r
        if r['verdict'] == 'UNKNOWN':
            return r
        r = self.precedent_appeal(r, scores, exclude)
        r['precedents'] = self.precedents(scores, 3, exclude)
        # Robustness: scores within 5 points of a threshold make the verdict fragile to scoring error.
        r['borderline'] = sorted(d for d, v in scores.items()
                                 if any(abs(v - t) < 5 for t in (WARNING, CRITICAL)))
        return r

    @staticmethod
    def report(name: str, r: Dict[str, Any]) -> str:
        if r['verdict'] == 'INVALID_SCORES':
            return f"{name}: INVALID INPUT — {', '.join(r['errors'])}"
        label = {
            'KILLED_CRITICAL_DIMENSION': 'KILLED by an evidenced critical weakness',
            'KILLED_FATAL_ASSUMPTION': 'KILLED by an unproven fatal assumption',
            'KILLED': 'KILLED by overall risk',
            'HOLD_PRECEDENT_APPEAL': 'ON HOLD: a historical success survived this risk',
            'HOLD_CRITICAL_UNEVIDENCED': 'ON HOLD: critical risk without evidence',
            'CRITICAL_REPAIR_REQUIRED': 'CRITICAL REPAIR required before investing',
            'SURVIVES_WITH_MAJOR_RISK': 'SURVIVES, with major risks',
            'SURVIVES_KILL_TEST': 'SURVIVES the kill test (not market validation)',
            'UNKNOWN_TOO_MANY_GAPS': 'UNKNOWN: too many dimensions missing',
            'UNKNOWN': 'UNKNOWN: no dimension was scored',
            'HOLD_UNSCORED_DIMENSIONS': 'ON HOLD: cannot survive with unscored dimensions',
        }.get(r['verdict'], r['verdict'])
        lines = [f"■ {name}: {label}  [average risk {r.get('risk_score')}]"]
        if r.get('killed_by'):
            lines.append('  Critical weakness: ' + ', '.join(r['killed_by']))
        if r.get('appeal'):
            a = r['appeal']
            lines.append(f"  Appeal: {a['precedent']} survived {', '.join(a['dimensions'])}. You must prove: {a['required_lever']}")
        if r.get('required'):
            lines.append('  ' + r['required'])
        if r.get('repair'):
            lines.append('  Repair first: ' + ', '.join(r['repair']))
        if r.get('borderline'):
            lines.append('  Borderline verdict (within 5 points of a threshold, research more): ' + ', '.join(r['borderline']))
        for p in r.get('precedents', []):
            extra = f"Saved by: {p['lever']}" if p['outcome'] == 'SUCCESS' else f"Died of: {p['cause']}"
            lines.append(f"  Resembles {p['name']} ({p['year']}, {p['outcome']}, similarity {p['similarity']}). {extra}")
        return '\n'.join(lines)


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[1], encoding='utf-8') as fh:
        data = json.load(fh)
    db = Dreambreaker()
    # Never fill missing dimensions silently: unscored dimensions must stay visible to the engine.
    r = db.evaluate(data.get('scores', {}), data.get('evidence', {}), data.get('fatal_assumptions', 0))
    print(db.report(data.get('idea', 'Idea'), r))
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
