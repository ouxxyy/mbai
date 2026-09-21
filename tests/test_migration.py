"""Migration tests: 历史版本 → 当前契约迁移、翻转保持、防双翻、读时兼容。"""

import unittest

from scripts.finalize_report import finalize_report
from scripts.migrate_report import migrate_report
from scripts.role_match import LEGACY_ROLE_MIGRATION
from scripts.sample_cases import case_definitions, draft_for_case
from scripts.version import SCHEMA_VERSION, RULE_VERSION
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
        self.assertEqual(report["schema_version"], SCHEMA_VERSION)
        self.assertEqual(report["rule_version"], RULE_VERSION)
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

        self.assertEqual(report["schema_version"], SCHEMA_VERSION)
        self.assertEqual(report["metrics"]["irreplaceability_index"], 40)

    def test_unknown_schema_version_is_rejected(self):
        draft = valid_draft()
        draft["schema_version"] = "0.9.0"

        with self.assertRaises(ReportValidationError):
            finalize_report(draft)


class LegacyRoleMappingTest(unittest.TestCase):
    def test_old_role_without_semantic_evidence_requires_reanalysis(self):
        draft = valid_draft()
        draft["schema_version"] = "4.0.0"
        draft["profile"]["role"].pop("reason")
        with self.assertRaisesRegex(ReportValidationError, "ROLE_REANALYSIS_REQUIRED"):
            finalize_report(draft)

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
        self.assertEqual(migrated["schema_version"], SCHEMA_VERSION)
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


def _final_current_stamp_as_5_0_0() -> dict:
    """构造一份 5.0.0 印记的 final 报告（内容取当前技术案例）。"""
    cases = {case["slug"]: case for case in case_definitions()}
    final = finalize_report(draft_for_case(cases["technical-execution"]))
    final["schema_version"] = "5.0.0"
    final["rule_version"] = "5.0.0"
    return final


class Migration5_0_0Test(unittest.TestCase):
    """5.0.0 → 5.1.0：内容基线改版的无损迁移（ADR 0001/0002）。"""

    def test_migrate_5_0_0_keeps_anchor_content_and_old_action_titles(self):
        import json as _json

        old = _final_current_stamp_as_5_0_0()
        snapshot = _json.dumps(old, ensure_ascii=False, sort_keys=True)

        migrated = migrate_report(old)

        assert_valid_report(migrated)
        self.assertEqual(migrated["schema_version"], SCHEMA_VERSION)
        self.assertEqual(migrated["rule_version"], RULE_VERSION)
        # 回归锚点：等级与权重不变，指数仍为 50（先取整后取补）。
        self.assertEqual(migrated["metrics"]["raw_score"], 47.5)
        self.assertEqual(migrated["metrics"]["irreplaceability_index"], 50)
        self.assertEqual(migrated["metrics"]["irreplaceability_level"], "MEDIUM")
        # 无损：处境结论、优势边界与三个行动文案逐字保留（ADR 0002：旧建议不回写新名）。
        self.assertEqual(old["action_plan"], migrated["action_plan"])
        self.assertEqual(old["profile"]["situation_paragraph"], migrated["profile"]["situation_paragraph"])
        self.assertEqual(old["human_edge"], migrated["human_edge"])
        self.assertEqual(old["share_card"]["value_line"], migrated["share_card"]["value_line"])
        for old_task, new_task in zip(old["tasks"], migrated["tasks"]):
            self.assertEqual(old_task["exposure_level"], new_task["exposure_level"])
            self.assertEqual(old_task["score"], new_task["score"])
            self.assertEqual(old_task["effective_weight"], new_task["effective_weight"])
        # 不覆盖原件：入参对象未被迁移过程改动。
        self.assertEqual(_json.dumps(old, ensure_ascii=False, sort_keys=True), snapshot)

    def test_current_5_1_0_report_refuses_remigration(self):
        final = finalize_report(draft_for_case({case["slug"]: case for case in case_definitions()}["technical-execution"]))
        with self.assertRaisesRegex(ValueError, "迁移"):
            migrate_report(final)
