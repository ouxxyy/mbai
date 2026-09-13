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
