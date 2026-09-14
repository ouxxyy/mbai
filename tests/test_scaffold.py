import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTest(unittest.TestCase):
    def test_frozen_contract_files_exist_and_are_parseable(self):
        schema_path = ROOT / "references" / "report-contract.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["schema_version"]["const"], "5.0.0")
        from scripts.version import RULE_VERSION as _RULE
        self.assertEqual(schema["properties"]["rule_version"]["const"], _RULE)
        self.assertIn("irreplaceability_index", schema["properties"]["metrics"]["required"])
        self.assertIn("irreplaceability_level", schema["properties"]["metrics"]["required"])
        self.assertIn("irreplaceability_index", schema["properties"]["share_card"]["required"])
        self.assertNotIn("exposure_index", schema["properties"]["metrics"]["required"])
        self.assertIn("raw_score", schema["properties"]["metrics"]["required"])
        self.assertEqual(len(schema["properties"]["profile"]["properties"]["role"]["properties"]["code"]["enum"]), 12)
        self.assertTrue((ROOT / "docs" / "MIGRATION_NOTES.md").is_file())
        self.assertTrue((ROOT / "docs" / "SCORING_RULES.md").is_file())
        self.assertTrue((ROOT / "docs" / "INTERFACE_CONTRACT.md").is_file())
        self.assertTrue((ROOT / "docs" / "SOURCES.md").is_file())


class IrreplaceabilityNamingContractTest(unittest.TestCase):
    """3.0.0 命名与方向词契约：三份生成文档一致，旧方向词按 scope 禁止回退。"""

    def test_generation_docs_use_irreplaceability_naming(self):
        sources = {
            "SKILL.md": (ROOT / "SKILL.md").read_text(encoding="utf-8"),
            "SCORING_RULES": (ROOT / "docs" / "SCORING_RULES.md").read_text(encoding="utf-8"),
            "content-baseline": (ROOT / "references" / "content-baseline.md").read_text(encoding="utf-8"),
            "README": (ROOT / "README.md").read_text(encoding="utf-8"),
            "AGENTS.md": (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
        }
        for name, text in sources.items():
            self.assertIn("不可替代指数", text, name)
            self.assertIn("先取整、后取补", text, name)

    def test_old_direction_words_are_banned_where_scope_requires(self):
        # 生成入口与基线不得再以「AI 替代指数」作为产品名或角落声明（防 A7 回退）。
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        baseline = (ROOT / "references" / "content-baseline.md").read_text(encoding="utf-8")
        agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for name, text in (("SKILL.md", skill), ("content-baseline", baseline)):
            self.assertNotIn("替代指数量的是任务", text, name)
            self.assertNotIn("工作任务 AI 替代指数", text, name)
        # AGENTS.md 由宿主每个会话自动加载，是产品名契约面的一部分：旧称必须被拦截。
        self.assertNotIn("工作任务 AI 替代指数", agents_md, "AGENTS.md")
        # 展示锚点必须已是翻转后数值。
        for name, text in (("SKILL.md", skill), ("content-baseline", baseline)):
            self.assertNotIn("87.5→90、85→85、92.5→95", text, name)
            self.assertIn("87.5→10", text, name)


class DesignSystemCtaDivisionTest(unittest.TestCase):
    """B1 收口（欧八 2026-09-13 授权）：分享卡角落 CTA 与 HTML 指标解释分层承担。"""

    def test_design_system_no_longer_demands_same_copy_across_page_and_card(self):
        design = (ROOT / "docs" / "DESIGN_SYSTEM_B_POSTER.md").read_text(encoding="utf-8")
        self.assertNotIn("在首屏、折叠区与分享卡显要位置常态化出现固定声明", design)
        self.assertIn("搜 欧八同学 生成自己的职业AI体检报告", design)
        self.assertIn("分数越高，当前工作越依赖人的判断、协作或现场处理", design)


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
