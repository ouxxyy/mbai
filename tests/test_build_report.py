import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_report import build_report
from tests.sample_factory import valid_draft


class BuildReportTest(unittest.TestCase):
    def test_builds_final_json_and_offline_html_from_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft_path = root / "draft.json"
            output_dir = root / "output"
            draft_path.write_text(json.dumps(valid_draft(), ensure_ascii=False), encoding="utf-8")

            artifacts = build_report(draft_path, output_dir, export_card=False, run_ocr=False)

            self.assertEqual(set(artifacts), {"report_json", "report_html"})
            report = json.loads(artifacts["report_json"].read_text(encoding="utf-8"))
            self.assertEqual(report["metrics"]["irreplaceability_index"], 40)
            self.assertIn("<!doctype html>", artifacts["report_html"].read_text(encoding="utf-8"))

    def test_repeated_build_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft_path = root / "draft.json"
            draft_path.write_text(json.dumps(valid_draft(), ensure_ascii=False), encoding="utf-8")

            first = build_report(draft_path, root / "one", export_card=False, run_ocr=False)
            second = build_report(draft_path, root / "two", export_card=False, run_ocr=False)

            self.assertEqual(first["report_json"].read_bytes(), second["report_json"].read_bytes())
            self.assertEqual(first["report_html"].read_bytes(), second["report_html"].read_bytes())


if __name__ == "__main__":
    unittest.main()
