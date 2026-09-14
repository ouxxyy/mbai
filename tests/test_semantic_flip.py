"""语义翻转（3.0.0）：替代指数 → AI 不可替代指数的展示层单点换算。

analyst 方案 §2/§3/§7 与 Mika 拍板口径：
- 唯一换算：先取整、后取补（display = 100 − round5(raw)）；
- 翻转只允许发生在 scripts/display_metrics.py 的单一函数；
- 锚点 87.5→10 / 85→15 / 92.5→5；21 点档位翻转映射与镜像带域逐一一致；
- 迁移防双翻；全链五层同数同词。
"""

import json
import re
import tempfile
import unittest
from pathlib import Path

from scripts.display_metrics import (
    DISPLAY_TRANSFORM_NOTE,
    LEVEL_FLIP,
    to_display_metrics,
    to_irreplaceability,
)
from scripts.finalize_report import finalize_report
from scripts.render_report import render_report
from scripts.score_report import aggregate_tasks, round_half_up_to_five
from scripts.sample_cases import case_definitions, draft_for_case
from scripts.validate_report import assert_valid_report

ROOT = Path(__file__).resolve().parents[1]

# 镜像展示带域（analyst §3）：≤20 LOW / 25–60 MEDIUM / ≥65 HIGH。
def _mirror_band(display_value: int) -> str:
    if display_value <= 20:
        return "LOW"
    if display_value >= 65:
        return "HIGH"
    return "MEDIUM"


def _internal_metrics(pairs):
    tasks = [
        {"exposure_level": level, "time_share_percent": share}
        for level, share in pairs
    ]
    metrics, _ = aggregate_tasks(tasks)
    return metrics


def _display_for(levels_and_shares):
    return to_display_metrics(_internal_metrics(levels_and_shares))


class RoundingAnchorsTest(unittest.TestCase):
    """analyst §7 锚点表（唯一来源）：87.5→10、85→15、92.5→5。"""

    def test_anchor_875_displays_10_low(self):
        display = _display_for([("HIGH", 45), ("HIGH", 30), ("MEDIUM", 25)])
        self.assertEqual(display["irreplaceability_index"], 10)
        self.assertEqual(display["irreplaceability_level"], "LOW")

    def test_anchor_85_displays_15_low(self):
        # 替代 85 属 HIGH 档（>75），翻转后为 15/LOW。
        display = _display_for([("HIGH", 85), ("LOW", 15)])
        self.assertEqual(display["irreplaceability_index"], 15)
        self.assertEqual(display["irreplaceability_level"], "LOW")

    def test_anchor_925_displays_5_low(self):
        display = _display_for([("HIGH", 85), ("MEDIUM", 15)])
        self.assertEqual(display["irreplaceability_index"], 5)
        self.assertEqual(display["irreplaceability_level"], "LOW")

    def test_doc_example_7746_displays_25_medium(self):
        display = _display_for([("HIGH", 40), ("MEDIUM", 30), ("LOW", None), ("UNKNOWN", 20), ("UNKNOWN", None)])
        self.assertEqual(display["irreplaceability_index"], 25)
        self.assertEqual(display["irreplaceability_level"], "MEDIUM")


class RoundingOrderTrapTest(unittest.TestCase):
    """A2 防线：禁止「先取补再取整」——两种顺序结果不同，必须锁死后者。"""

    def test_round_first_then_complement_is_the_only_order(self):
        raw = 87.5
        self.assertEqual(100 - round_half_up_to_five(raw), 10)
        self.assertEqual(round_half_up_to_five(100 - raw), 15)  # 错误顺序的陷阱值
        self.assertNotEqual(
            round_half_up_to_five(100 - raw),
            100 - round_half_up_to_five(raw),
        )

    def test_to_irreplaceability_uses_round_first(self):
        self.assertEqual(to_irreplaceability(87.5), 10)
        self.assertEqual(to_irreplaceability(92.5), 5)
        self.assertEqual(to_irreplaceability(85), 15)


