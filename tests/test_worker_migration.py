"""4.0.0 工系迁移契约：清野清扫、工牌码与品牌露出、三层迁移链、素材文件契约。"""

import json
import re
import unittest
from pathlib import Path

from scripts.finalize_report import finalize_report
from scripts.migrate_report import migrate_report
from scripts.render_report import render_report
from scripts.role_match import BEAST_TO_WORKER, ROLES, ROLE_BY_CODE
from scripts.sample_cases import case_definitions, draft_for_case
from scripts.validate_report import assert_valid_report
from tests.sample_factory import valid_draft

ROOT = Path(__file__).resolve().parents[1]

OLD_CODE_PATTERN = re.compile(
    r"TABLE_GOBLIN|INSPECTOR_BOT|PROOFREADER_OWL|ASSEMBLY_CRANE|ROOTCAUSE_HOUND|"
    r"GATEKEEPER_BEAR|TRANSLATOR_FOX|DECONSTRUCTOR_BEAVER|PROGRESS_HERDER|"
    r"MINESWEEPER_MOLE|SOLVER_OTTER|ONSCENE_CHAMELEON|SHADOW_BEAST"
)

# 用户可见面（生成、渲染、交付、文档契约）；历史记录容身处按 analyst 清野口径排除。
SWEEP_FILES = [
    "SKILL.md",
    "README.md",
    "INSTALL.md",
    "AGENTS.md",
    "docs/SCORING_RULES.md",
    "docs/INTERFACE_CONTRACT.md",
    "docs/DESIGN_SYSTEM_B_POSTER.md",
    "references/content-baseline.md",
    "references/report-contract.schema.json",
    "scripts/finalize_report.py",
    "scripts/validate_report.py",
    "scripts/render_report.py",
    "scripts/sample_cases.py",
    "scripts/generate_examples.py",
]
SWEEP_GLOBS = ["examples/drafts/*.json", "examples/manifest.json"]


class NamingSweepTest(unittest.TestCase):
    """B1/B8/B13 清野：用户可见面「兽」=0，旧 code 仅存于迁移数据。"""

    def test_user_visible_sources_are_free_of_beast_names(self):
        checked = 0
        for rel in SWEEP_FILES:
            text = (ROOT / rel).read_text(encoding="utf-8")
            checked += 1
            self.assertNotIn("兽", text, rel)
        for pattern in SWEEP_GLOBS:
            for path in sorted(ROOT.glob(pattern)):
                self.assertNotIn("兽", path.read_text(encoding="utf-8"), str(path))
                checked += 1
        self.assertGreater(checked, 15)

    def test_old_codes_only_live_in_migration_data(self):
        allowed = {
            "scripts/role_match.py",  # LEGACY_ROLE_MIGRATION / LEGACY_ROLE_NAMES / BEAST_TO_WORKER
            "scripts/migrate_report.py",  # 迁移脚本
            "docs/MIGRATION_NOTES.md",  # 历史映射表
        }
        offenders = []
        for path in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "docs").glob("*.md")) + list((ROOT / "references").glob("*")) + [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "INSTALL.md", ROOT / "AGENTS.md"]:
            rel = str(path.relative_to(ROOT))
            if rel in allowed or path.suffix not in {".py", ".md", ".json"} or not path.is_file():
                continue
            if OLD_CODE_PATTERN.search(path.read_text(encoding="utf-8")):
                offenders.append(rel)
        offenders += [
            str(p.relative_to(ROOT)) for p in sorted(ROOT.glob("examples/drafts/*.json"))
            if OLD_CODE_PATTERN.search(p.read_text(encoding="utf-8"))
        ]
        self.assertEqual(offenders, [], f"旧 code 残留在非迁移数据文件：{offenders}")

    def test_role_table_contains_twelve_distinct_nicknames(self):
        self.assertEqual(len({r["name"] for r in ROLES}), 12)
        self.assertNotIn("SHADOW_WORKER", ROLE_BY_CODE)



