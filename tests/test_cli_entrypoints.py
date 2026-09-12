import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliEntrypointTest(unittest.TestCase):
    def test_bundled_python_entrypoints_work_from_outside_skill_directory(self):
        scripts = [
            "extract_resume.py",
            "finalize_report.py",
            "validate_report.py",
            "render_report.py",
            "export_png.py",
            "verify_png_privacy.py",
            "build_report.py",
            "migrate_report.py",
        ]
        with tempfile.TemporaryDirectory() as directory:
            for script in scripts:
                completed = subprocess.run(
                    [str(ROOT / ".venv" / "bin" / "python"), str(ROOT / "scripts" / script), "--help"],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, f"{script}: {completed.stderr}")


if __name__ == "__main__":
    unittest.main()
