"""Migration tests: 1.0.0/2.0.0/3.0.0 → 4.0.0 迁移、翻转保持、防双翻、读时兼容。"""

import unittest

from scripts.finalize_report import finalize_report
from scripts.migrate_report import migrate_report
from scripts.role_match import LEGACY_ROLE_MIGRATION
from scripts.sample_cases import case_definitions, draft_for_case
from scripts.validate_report import ReportValidationError, assert_valid_report
from tests.sample_factory import valid_draft


ROLE_NAMES_OK = {
    "TABLE_WORKER", "INSPECTOR_WORKER", "PROOFREADER_WORKER", "ASSEMBLY_WORKER", "ROOTCAUSE_WORKER",
    "GATEKEEPER_WORKER", "TRANSLATOR_WORKER", "DECONSTRUCTOR_WORKER", "PROGRESS_WORKER",
    "MINESWEEPER_WORKER", "SOLVER_WORKER", "ONSCENE_WORKER", "SHADOW_WORKER",
}


class LegacyDraftMigrationTest(unittest.TestCase):
    def test_legacy_draft_is_migrated_at_read_time_with_flip(self):
        draft = valid_draft()  # 1.0.0 fixture with PROJECT_RISK_NAVIGATOR
        legacy_tasks = draft["tasks"]

        report = finalize_report(draft)

        assert_valid_report(report)
        self.assertEqual(report["schema_version"], "4.0.0")
        self.assertEqual(report["rule_version"], "4.1.0")
        self.assertIn(report["profile"]["role"]["code"], ROLE_NAMES_OK)
        # 任务级替代语义逐字段保留；raw_score 是翻转前的锚。
        for old, new in zip(legacy_tasks, report["tasks"]):
            self.assertEqual(old["exposure_level"], new["exposure_level"])
        self.assertEqual(report["metrics"]["raw_score"], 60)
        self.assertEqual(report["metrics"]["irreplaceability_index"], 40)

    def test_2_0_0_draft_is_accepted_and_flips_once(self):
        draft = valid_draft()
        draft["schema_version"] = "2.0.0"
        draft["rule_version"] = "2.0.0"

        report = finalize_report(draft)

        self.assertEqual(report["schema_version"], "4.0.0")
        self.assertEqual(report["metrics"]["irreplaceability_index"], 40)

    def test_unknown_schema_version_is_rejected(self):
        draft = valid_draft()
        draft["schema_version"] = "0.9.0"

        with self.assertRaises(ReportValidationError):
            finalize_report(draft)


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


def _final_2_0_0() -> dict:
    """构造一份 2.0.0 形态的旧 final 报告（替代口径 90/HIGH）。"""
    cases = {case["slug"]: case for case in case_definitions()}
    final = finalize_report(draft_for_case(cases["operations-repetitive"]))
    final["schema_version"] = "2.0.0"
    final["rule_version"] = "2.0.0"
    # 还原 2.0.0 字段形态：irreplaceability_* → exposure_*（替代语义值）。
    metrics = final["metrics"]
    metrics["exposure_index"] = 90
    metrics["exposure_level"] = "HIGH"
    for key in ("irreplaceability_index", "irreplaceability_level"):
        metrics.pop(key)
    share = final["share_card"]
    share["exposure_index"] = 90
    share["exposure_level"] = "HIGH"
    for key in ("irreplaceability_index", "irreplaceability_level"):
        share.pop(key)
    return final


class FinalReportMigrationTest(unittest.TestCase):
    def test_migrate_2_0_0_final_flips_display_and_keeps_raw(self):
        old_final = _final_2_0_0()

        migrated = migrate_report(old_final)

        assert_valid_report(migrated)
        self.assertEqual(migrated["schema_version"], "4.0.0")
        # 产品决策（非回归）：旧 90/HIGH 展示为 10/LOW；raw_score 与任务等级逐字段保留。
        self.assertEqual(migrated["metrics"]["irreplaceability_index"], 10)
        self.assertEqual(migrated["metrics"]["irreplaceability_level"], "LOW")
        self.assertEqual(migrated["metrics"]["raw_score"], 87.5)
        self.assertEqual(migrated["share_card"]["irreplaceability_index"], 10)
        for old, new in zip(old_final["tasks"], migrated["tasks"]):
            self.assertEqual(old["exposure_level"], new["exposure_level"])
            self.assertEqual(old["score"], new["score"])

    def test_migrating_a_3_0_0_report_is_rejected_as_double_flip(self):
        old_final = _final_2_0_0()
        migrated = migrate_report(old_final)

        with self.assertRaisesRegex(ValueError, "双翻"):
            migrate_report(migrated)

    def test_migrate_rejects_unsupported_version(self):
        report = finalize_report(valid_draft())
        report["schema_version"] = "9.9.9"

        with self.assertRaisesRegex(ValueError, "仅迁移"):
            migrate_report(report)


if __name__ == "__main__":
    unittest.main()