class BeastToWorkerMappingTest(unittest.TestCase):
    """机械映射一一对应且覆盖全部 13 项。"""

    def test_mapping_is_complete_bijection(self):
        worker_codes = {role["code"] for role in ROLES} | {"SHADOW_WORKER"}
        self.assertEqual(set(BEAST_TO_WORKER.values()), worker_codes)
        self.assertEqual(len(BEAST_TO_WORKER), 13)


class BrandExposureTest(unittest.TestCase):
    """Logo 三处露出与工牌码（冻结口径：主标题/CTA/OCR marker 不动）。"""

    def test_html_carries_badge_ticker_and_footer_lockup(self):
        cases = {case["slug"]: case for case in case_definitions()}
        html = render_report(finalize_report(draft_for_case(cases["operations-repetitive"])))

        self.assertIn("ticker-badge", html)  # ticker mbai 徽章
        self.assertIn("MBAI", html)
        self.assertIn("MBAI — Me, Beyond AI · 我，在 AI 之上", html)  # 页脚锁定语
        self.assertNotIn("SPECIMEN POD", html)  # 工牌码进 ticker 与标本舱
        self.assertIn("表格永动机", html)

    def test_card_script_carries_badge_and_brand_asset(self):
        cases = {case["slug"]: case for case in case_definitions()}
        html = render_report(finalize_report(draft_for_case(cases["risk-owner-showcase"])))

        # Canvas 模板字面量注入点与徽章 data URI 常量（${badge} 为 JS 模板变量）。
        self.assertNotIn("SPECIMEN POD // ${badge}", html)
        self.assertNotIn("SPECIMEN CARD // ${badge}", html)
        self.assertIn('const badge = "TW-10"', html)
        self.assertNotIn("__ASSET_BADGE__", html)  # 占位符已替换为徽章 data URI
        self.assertIn("data:image/svg+xml;base64,", html)
        # 卡面顶栏标题与 OCR marker 冻结不动。
        self.assertIn("工作任务 AI", html)
        self.assertIn('ctx.fillText("欧八同学",', html)
        self.assertIn("生成自己的职业 AI 体检报告", html)
        self.assertNotIn('ctx.fillText("mbai"', html)
        self.assertNotIn("工作方式图鉴", html)
        self.assertNotIn("我的工作方式", html)
        self.assertNotIn("不可替代指数量的也是任务，不是人", html)

    def test_brand_assets_are_closed_path_vectors(self):
        svg_dir = ROOT / "assets" / "brand" / "svg"
        badges = sorted(svg_dir.glob("mbai_badge_*.svg"))
        self.assertGreaterEqual(len(badges), 4)
        # 徽章（卡面/ticker 实际消费的资产）必须为闭合路径矢量：0 <text>、0 土耳其无点 i。
        for svg in badges:
            source = svg.read_text(encoding="utf-8")
            self.assertNotIn("<text", source, svg.name)
            self.assertNotIn("\u0131", source, svg.name)
        # 字标仅作品牌库储备（正文品牌字为 path，副标允许 <text>，不被渲染层消费）。
        self.assertGreaterEqual(len(sorted(svg_dir.glob("mbai_wordmark_*.svg"))), 3)
        for needed in ("mbai_badge_64px.png", "mbai_badge_32px.png"):
            self.assertTrue((ROOT / "assets" / "brand" / "png" / needed).is_file(), needed)


class ReanalysisMigrationTest(unittest.TestCase):
    def test_legacy_beast_cannot_be_silently_mapped(self):
        draft = valid_draft()
        draft["schema_version"] = "3.0.0"
        draft["profile"]["role"]["code"] = "TABLE_GOBLIN"
        from scripts.validate_report import ReportValidationError
        with self.assertRaisesRegex(ReportValidationError, "ROLE_REANALYSIS_REQUIRED"):
            finalize_report(draft)

    def test_current_version_rejects_remigration(self):
        with self.assertRaisesRegex(ValueError, "双翻"):
            migrate_report(finalize_report(valid_draft()))