class TwentyOnePointEquivalenceTest(unittest.TestCase):
    """A3 防线：0–100 全部 21 个 5 分档，翻转表与镜像带域逐一一致，且补运算可逆。"""

    def test_flip_table_matches_mirrored_bands_on_all_21_steps(self):
        for replacement in range(0, 101, 5):
            display_value = 100 - replacement
            self.assertEqual(display_value + replacement, 100, "补运算必须可逆")
            # 复刻旧带域判替代等级（0–35 LOW / 40–75 MEDIUM / 80–100 HIGH）。
            if replacement <= 35:
                replacement_level = "LOW"
            elif replacement <= 75:
                replacement_level = "MEDIUM"
            else:
                replacement_level = "HIGH"
            self.assertEqual(
                LEVEL_FLIP[replacement_level],
                _mirror_band(display_value),
                f"替代分 {replacement} 的翻转等级与镜像带域不一致",
            )


class SingleFlipPointTest(unittest.TestCase):
    """A4/A5 防线：100− 翻转只允许出现在 display_metrics.py。"""

    def test_complement_operation_lives_only_in_display_metrics(self):
        pattern = re.compile(r"100\s*-\s*")
        offenders = []
        for path in sorted((ROOT / "scripts").glob("*.py")):
            source = path.read_text(encoding="utf-8")
            hits = [line_no for line_no, line in enumerate(source.splitlines(), start=1) if pattern.search(line)]
            if path.name == "display_metrics.py":
                self.assertEqual(len(hits), 1, "取补运算在 display_metrics.py 内也只能有一个位置")
                continue
            offenders.extend(f"{path.name}:{line_no}" for line_no in hits)
        self.assertEqual(offenders, [], f"发现单点翻转之外的取补运算：{offenders}")

    def test_score_report_stays_pure_replacement(self):
        source = (ROOT / "scripts" / "score_report.py").read_text(encoding="utf-8")
        self.assertNotIn("irreplaceability", source)
        metrics = _internal_metrics([("HIGH", 45), ("HIGH", 30), ("MEDIUM", 25)])
        self.assertEqual(metrics["exposure_index"], 90)  # 内部仍是替代语义
        self.assertEqual(metrics["exposure_level"], "HIGH")


class DisplayMetricsContractTest(unittest.TestCase):
    def test_display_metrics_renames_and_preserves_traceability(self):
        metrics = _internal_metrics([("HIGH", 45), ("HIGH", 30), ("MEDIUM", 25)])
        display = to_display_metrics(metrics)

        self.assertNotIn("exposure_index", display)
        self.assertNotIn("exposure_level", display)
        self.assertEqual(display["irreplaceability_index"], 10)
        self.assertEqual(display["irreplaceability_level"], "LOW")
        # raw_score 与聚合口径字段原样保留（可追溯锚点）。
        self.assertEqual(display["raw_score"], 87.5)
        self.assertEqual(display["rounding_mode"], "ROUND_HALF_UP_TO_5")
        self.assertEqual(display["weight_mode"], "USER_WEIGHTED")
        self.assertIn("100", DISPLAY_TRANSFORM_NOTE)

    def test_unknown_stays_unknown_without_fake_number(self):
        display = _display_for([("UNKNOWN", None), ("UNKNOWN", None)])
        self.assertIsNone(display["irreplaceability_index"])
        self.assertEqual(display["irreplaceability_level"], "UNKNOWN")


