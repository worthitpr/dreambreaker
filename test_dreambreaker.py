# Copyright 2026 Kritsia Quiñones (XXSELENEPRXX). Licensed under the Apache License, Version 2.0.
"""DREAMBREAKER tests. Run: python3 test_dreambreaker.py"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dreambreaker_core import Dreambreaker as Core, KILL_DIMENSIONS as K
from dreambreaker import Dreambreaker

DB = Dreambreaker()


def profile(base=30, **over):
    s = {d: base for d in K}
    s.update(over)
    return s


def refs(scores):
    return {d: ['ref'] for d in scores}


def case(case_id):
    c = next(c for c in DB.graveyard['cases'] if c['id'] == case_id)
    return {**{d: 40 for d in K}, **c['risks']}


class WeakestLink(unittest.TestCase):
    def test_pure_average_hides_fatal_flaw(self):
        self.assertEqual(Core().kill_score(profile(substitutes=100))['verdict'], 'SURVIVES_KILL_TEST')

    def test_evidenced_critical_weakness_kills(self):
        s = profile(substitutes=100)
        self.assertEqual(DB.kill_score(s, evidence_refs=refs(s))['verdict'], 'KILLED_CRITICAL_DIMENSION')

    def test_unevidenced_critical_weakness_holds(self):
        self.assertEqual(DB.kill_score(profile(substitutes=100))['verdict'], 'HOLD_CRITICAL_UNEVIDENCED')

    def test_warning_requires_repair(self):
        s = profile(unit_economics=85)
        self.assertEqual(DB.kill_score(s, evidence_refs=refs(s))['verdict'], 'CRITICAL_REPAIR_REQUIRED')

    def test_healthy_idea_survives(self):
        s = profile(25)
        self.assertEqual(DB.kill_score(s, evidence_refs=refs(s))['verdict'], 'SURVIVES_KILL_TEST')

    def test_fatal_assumption_still_rules(self):
        s = profile(25)
        self.assertEqual(DB.kill_score(s, 1, evidence_refs=refs(s))['verdict'], 'KILLED_FATAL_ASSUMPTION')

    def test_high_average_still_kills(self):
        s = profile(85)
        self.assertEqual(DB.kill_score(s, evidence_refs=refs(s))['verdict'], 'KILLED')

    def test_average_verdict_reported(self):
        s = profile(substitutes=100)
        self.assertEqual(DB.kill_score(s, evidence_refs=refs(s))['average_verdict'], 'SURVIVES_KILL_TEST')


class HostileInput(unittest.TestCase):
    def check(self, s):
        self.assertEqual(DB.evaluate(s)['verdict'], 'INVALID_SCORES')

    def test_nan(self): self.check(profile(substitutes=float('nan')))
    def test_infinity(self): self.check(profile(substitutes=float('inf')))
    def test_text(self): self.check(profile(substitutes='95'))
    def test_boolean(self): self.check(profile(substitutes=True))
    def test_negative(self): self.check(profile(substitutes=-5))
    def test_above_100(self): self.check(profile(substitutes=150))
    def test_unknown_dimension(self): self.check({**profile(), 'vibes': 10})
    def test_not_an_object(self): self.check([1, 2, 3])

    def test_core_alone_misses_nan(self):
        self.assertIsNotNone(Core().kill_score(profile(substitutes=float('nan')))['risk_score'])


class AntiGaming(unittest.TestCase):
    """Regression tests for the ways the stress test found to cheat the engine."""

    def test_blank_evidence_is_not_evidence(self):
        s = profile(substitutes=95)
        for fake in ([''], ['   '], [None], 'text', [], {'a': 1}):
            self.assertEqual(DB.evaluate(s, {'substitutes': fake})['verdict'], 'HOLD_CRITICAL_UNEVIDENCED', fake)

    def test_evidence_not_a_dict(self):
        s = profile(substitutes=95)
        self.assertEqual(DB.evaluate(s, ['substitutes'])['verdict'], 'HOLD_CRITICAL_UNEVIDENCED')

    def test_cannot_survive_by_omitting_dimensions(self):
        s = {d: 30 for d in K if d != 'substitutes'}
        r = DB.evaluate(s, refs(s))
        self.assertEqual(r['verdict'], 'HOLD_UNSCORED_DIMENSIONS')
        self.assertIn('substitutes', r['required'])

    def test_negative_fatal_assumptions_rejected(self):
        s = profile(25)
        self.assertEqual(DB.evaluate(s, refs(s), fatal_assumptions=-5)['verdict'], 'INVALID_SCORES')

    def test_text_fatal_assumptions_rejected_without_crash(self):
        s = profile(25)
        self.assertEqual(DB.evaluate(s, refs(s), fatal_assumptions='1')['verdict'], 'INVALID_SCORES')

    def test_inflating_risk_cannot_buy_an_appeal(self):
        s = case('uber')
        s['regulatory'] = 100
        self.assertEqual(DB.evaluate(s, refs(s))['verdict'], 'KILLED_CRITICAL_DIMENSION')

    def test_empty_scores_are_unknown(self):
        self.assertEqual(DB.evaluate({}, {})['verdict'], 'UNKNOWN')

    def test_cli_does_not_fill_missing_dimensions(self):
        import io, json, tempfile, contextlib
        from dreambreaker import main
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as t:
            json.dump({'idea': 'x', 'scores': {'problem_reality': 10}}, t)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(['x', t.name])
        os.unlink(t.name)
        self.assertNotIn('SURVIVES', buf.getvalue().splitlines()[0])

    def test_malformed_graveyards_fail_clearly(self):
        bad = [{}, {'cases': 'x'}, {'cases': [1]}, {'cases': [{'id': 'a', 'risks': {}}]},
               {'cases': [{'id': 'a', 'name': 'a', 'year': 1, 'outcome': 'SUCCESS', 'cause': 'c', 'risks': {'substitutes': '90'}, 'lever': 'l'}]},
               {'cases': [{'id': 'a', 'name': 'a', 'year': 1, 'outcome': 'MAYBE', 'cause': 'c', 'risks': {}}]},
               {'cases': [{'id': 'a', 'name': 'a', 'year': 1, 'outcome': 'SUCCESS', 'cause': 'c', 'risks': {}}]},
               {'default_risk': 500, 'cases': []}]
        for g in bad:
            with self.assertRaises(ValueError, msg=str(g)):
                Dreambreaker(graveyard=g)


class Graveyard(unittest.TestCase):
    def test_graveyard_is_valid(self):
        cases = DB.graveyard['cases']
        self.assertGreaterEqual(len(cases), 20)
        self.assertEqual(len({c['id'] for c in cases}), len(cases))
        for c in cases:
            self.assertIn(c['outcome'], ('FAILURE', 'SUCCESS'))
            if c['outcome'] == 'SUCCESS':
                self.assertTrue(c.get('lever'))

    def test_bad_graveyard_rejected(self):
        with self.assertRaises(ValueError):
            Dreambreaker(graveyard={'cases': [{'id': 'x', 'risks': {'magic': 90}}]})

    def test_clone_matches_itself(self):
        self.assertEqual(DB.precedents(case('juicero'), 1)[0]['id'], 'juicero')

    def test_precedent_appeal(self):
        s = case('uber')
        r = DB.evaluate(s, refs(s))
        self.assertEqual(r['verdict'], 'HOLD_PRECEDENT_APPEAL')
        self.assertIn('demand', r['appeal']['required_lever'])

    def test_appeal_needs_all_critical_dimensions(self):
        s = case('theranos')
        r = DB.evaluate(s, refs(s), exclude='theranos')
        self.assertTrue(r['verdict'].startswith('KILLED'), r['verdict'])

    def test_deterministic(self):
        s = profile(substitutes=92, unit_economics=81)
        self.assertEqual(DB.evaluate(s, refs(s)), DB.evaluate(s, refs(s)))

    def test_borderline_flagged(self):
        s = profile(onboarding_friction=80)
        r = DB.evaluate(s, refs(s))
        self.assertEqual(r['borderline'], ['onboarding_friction'])
        self.assertIn('Borderline', DB.report('Test', r))

    def test_clear_scores_not_borderline(self):
        s = profile(25)
        self.assertEqual(DB.evaluate(s, refs(s))['borderline'], [])

    def test_shipped_example_gives_a_real_verdict(self):
        import io, json, contextlib
        from dreambreaker import main
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'example_input.json')
        data = json.load(open(path, encoding='utf-8'))
        self.assertEqual(set(data['scores']), set(K))  # the example must score all 24 dimensions
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(['x', path])
        self.assertIn('KILLED by an evidenced critical weakness', buf.getvalue().splitlines()[0])

    def test_readable_report(self):
        s = profile(substitutes=95)
        self.assertIn('Resembles', DB.report('Test', DB.evaluate(s, refs(s))))


if __name__ == '__main__':
    unittest.main(verbosity=2)
