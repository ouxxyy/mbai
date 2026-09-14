import json
import unittest
from pathlib import Path

from scripts.version import (
    MIGRATABLE_SCHEMA_VERSIONS,
    RULE_VERSION,
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
)


ROOT = Path(__file__).resolve().parents[1]


class VersionSingleSourceTest(unittest.TestCase):
    """版本单一来源：scripts/version.py 与 schema const、SKILL.md metadata 断言一致。"""

    def test_version_constants_match_schema_const(self):
        schema = json.loads(
            (ROOT / "references" / "report-contract.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)
        self.assertEqual(schema["properties"]["rule_version"]["const"], RULE_VERSION)

    def test_skill_md_metadata_matches_contract_version(self):
        frontmatter = (ROOT / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
        self.assertIn(f"version: {SCHEMA_VERSION}", frontmatter)

    def test_generate_examples_manifest_uses_single_source(self):
        source = (ROOT / "scripts" / "generate_examples.py").read_text(encoding="utf-8")
        self.assertIn("from scripts.version import RULE_VERSION", source)
        self.assertNotRegex(source, r'"rule_version":\s*"')

    def test_current_version_supported_but_not_migratable(self):
        self.assertEqual(SUPPORTED_SCHEMA_VERSIONS[-1], SCHEMA_VERSION)
        self.assertNotIn(SCHEMA_VERSION, MIGRATABLE_SCHEMA_VERSIONS)
        self.assertEqual(MIGRATABLE_SCHEMA_VERSIONS, SUPPORTED_SCHEMA_VERSIONS[:-1])


if __name__ == "__main__":
    unittest.main()


class TrackedVersionStampGateTest(unittest.TestCase):
    """P0-3 防回归门禁（analyst 2026-09-14 方案）：版本戳从源头单源锁死。"""

    def test_tracked_examples_carry_current_version_stamp(self):
        # ① tracked 版本戳清野：drafts＋manifest 不得停在历史版本。
        drafts = sorted((ROOT / "examples" / "drafts").glob("*.json"))
        self.assertGreaterEqual(len(drafts), 13)
        for draft in drafts:
            payload = json.loads(draft.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("schema_version"), SCHEMA_VERSION, draft.name)
            self.assertEqual(payload.get("rule_version"), RULE_VERSION, draft.name)
        manifest = json.loads((ROOT / "examples" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["rule_version"], RULE_VERSION)

    def test_generate_examples_produces_current_version_stamps(self):
        # ② 生成式测试：从源头锁死，跨机器稳定（新 checkout 无 output 目录也成立）。
        # 断言对象是 drafts/manifest（纯 Python 生成）；PDF 简历夹具依赖 Chrome，
        # 无 Chrome 时以文本替身 mock（reviewer P0 复核指出的误跳过修正），门禁不再依赖浏览器。
        import tempfile
        from unittest import mock

        from scripts import generate_examples as generator

        def _fake_write_pdf(path, text):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        with mock.patch.object(generator, "_write_pdf", _fake_write_pdf):
            with tempfile.TemporaryDirectory() as directory:
                manifest_path = generator.generate_examples(Path(directory), build_outputs=False)
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(manifest["rule_version"], RULE_VERSION)
                for entry in manifest["cases"]:
                    draft = json.loads((Path(directory) / entry["draft_path"]).read_text(encoding="utf-8"))
                    self.assertEqual(draft["schema_version"], SCHEMA_VERSION, entry["slug"])
                    self.assertEqual(draft["rule_version"], RULE_VERSION, entry["slug"])

    def test_no_stale_version_literals_in_scripts(self):
        # ③ 单源防回退：scripts/ 内禁止历史版本字面量（白名单＝version.py 的 SUPPORTED 历史表
        #    与 migrate_report.py 的迁移语义；测试夹具的历史版本属 fixtures，在 tests/ 域不扫）。
        import re

        pattern = re.compile(r'"[123]\.0\.0"')
        whitelist = {"version.py", "migrate_report.py"}
        offenders = []
        for path in sorted((ROOT / "scripts").glob("*.py")):
            if path.name in whitelist:
                continue
            hits = [line_no for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) if pattern.search(line)]
            offenders.extend(f"{path.name}:{line_no}" for line_no in hits)
        self.assertEqual(offenders, [], f"scripts/ 内发现历史版本字面量：{offenders}")
