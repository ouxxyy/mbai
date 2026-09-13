import unittest
from unittest import mock

from scripts import check_env
from scripts.check_env import check_chrome, check_python, check_swift


class CheckEnvTest(unittest.TestCase):
    def test_python_check_passes_on_supported_runtime(self):
        ok, detail = check_python()
        self.assertTrue(ok)
        self.assertIn("Python", detail)

    def test_swift_check_always_returns_reason(self):
        ok, detail = check_swift()
        self.assertIsInstance(ok, bool)
        self.assertTrue(detail.strip())

    def test_chrome_check_reports_degradation_when_missing(self):
        with mock.patch.object(check_env, "find_chrome", return_value=None):
            ok, detail = check_chrome()
        self.assertFalse(ok)
        self.assertIn("--no-png", detail)

    def test_chrome_check_reports_ready_when_found(self):
        with mock.patch.object(check_env, "find_chrome", return_value=None):
            missing_ok, _ = check_chrome()
        ok, detail = check_chrome()
        self.assertEqual(ok, not missing_ok)
        self.assertTrue(detail.strip())


if __name__ == "__main__":
    unittest.main()
