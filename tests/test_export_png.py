import tempfile
import unittest
from pathlib import Path

from scripts.export_png import export_png, find_chrome, png_dimensions, png_text_chunks
from scripts.finalize_report import finalize_report
from scripts.render_report import render_report
from tests.sample_factory import valid_draft


class ExportPngTest(unittest.TestCase):
    def test_reads_png_dimensions_and_rejects_non_png(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.png"
            bad.write_bytes(b"not-png")
            with self.assertRaisesRegex(ValueError, "PNG"):
                png_dimensions(bad)

    def test_exports_real_1080_by_1440_png_with_local_chrome(self):
        chrome = find_chrome()
        if chrome is None:
            self.skipTest("Chrome/Chromium not available")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html_path = root / "report.html"
            png_path = root / "share.png"
            html_path.write_text(render_report(finalize_report(valid_draft())), encoding="utf-8")

            export_png(html_path, png_path, chrome_path=chrome)

            self.assertEqual(png_dimensions(png_path), (1080, 1440))
            self.assertGreater(png_path.stat().st_size, 50_000)
            self.assertEqual(png_text_chunks(png_path), [])


if __name__ == "__main__":
    unittest.main()
