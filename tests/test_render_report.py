import re
import unittest

from scripts.finalize_report import finalize_report
from scripts.render_report import render_report
from scripts.sample_cases import case_definitions, draft_for_case
from tests.sample_factory import valid_draft


class RenderReportTest(unittest.TestCase):
    def setUp(self):
        self.report = finalize_report(valid_draft())

    def test_renders_sections_in_required_order(self):
        html = render_report(self.report)
        ids = ["hero", "task-breakdown", "human-edge", "action-plan", "skill-panel", "share-export", "methodology"]
        positions = [html.index(f'id="{section_id}"') for section_id in ids]

        self.assertEqual(positions, sorted(positions))
        self.assertIn("40", html)
        self.assertIn("不是失业概率", html)
        self.assertIn("分数越高，当前工作越依赖人的判断、协作或现场处理", html)
        self.assertIn("低不可替代", html)
        self.assertNotIn("替代指数量的是任务", html)

    def test_is_byte_deterministic_for_same_final_json(self):
        self.assertEqual(render_report(self.report), render_report(self.report))

    def test_renderer_follows_final_json_without_recalculating(self):
        self.report["metrics"]["irreplaceability_index"] = 15
        self.report["share_card"]["irreplaceability_index"] = 15

        html = render_report(self.report)

        self.assertIn('data-irreplaceability-index="15"', html)
        self.assertIn("15", html)

    def test_unknown_index_renders_placeholder_not_fake_number(self):
        draft = valid_draft()
        for task in draft["tasks"]:
            task["exposure_level"] = "UNKNOWN"
            task["time_share_percent"] = None
        html = render_report(finalize_report(draft))

        self.assertIn("暂无指数", html)
        self.assertIn("证据不够，不下结论", html)
        self.assertIn("未知", html)

    def test_escapes_resume_evidence_and_script_closing_sequences(self):
        draft = valid_draft()
        draft["tasks"][0]["evidence"] = '<script>window.pwned = true</script> 负责周报'
        html = render_report(finalize_report(draft))

        self.assertNotIn("<script>window.pwned", html)
        self.assertIn("&lt;script&gt;window.pwned", html)
        self.assertNotRegex(html, r"const cardData\s*=.*</script>")

    def test_has_no_external_runtime_assets(self):
        html = render_report(self.report).lower()

        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link ", html)
        self.assertNotIn("@import", html)
        self.assertNotIn("url(http", html)


class BPosterStyleTest(unittest.TestCase):
    def setUp(self):
        self.html = render_report(finalize_report(valid_draft()))

    def test_b_poster_palette_and_type_system_present(self):
        for token in ("#EBFB3B", "#0D0D0D", "#FF4A00", "Arial Black", "SF Mono"):
            self.assertIn(token, self.html)

    def test_mobile_contract_prevents_horizontal_overflow(self):
        html = self.html

        self.assertIn("@media (max-width: 680px)", html)
        self.assertIn("word-break: break-word", html)
        self.assertIn("overflow-wrap:", html)
        self.assertIn("min-width: 0", html)
        self.assertIn("data-horizontal-overflow", html)

    def test_share_only_mode_pins_exact_card_viewport(self):
        html = self.html

        self.assertIn("html.share-only", html)
        self.assertIn("width: 1080px; height: 1440px", html)