class SampleFlipExpectationsTest(unittest.TestCase):
    """§5 三态样例的翻转后取值：10/LOW、45/MEDIUM、无指数不变、门面 85/HIGH。"""

    @classmethod
    def setUpClass(cls):
        cases = {case["slug"]: case for case in case_definitions()}
        cls.reports = {
            slug: finalize_report(draft_for_case(cases[slug]))
            for slug in ("operations-repetitive", "ops-deep", "sparse-information", "risk-owner-showcase")
        }

    def test_standard_state_flips_to_10_low_with_same_role_and_quote(self):
        report = self.reports["operations-repetitive"]
        self.assertEqual(report["metrics"]["irreplaceability_index"], 10)
        self.assertEqual(report["metrics"]["irreplaceability_level"], "LOW")
        self.assertEqual(report["profile"]["role"]["code"], "TABLE_WORKER")
        self.assertEqual(report["profile"]["role"]["snarky_quote"], "六个平台互不相通，全靠你本人兼容。")
        self.assertEqual(report["metrics"]["raw_score"], 87.5)

    def test_parallel_state_flips_to_45_medium(self):
        report = self.reports["ops-deep"]
        self.assertEqual(report["metrics"]["irreplaceability_index"], 45)
        self.assertEqual(report["metrics"]["irreplaceability_level"], "MEDIUM")
        self.assertEqual(report["profile"]["role"]["code"], "MINESWEEPER_WORKER")

    def test_insufficient_state_unchanged(self):
        report = self.reports["sparse-information"]
        self.assertIsNone(report["metrics"]["irreplaceability_index"])
        self.assertEqual(report["metrics"]["irreplaceability_level"], "UNKNOWN")
        self.assertEqual(report["profile"]["role"]["code"], "TRANSLATOR_WORKER")

    def test_showcase_case_is_high_irreplaceability(self):
        report = self.reports["risk-owner-showcase"]
        self.assertEqual(report["metrics"]["irreplaceability_index"], 85)
        self.assertEqual(report["metrics"]["irreplaceability_level"], "HIGH")
        self.assertEqual(report["profile"]["role"]["code"], "MINESWEEPER_WORKER")

    def test_responsibility_depth_now_ranks_naturally(self):
        cases = {case["slug"]: case for case in case_definitions()}
        shallow = finalize_report(draft_for_case(cases["ops-shallow"]))
        deep = finalize_report(draft_for_case(cases["ops-deep"]))
        showcase = self.reports["risk-owner-showcase"]
        # 新语义下：纯模板执行 < 有策略责任 < 风险兜底，方向随直觉。
        self.assertLess(shallow["metrics"]["irreplaceability_index"], deep["metrics"]["irreplaceability_index"])
        self.assertLess(deep["metrics"]["irreplaceability_index"], showcase["metrics"]["irreplaceability_index"])


class FreshInputsPipelineTest(unittest.TestCase):
    """A10 防线（轻量）：3 个未参与文案打磨的虚构输入走真实管线，方向词与数字一致。"""

    def _case(self, slug, tasks):
        draft = {
            "schema_version": "3.0.0",
            "rule_version": "3.0.0",
            "report_metadata": {
                "report_id": slug,
                "generated_at": "2026-09-13T20:00:00+08:00",
                "confidence_level": "HIGH",
                "confidence_reason": "虚构验收输入。",
                "questions_asked": [],
                "questions_skipped": False,
            },
            "source": {
                "input_type": "TEXT",
                "input_name": f"{slug}.txt",
                "privacy_entities": [],
                "extraction_status": "OK",
            },
            "profile": {
                "sanitized_category": "虚构 / 方向验收",
                "situation_paragraph": "虚构输入：验证语义方向。",
                "index_note": "分数越高，当前工作越依赖人的判断、协作或现场处理。",
                "role": {
                    "code": "TABLE_WORKER",
                    "reason": "方向测试夹具，模型选择独立于指数。",
                    "confidence": "MEDIUM",
                    "name": "搬表工",
                    "tags": ["表格搬运", "格式转换"],
                    "source_task_ids": [tasks[0]["task_id"]],
                    "snarky_quote": "虚构嘴替句。",
                },
            },
            "skill_panel": {
                key: {"score": None, "evidence": "未展开", "is_known": False, "source_task_ids": []}
                for key in ("execution", "discretion", "coordination", "accountability")
            },
            "tasks": tasks,
            "human_edge": [{"summary": "虚构边界。", "source_task_ids": [tasks[0]["task_id"]]}],
            "action_plan": {
                "hand_to_ai": {"title": "a", "action": "a", "deliverable": "a", "acceptance_criteria": "a", "human_checkpoint": "a", "grounded_evidence": "a", "source_task_ids": [tasks[0]["task_id"]]},
                "level_up": {"title": "b", "action": "b", "deliverable": "b", "acceptance_criteria": "b", "human_checkpoint": "b", "grounded_evidence": "b", "source_task_ids": [tasks[0]["task_id"]]},
                "proof_7d": {"title": "c", "action": "c", "deliverable": "c", "acceptance_criteria": "c", "human_checkpoint": "c", "grounded_evidence": "c", "source_task_ids": [tasks[0]["task_id"]]},
            },
            "share_card": {
                "category": "虚构 / 方向验收",
                "role_name": "搬表工",
                "role_tags": ["表格搬运"],
                "confidence_label": "证据置信度：高",
                "irreplaceability_index": None,
                "irreplaceability_level": "UNKNOWN",
                "snarky_quote": "虚构嘴替句。",
                "value_line": "虚构方向测试。",
                "source_task_ids": [tasks[0]["task_id"]],
                "disclaimer": "依据当前任务描述分析，不代表未来失业概率。",
            },
        }
        return draft

    def _task(self, task_id, name, evidence, level, share, signals):
        return {
            "task_id": task_id,
            "task_name": name,
            "time_share_percent": share,
            "exposure_level": level,
            "ai_can_do": "机械部分。",
            "human_must_do": "关键判断。",
            "evidence": evidence,
            "reason": "虚构。",
            "confidence": "HIGH",
            "signals": signals,
        }

    def test_three_fresh_inputs_keep_direction_consistent(self):
        scenarios = [
            ("fresh-tab-mover", [("HIGH", 70), ("HIGH", 30)], 0, "LOW"),
            ("fresh-mixed-planner", [("MEDIUM", 60), ("LOW", 40)], 70, "HIGH"),
            ("fresh-field-responder", [("LOW", 50), ("LOW", 50)], 100, "HIGH"),
        ]
        for slug, spec, expected_index, expected_level in scenarios:
            with self.subTest(slug=slug):
                tasks = [
                    self._task(
                        f"task-{index}",
                        f"虚构任务 {index}",
                        f"虚构证据 {index}：导出数据并汇总进模板，同时识别上线风险对结果兜底。",
                        level,
                        share,
                        {"judgment": 2, "coordination": 1, "physical_presence": 1, "accountability": 2, "repeatability": 1, "digital_input_output": 2},
                    )
                    for index, (level, share) in enumerate(spec)
                ]
                report = finalize_report(self._case(slug, tasks))
                assert_valid_report(report)
                self.assertEqual(report["metrics"]["irreplaceability_index"], expected_index)
                self.assertEqual(report["metrics"]["irreplaceability_level"], expected_level)
                html = render_report(report)
                self.assertIn("不可替代指数", html)
                self.assertNotIn("替代指数量的是任务", html)


