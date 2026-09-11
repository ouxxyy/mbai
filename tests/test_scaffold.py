import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTest(unittest.TestCase):
    def test_frozen_contract_files_exist_and_are_parseable(self):
        schema_path = ROOT / "references" / "report-contract.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0.0")
        self.assertTrue((ROOT / "docs" / "SCORING_RULES.md").is_file())
        self.assertTrue((ROOT / "docs" / "INTERFACE_CONTRACT.md").is_file())
        self.assertTrue((ROOT / "docs" / "SOURCES.md").is_file())


if __name__ == "__main__":
    unittest.main()
