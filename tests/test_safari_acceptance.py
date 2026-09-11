import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.finalize_report import finalize_report
from scripts.render_report import render_report
from scripts.safari_acceptance import inspect_safari
from tests.sample_factory import valid_draft


class SafariAcceptanceTest(unittest.TestCase):
    def test_real_safari_has_no_horizontal_overflow_at_narrow_width(self):
        if shutil.which("safaridriver") is None:
            self.skipTest("safaridriver not available")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report.html"
            screenshot = root / "safari-mobile.png"
            report.write_text(render_report(finalize_report(valid_draft())), encoding="utf-8")

            try:
                result = inspect_safari(report, css_width=390, css_height=844, screenshot_path=screenshot)
            except RuntimeError as exc:
                if "Allow remote automation" in str(exc):
                    self.skipTest("SafariDriver requires 'Allow remote automation' in Safari Develop menu")
                raise

            self.assertEqual(result["browser"], "Safari")
            self.assertLessEqual(abs(result["viewport_width"] - 390), 2)
            self.assertLessEqual(result["scroll_width"], result["viewport_width"])
            self.assertFalse(result["horizontal_overflow"])
            self.assertTrue(screenshot.is_file())


if __name__ == "__main__":
    unittest.main()
