"""5.0 模型选类契约：这些测试验证模型输出的承接，不声称测试了模型理解能力。"""
import unittest
from copy import deepcopy
from pathlib import Path
from scripts.role_match import ROLES, ROLE_BY_CODE
from scripts.finalize_report import finalize_report
from scripts.validate_report import ReportValidationError, assert_valid_report
from tests.sample_factory import valid_draft

class SemanticRoleContractTest(unittest.TestCase):
    def test_all_twelve_model_choices_survive_finalization(self):
        for role in ROLES:
            d=valid_draft(); d['profile']['role']['code']=role['code']
            r=finalize_report(d)
            self.assertEqual(r['profile']['role']['code'],role['code'])
            self.assertEqual(r['profile']['role']['name'],role['name'])
            self.assertEqual(r['profile']['role']['reason'],d['profile']['role']['reason'])
            assert_valid_report(r)
            self.assertTrue((Path(__file__).resolve().parents[1]/'assets/characters'/role['asset']).is_file())
        self.assertEqual(len(ROLES),12)

    def test_rephrasing_signals_and_weights_do_not_override_model_choice(self):
        d=valid_draft(); before=finalize_report(d)['profile']['role']
        for t in d['tasks']:
            t['task_name']='与旧词表完全不同的表述';t['evidence']='按实际环境完成工作。'
            t['signals']={k:0 for k in t['signals']};t['time_share_percent']=None
        self.assertEqual(finalize_report(d)['profile']['role'],before)

    def test_unknown_index_still_has_selected_role(self):
        d=valid_draft();d['profile']['role']['confidence']='LOW'
        for t in d['tasks']: t['exposure_level']='UNKNOWN';t['time_share_percent']=None
        r=finalize_report(d)
        self.assertIsNone(r['metrics']['irreplaceability_index'])
        self.assertEqual(r['profile']['role']['code'],'MINESWEEPER_WORKER')
        self.assertEqual(r['share_card']['confidence_label'],'暂按现有描述归类')

    def test_no_role_scoring_metadata(self):
        r=finalize_report(valid_draft())
        self.assertNotIn('is_role_sufficient_info',r['report_metadata'])
        self.assertNotIn('task_count_role_evaluable',r['metrics'])
        self.assertTrue(all('role_codes' not in t for t in r['tasks']))

    def test_missing_or_shadow_role_requires_model_reanalysis(self):
        for change in ({'code':'SHADOW_WORKER'},{'code':'NO_SUCH_ROLE'},{'reason':''},{'source_task_ids':[]}):
            d=valid_draft();d['profile']['role'].update(change)
            with self.assertRaisesRegex(ReportValidationError,'ROLE_REANALYSIS_REQUIRED'):finalize_report(d)

    def test_invalid_reason_confidence_and_refs_are_rejected(self):
        for change in ({'reason':' '},{'confidence':'CERTAIN'},{'source_task_ids':['missing']},{'source_task_ids':['task-launch-decision']*2}):
            d=valid_draft();d['profile']['role'].update(change)
            with self.assertRaises(ReportValidationError):finalize_report(d)

    def test_input_not_mutated_and_finalization_repeatable(self):
        d=valid_draft();old=deepcopy(d)
        first=finalize_report(d)
        self.assertEqual(d,old)
        self.assertEqual(first,finalize_report(d))
