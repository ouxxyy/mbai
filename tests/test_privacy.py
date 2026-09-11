import unittest

from scripts.finalize_report import finalize_report
from scripts.privacy import PrivacyLeakError, assert_share_card_private, find_privacy_leaks
from tests.sample_factory import valid_draft


class ShareCardPrivacyTest(unittest.TestCase):
    def test_safe_card_passes(self):
        report = finalize_report(valid_draft())

        assert_share_card_private(report["share_card"], report["source"]["privacy_entities"])

    def test_exact_entity_match_fails_closed(self):
        report = finalize_report(valid_draft())
        report["share_card"]["snarky_quote"] += " 星河科技"

        with self.assertRaisesRegex(PrivacyLeakError, "星河科技"):
            assert_share_card_private(report["share_card"], report["source"]["privacy_entities"])

    def test_contact_patterns_fail_even_if_entity_list_missed_them(self):
        card = valid_draft()["share_card"]
        card["proof_7d"] = "联系 13812345678 或 test@example.com 查看作品"

        leaks = find_privacy_leaks(card, [])

        self.assertTrue(any("手机号" in leak for leak in leaks))
        self.assertTrue(any("邮箱" in leak for leak in leaks))

    def test_entity_matching_ignores_case_and_whitespace(self):
        card = valid_draft()["share_card"]
        card["category"] = "STAR LABS 项目交付"

        leaks = find_privacy_leaks(card, ["Star  Labs"])

        self.assertTrue(any("Star  Labs" in leak for leak in leaks))


if __name__ == "__main__":
    unittest.main()
