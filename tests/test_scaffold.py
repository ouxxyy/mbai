import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTest(unittest.TestCase):
    def test_frozen_contract_files_exist_and_are_parseable(self):
        schema_path = ROOT / "references" / "report-contract.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["schema_version"]["const"], "2.0.0")
        self.assertEqual(schema["properties"]["rule_version"]["const"], "2.0.0")
        self.assertEqual(len(schema["properties"]["profile"]["properties"]["role"]["properties"]["code"]["enum"]), 13)
        self.assertTrue((ROOT / "docs" / "MIGRATION_NOTES.md").is_file())
        self.assertTrue((ROOT / "docs" / "SCORING_RULES.md").is_file())
        self.assertTrue((ROOT / "docs" / "INTERFACE_CONTRACT.md").is_file())
        self.assertTrue((ROOT / "docs" / "SOURCES.md").is_file())


class ActionDeadlineWordingTest(unittest.TestCase):
    """冻结规则 9 的行动口径在全部生成契约文档中保持一致，防止回退成"7 天内完成"。"""

    def test_proof_action_wording_matches_frozen_rule_9_everywhere(self):
        sources = {
            "SCORING_RULES §7": (ROOT / "docs" / "SCORING_RULES.md").read_text(encoding="utf-8"),
            "SKILL.md": (ROOT / "SKILL.md").read_text(encoding="utf-8"),
            "content-baseline": (ROOT / "references" / "content-baseline.md").read_text(encoding="utf-8"),
        }
        for name, text in sources.items():
            self.assertIn("7 天内可启动", text, name)
            self.assertIn("观察窗", text, name)
            self.assertIn("第 7 天", text, name)
            self.assertNotIn("7 天内完成的求职作品", text, name)


if __name__ == "__main__":
    unittest.main()