class CharacterAssetTest(unittest.TestCase):
    def setUp(self):
        self.report = finalize_report(valid_draft())
        self.html = render_report(self.report)

    def test_character_image_is_embedded_as_data_uri(self):
        self.assertRegex(self.html, r'<img class="character-figure" src="data:image/(?:webp|png);base64,')

    def test_card_script_awaits_asset_decode_before_ready(self):
        html = self.html

        self.assertIn("img.decode()", html)
        self.assertIn("await document.fonts.ready", html)
        self.assertIn("window.__CARD_READY__ = true", html)

    def test_asset_failure_aborts_export_explicitly(self):
        html = self.html

        self.assertIn("drawFailure", html)
        self.assertIn("EXPORT ABORTED", html)
        self.assertIn("素材加载失败", html)
        # 失败态必须阻断下载按钮，不得静默出缺角色的成功卡片。
        self.assertIn("button.disabled = true", html)
        self.assertIn("if (window.__CARD_ERROR__) return", html)

    def test_only_selected_character_asset_is_embedded(self):
        # 每份报告只内嵌所选角色；宽泛资料仍归类，不嵌入历史兜底图。
        uris = set(re.findall(r'data:image/(?:webp|png);base64,[A-Za-z0-9+/=]+', self.html))
        self.assertEqual(len(uris), 1)

        sparse_html = render_report(finalize_report(draft_for_case(
            next(case for case in case_definitions() if case["slug"] == "sparse-information")
        )))
        sparse_uris = set(re.findall(r'data:image/(?:webp|png);base64,[A-Za-z0-9+/=]+', sparse_html))
        self.assertEqual(len(sparse_uris), 1)

    def test_missing_asset_file_fails_render_explicitly(self):
        from pathlib import Path

        import scripts.render_report as render_module

        original = render_module.ASSET_DIR
        try:
            render_module.ASSET_DIR = Path(original) / "does-not-exist"
            with self.assertRaisesRegex(RuntimeError, "素材缺失"):
                render_report(self.report)
        finally:
            render_module.ASSET_DIR = original

    def test_share_canvas_is_exact_size_and_has_real_download_path(self):
        html = self.html

        self.assertIn('id="share-card-canvas" width="1080" height="1440"', html)
        self.assertIn("canvas.toBlob", html)
        self.assertIn("download =", html)


class ShareCardContentTest(unittest.TestCase):
    def test_card_carries_cta_corner_and_grade_code(self):
        html = render_report(finalize_report(valid_draft()))

        self.assertIn('ctx.fillText("欧八同学",', html)
        self.assertIn("生成自己的职业 AI 体检报告", html)
        self.assertNotIn("SPECIMEN CARD //", html)
        self.assertIn("工作任务 AI", html)

    def test_indicator_explanation_stays_on_html_while_card_corner_carries_cta(self):
        html = render_report(finalize_report(valid_draft()))

        # 分层承担（MYW-70 2026-09-13 冻结）：HTML 报告页保留指标解释，
        # 分享卡角落承担 CTA——两层各司其职，不要求同文案。
        self.assertIn("分数越高，当前工作越依赖人的判断、协作或现场处理", html)
        self.assertIn('ctx.fillText("欧八同学",', html)
        self.assertIn("生成自己的职业 AI 体检报告", html)

    def test_card_script_contains_only_share_projection_not_private_entities(self):
        html = render_report(finalize_report(valid_draft()))
        match = re.search(r"const cardData = (.*?);\n", html)

        self.assertIsNotNone(match)
        self.assertNotIn("星河科技", match.group(1))

    def test_coexistence_card_shows_real_index_with_shadow_beast(self):
        cases = {case["slug"]: case for case in case_definitions()}
        report = finalize_report(draft_for_case(cases["ops-deep"]))
        self.assertEqual(report["profile"]["role"]["code"], "MINESWEEPER_WORKER")
        self.assertIsNotNone(report["metrics"]["irreplaceability_index"])
        self.assertEqual(report["metrics"]["irreplaceability_index"], 45)

        html = render_report(report)

        self.assertNotIn("神秘工 · 待解锁", html)
        self.assertIn("证据不够，不下结论", html)
        self.assertIn("45", html)
        self.assertIn("中不可替代", html)

    def test_long_copy_is_wrapped_not_clipped_on_card(self):
        draft = valid_draft()
        draft["profile"]["role"]["snarky_quote"] = (
            "这是一句特别长的嘴替句，用来验证分享卡在长文案下的折行保护："
            "它远超一行宽度，必须被折行或截断成省略号，而不是溢出画布边界。"
        )
        html = render_report(finalize_report(draft))

        self.assertIn("wrapLines", html)
        self.assertIn("…", html)

    def test_frozen_operations_copy_renders_verbatim(self):
        cases = {case["slug"]: case for case in case_definitions()}
        report = finalize_report(draft_for_case(cases["operations-repetitive"]))
        html = render_report(report)

        self.assertIn("六个平台互不相通，全靠你本人兼容。", html)
        self.assertIn("表格永动机", html)
        self.assertIn("每到交周报的日子", html)
        self.assertIn("分数低", html)
        self.assertIn("AI 可接管·大部分", html)


if __name__ == "__main__":
    unittest.main()
