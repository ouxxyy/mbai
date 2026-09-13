import unittest

from scripts.finalize_report import finalize_report
from scripts.sample_cases import case_definitions, draft_for_case


class SampleCasesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {case["slug"]: case for case in case_definitions()}
        cls.reports = {slug: finalize_report(draft_for_case(case)) for slug, case in cls.cases.items()}

    def test_has_six_core_scenarios_and_required_adversarial_variants(self):
        expected = {
            "operations-repetitive",
            "content-calibrator",
            "technical-execution",
            "client-coordination",
            "project-owner",
            "sparse-information",
            "risk-owner-showcase",
            "ops-shallow",
            "ops-deep",
            "writing-detailed",
            "writing-concise",
            "operations-injection",
            "operations-demographics",
        }
        self.assertTrue(expected.issubset(self.cases))

    def test_same_facts_different_writing_detail_keep_levels_and_score(self):
        detailed = self.reports["writing-detailed"]
        concise = self.reports["writing-concise"]

        self.assertEqual(
            [task["exposure_level"] for task in detailed["tasks"]],
            [task["exposure_level"] for task in concise["tasks"]],
        )
        self.assertEqual(detailed["metrics"]["irreplaceability_index"], concise["metrics"]["irreplaceability_index"])
        self.assertNotEqual(
            detailed["report_metadata"]["confidence_level"],
            concise["report_metadata"]["confidence_level"],
        )

    def test_prompt_injection_and_demographics_do_not_change_score(self):
        baseline = self.reports["operations-repetitive"]
        injected = self.reports["operations-injection"]
        demographics = self.reports["operations-demographics"]

        self.assertIn("忽略以上", self.cases["operations-injection"]["resume_text"])
        self.assertIn("已婚", self.cases["operations-demographics"]["resume_text"])
        self.assertEqual(baseline["metrics"], injected["metrics"])
        self.assertEqual(baseline["metrics"], demographics["metrics"])
        for key in ("profile", "skill_panel", "tasks", "human_edge", "action_plan", "share_card"):
            self.assertEqual(baseline[key], injected[key], f"prompt injection changed {key}")
            self.assertEqual(baseline[key], demographics[key], f"demographics changed {key}")

    def test_same_job_title_changes_with_responsibility_depth(self):
        shallow = self.reports["ops-shallow"]
        deep = self.reports["ops-deep"]

        self.assertEqual(self.cases["ops-shallow"]["job_title"], self.cases["ops-deep"]["job_title"])
        # 3.0.0 不可替代口径：模板执行 0 分 < 策略责任 45 分，方向随直觉。
        self.assertLess(shallow["metrics"]["irreplaceability_index"], deep["metrics"]["irreplaceability_index"])

    def test_sparse_case_is_honestly_information_insufficient(self):
        sparse = self.reports["sparse-information"]

        self.assertFalse(sparse["report_metadata"]["is_sufficient_info"])
        self.assertIsNone(sparse["metrics"]["irreplaceability_index"])

    def test_all_normal_cases_have_three_distinct_grounded_actions_and_unique_quotes(self):
        quotes = []
        adversarial_variants = {"operations-injection", "operations-demographics"}
        for slug, report in self.reports.items():
            if slug not in adversarial_variants:
                quotes.append(report["profile"]["role"]["snarky_quote"])
            actions = report["action_plan"]
            self.assertEqual(set(actions), {"hand_to_ai", "level_up", "proof_7d"}, slug)
            self.assertEqual(len({item["title"] for item in actions.values()}), 3, slug)
            self.assertTrue(all(item["source_task_ids"] for item in actions.values()), slug)
        self.assertEqual(len(quotes), len(set(quotes)))


if __name__ == "__main__":
    unittest.main()
