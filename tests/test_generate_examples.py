import json
import tempfile
import unittest
from pathlib import Path

from scripts.extract_resume import extract_resume
from scripts.export_png import find_chrome
from scripts.generate_examples import generate_examples, relative_artifact_paths


class GenerateExamplesTest(unittest.TestCase):
    def test_relativizes_absolute_artifacts_against_relative_root(self):
        root = Path("examples")
        absolute = (Path.cwd() / root / "output" / "case" / "report.html").resolve()

        result = relative_artifact_paths(root, {"report_html": absolute})

        self.assertEqual(result, {"report_html": "output/case/report.html"})

    def test_generates_real_text_docx_and_pdf_inputs_plus_drafts(self):
        if find_chrome() is None:
            self.skipTest("Chrome/Chromium not available for PDF fixture")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            manifest_path = generate_examples(root, build_outputs=False)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertGreaterEqual(len(manifest["cases"]), 12)
            inputs = {item["input_type"] for item in manifest["cases"]}
            self.assertEqual(inputs, {"TEXT", "DOCX", "PDF"})
            for item in manifest["cases"]:
                self.assertTrue((root / item["resume_path"]).is_file())
                self.assertTrue((root / item["draft_path"]).is_file())
                self.assertRegex(item["resume_sha256"], r"^[0-9a-f]{64}$")

            for slug in ("operations-repetitive", "content-calibrator", "technical-execution"):
                item = next(entry for entry in manifest["cases"] if entry["slug"] == slug)
                extracted = extract_resume(root / item["resume_path"])
                self.assertEqual(extracted["status"], "OK", slug)
                self.assertGreater(len(extracted["untrusted_resume_text"]), 30, slug)


if __name__ == "__main__":
    unittest.main()
