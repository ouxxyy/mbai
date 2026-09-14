"""取代 4.1 词表命中测试：确保生产链路没有词表回退。"""
import unittest
from scripts.role_match import ROLES
from scripts.finalize_report import finalize_report
from scripts.sample_cases import case_definitions, draft_for_case

class SemanticClassificationRegressionTest(unittest.TestCase):
    def test_directory_has_definitions_without_predicate_tables(self):
        for r in ROLES:
            self.assertTrue(r['description'])
            self.assertFalse({'verbs','objects','signals','or_signals'} & r.keys())

    def test_previous_unmatched_cases_now_keep_explicit_model_choice(self):
        cases={c['slug']:c for c in case_definitions()}
        for slug,code in [('ops-deep','MINESWEEPER_WORKER'),('sparse-information','TRANSLATOR_WORKER'),('knowledge-flow-builder','DECONSTRUCTOR_WORKER')]:
            r=finalize_report(draft_for_case(cases[slug]))
            self.assertEqual(r['profile']['role']['code'],code)
