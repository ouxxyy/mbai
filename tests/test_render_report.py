import re
import unittest

from scripts.finalize_report import finalize_report
from scripts.render_report import render_report
from tests.sample_factory import valid_draft


class RenderReportTest(unittest.TestCase):
    def setUp(self):
        self.report = finalize_report(valid_draft())

    def test_renders_six_sections_in_required_order(self):
        html = render_report(self.report)
        ids = ["hero", "skill-panel", "task-breakdown", "human-edge", "action-plan", "share-export", "methodology"]
        positions = [html.index(f'id="{section_id}"') for section_id in ids]

        self.assertEqual(positions, sorted(positions))
        self.assertIn("60", html)
        self.assertIn("不是失业概率", html)
        self.assertIn("项目风险领航员", html)

    def test_is_byte_deterministic_for_same_final_json(self):
        self.assertEqual(render_report(self.report), render_report(self.report))

    def test_renderer_follows_final_json_without_recalculating(self):
        self.report["metrics"]["exposure_index"] = 15
        self.report["share_card"]["exposure_index"] = 15

        html = render_report(self.report)

        self.assertIn('data-exposure-index="15"', html)
        self.assertIn("15 / 100", html)

    def test_escapes_resume_evidence_and_script_closing_sequences(self):
        draft = valid_draft()
        draft["tasks"][0]["evidence"] = '<script>window.pwned = true</script> 负责周报'
        html = render_report(finalize_report(draft))

        self.assertNotIn("<script>window.pwned", html)
        self.assertIn("&lt;script&gt;window.pwned", html)
        self.assertNotRegex(html, r"const\s+cardData\s*=.*</script>")

    def test_has_no_external_runtime_assets(self):
        html = render_report(self.report).lower()

        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link ", html)
        self.assertNotIn("@import", html)
        self.assertNotIn("url(http", html)

    def test_share_canvas_is_exact_size_and_has_real_download_path(self):
        html = render_report(self.report)

        self.assertIn('id="share-card-canvas" width="1080" height="1440"', html)
        self.assertIn("canvas.toBlob", html)
        self.assertIn("download =", html)
        self.assertIn("window.__CARD_READY__ = true", html)

    def test_mobile_contract_prevents_horizontal_overflow(self):
        html = render_report(self.report)

        self.assertIn("@media (max-width: 680px)", html)
        self.assertRegex(html, r"overflow-x:\s*hidden")
        self.assertIn("min-height: 44px", html)
        self.assertIn("data-horizontal-overflow", html)

    def test_card_script_contains_only_share_projection_not_private_entities(self):
        html = render_report(self.report)
        match = re.search(r"const cardData = (.*?);\n", html)

        self.assertIsNotNone(match)
        self.assertNotIn("星河科技", match.group(1))
        self.assertNotIn("张三", match.group(1))

    def test_information_insufficient_uses_words_instead_of_fake_number(self):
        draft = valid_draft()
        for task in draft["tasks"]:
            task["exposure_level"] = "UNKNOWN"
        report = finalize_report(draft)

        html = render_report(report)

        self.assertIn('data-exposure-index="unknown"', html)
        self.assertIn("信息不足", html)
        self.assertNotIn("None / 100", html)


if __name__ == "__main__":
    unittest.main()
