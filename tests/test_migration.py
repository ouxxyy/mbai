"""Migration tests: 1.0.0 → 2.0.0 legacy roles, index invariance, dual-threshold rewrite."""

import unittest

from scripts.finalize_report import finalize_report
from scripts.migrate_report import migrate_report
from scripts.role_match import LEGACY_ROLE_MIGRATION
from scripts.sample_cases import case_definitions, draft_for_case
from scripts.validate_report import ReportValidationError, assert_valid_report
from tests.sample_factory import valid_draft


class LegacyDraftMigrationTest(unittest.TestCase):
    def test_legacy_draft_is_migrated_at_read_time_with_index_untouched(self):
        draft = valid_draft()  # 1.0.0 fixture with PROJECT_RISK_NAVIGATOR
        legacy_index_draft = draft["tasks"]

        report = finalize_report(draft)

        assert_valid_report(report)
        self.assertEqual(report["schema_version"], "2.0.0")
        self.assertEqual(report["rule_version"], "2.0.0")
        self.assertIn(report["profile"]["role"]["code"], ROLE_NAMES_OK)
        # 指数字段语义未动：等级逐一保留。
        for old, new in zip(legacy_index_draft, report["tasks"]):
            self.assertEqual(old["exposure_level"], new["exposure_level"])

    def test_unknown_schema_version_is_rejected(self):
        draft = valid_draft()
        draft["schema_version"] = "0.9.0"

        with self.assertRaises(ReportValidationError):
            finalize_report(draft)


ROLE_NAMES_OK = {
    "TABLE_GOBLIN", "INSPECTOR_BOT", "PROOFREADER_OWL", "ASSEMBLY_CRANE", "ROOTCAUSE_HOUND",
    "GATEKEEPER_BEAR", "TRANSLATOR_FOX", "DECONSTRUCTOR_BEAVER", "PROGRESS_HERDER",
    "MINESWEEPER_MOLE", "SOLVER_OTTER", "ONSCENE_CHAMELEON", "SHADOW_BEAST",
}


class LegacyRoleMappingTest(unittest.TestCase):
    def test_sample_case_roles_stay_inside_frozen_migration_candidates(self):
        legacy_code_by_slug = {
            "operations-repetitive": "FLOW_ORCHESTRATOR",
            "content-calibrator": "CONTENT_CALIBRATOR",
            "technical-execution": "SYSTEM_BOUNDARY_GUARD",
            "client-coordination": "COORDINATION_TRANSLATOR",
            "project-owner": "PROJECT_RISK_NAVIGATOR",
            "sparse-information": "LOCKED_ROLE",
        }
        cases = {case["slug"]: case for case in case_definitions()}
        for slug, legacy_code in legacy_code_by_slug.items():
            with self.subTest(slug=slug):
                report = finalize_report(draft_for_case(cases[slug]))
                new_code = report["profile"]["role"]["code"]
                self.assertIn(
                    new_code,
                    LEGACY_ROLE_MIGRATION[legacy_code],
                    f"{legacy_code} → {new_code} 超出冻结版候选映射",
                )

    def test_legacy_role_codes_are_gone_from_the_contract(self):
        report = finalize_report(valid_draft())
        self.assertNotIn(report["profile"]["role"]["code"], LEGACY_ROLE_MIGRATION)


class FinalReportMigrationTest(unittest.TestCase):
    def test_migrate_final_report_keeps_index_and_level_identical(self):
        old_final = finalize_report(valid_draft())
        old_final["schema_version"] = "1.0.0"
        old_final["rule_version"] = "1.0.0"
        # 还原 1.0.0 final 形态：没有角色命中与双门槛字段。
        for task in old_final["tasks"]:
            task.pop("role_codes", None)
        old_final["metrics"].pop("task_count_role_evaluable", None)
        old_final["report_metadata"].pop("is_role_sufficient_info", None)
        old_final["profile"]["role"] = {
            "code": "PROJECT_RISK_NAVIGATOR",
            "name": "项目风险领航员",
            "tags": ["结果兜底", "跨团队协调"],
            "source_task_ids": ["task-weekly-report", "task-launch-decision"],
            "snarky_quote": "周报可以自动写，真正不能一键生成的是上线那晚谁来拍板。",
        }

        migrated = migrate_report(old_final)

        assert_valid_report(migrated)
        self.assertEqual(migrated["schema_version"], "2.0.0")
        self.assertEqual(migrated["metrics"]["exposure_index"], old_final["metrics"]["exposure_index"])
        self.assertEqual(migrated["metrics"]["exposure_level"], old_final["metrics"]["exposure_level"])
        self.assertEqual(migrated["metrics"]["raw_score"], old_final["metrics"]["raw_score"])
        for old, new in zip(old_final["tasks"], migrated["tasks"]):
            self.assertEqual(old["exposure_level"], new["exposure_level"])
            self.assertEqual(old["score"], new["score"])

    def test_migrate_rejects_non_1_0_0_input(self):
        report = finalize_report(valid_draft())

        with self.assertRaisesRegex(ValueError, "1.0.0"):
            migrate_report(report)


if __name__ == "__main__":
    unittest.main()