class FullChainConsistencyTest(unittest.TestCase):
    """门槛 1：同一案例 draft → report.json → HTML 巨号数字 → Canvas PNG → OCR 五层同数同词。"""

    def test_five_layers_carry_same_number_and_word(self):
        try:
            from scripts.export_png import export_png, find_chrome
            from scripts.verify_png_privacy import ocr_png
        except ImportError:  # pragma: no cover
            self.skipTest("导出或 OCR 依赖不可用")

        if find_chrome() is None:
            self.skipTest("Chrome/Chromium not available")

        cases = {case["slug"]: case for case in case_definitions()}
        for slug, expected_number, expected_word in (
            ("operations-repetitive", "10", "低不可替代"),
            ("ops-deep", "45", "中不可替代"),
            ("risk-owner-showcase", "85", "高不可替代"),
        ):
            with self.subTest(slug=slug):
                report = finalize_report(draft_for_case(cases[slug]))
                assert_valid_report(report)
                # 第 1–2 层：draft → report.json
                self.assertEqual(str(report["metrics"]["irreplaceability_index"]), expected_number)
                # 第 3 层：HTML 巨号数字与方向词
                html_text = render_report(report)
                self.assertIn(f'>{expected_number}</div>', html_text)
                self.assertIn(expected_word, html_text)
                # 第 4–5 层：Canvas PNG（命令行导出）→ OCR
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    html_path = root / "report.html"
                    html_path.write_text(html_text, encoding="utf-8")
                    png_path = export_png(html_path, root / "card.png")
                    ocr_text = ocr_png(png_path)
                    self.assertIn(expected_number, ocr_text)
                    self.assertIn("不可替代", ocr_text.replace(" ", ""))
                    # OCR 层与 JSON 层不得出现方向矛盾的旧词。
                    self.assertNotIn("低替代", ocr_text)
                    self.assertNotIn("高替代", ocr_text)


if __name__ == "__main__":
    unittest.main()
