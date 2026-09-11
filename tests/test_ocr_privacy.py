import unittest
import tempfile
from pathlib import Path

from scripts.verify_png_privacy import OcrVerificationError, assert_ocr_meaningful, build_ocr_helper, find_ocr_privacy_leaks


class OcrPrivacyTest(unittest.TestCase):
    def test_detects_entities_and_contact_details_in_ocr_text(self):
        text = "项目风险领航员 星河科技 联系 13812345678 test@example.com"

        leaks = find_ocr_privacy_leaks(text, ["星河科技", "张三"])

        self.assertTrue(any("星河科技" in leak for leak in leaks))
        self.assertTrue(any("手机号" in leak for leak in leaks))
        self.assertTrue(any("邮箱" in leak for leak in leaks))

    def test_allows_generalized_card_text(self):
        text = "项目风险领航员 企业服务 项目交付 本卡不是个人失业概率"

        self.assertEqual(find_ocr_privacy_leaks(text, ["星河科技", "张三"]), [])

    def test_rejects_empty_or_unrelated_ocr_instead_of_false_pass(self):
        card = {"role_name": "项目风险领航员"}

        with self.assertRaises(OcrVerificationError):
            assert_ocr_meaningful("", card)
        with self.assertRaises(OcrVerificationError):
            assert_ocr_meaningful("unrelated blank image", card)

    def test_accepts_ocr_that_contains_the_card_role(self):
        assert_ocr_meaningful("工作任务 AI 替代指数\n项目风险领航员", {"role_name": "项目风险领航员"})

    def test_builds_native_macos_vision_ocr_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "ocr-image"

            built = build_ocr_helper(output)

            self.assertEqual(built, output)
            self.assertTrue(output.is_file())
            self.assertTrue(output.stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
