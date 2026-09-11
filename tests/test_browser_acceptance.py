import tempfile
import unittest
from pathlib import Path

from scripts.browser_acceptance import capture_viewport, probe_layout
from scripts.export_png import find_chrome, png_dimensions
from scripts.finalize_report import finalize_report
from scripts.render_report import render_report
from tests.sample_factory import valid_draft


class BrowserAcceptanceTest(unittest.TestCase):
    def test_chrome_mobile_viewport_has_no_horizontal_overflow(self):
        chrome = find_chrome()
        if chrome is None:
            self.skipTest("Chrome/Chromium not available")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_path = root / "report.html"
            screenshot = root / "mobile.png"
            report_path.write_text(render_report(finalize_report(valid_draft())), encoding="utf-8")

            metrics = probe_layout(report_path, width=390, height=844, chrome_path=chrome)
            capture_viewport(report_path, screenshot, width=390, height=844, chrome_path=chrome)

            self.assertEqual(metrics["viewport_width"], 390)
            self.assertLessEqual(metrics["scroll_width"], metrics["viewport_width"])
            self.assertFalse(metrics["horizontal_overflow"])
            self.assertEqual(metrics["external_resource_requests"], [])
            self.assertEqual(png_dimensions(screenshot), (390, 844))


if __name__ == "__main__":
    unittest.main()
