"""Rebuild a legacy report after model-authored v5 role and share fields are supplied.

Missing semantic classification fails closed; old task scores are recomputed with
unchanged aggregation, never by complementing an already displayed score.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.finalize_report import finalize_report
from scripts.role_match import LEGACY_ROLE_NAMES
from scripts.version import MIGRATABLE_SCHEMA_VERSIONS

MIGRATABLE_VERSIONS = MIGRATABLE_SCHEMA_VERSIONS

COMPUTED_TASK_FIELDS = ("score", "effective_weight", "weight_source", "role_codes")
COMPUTED_METADATA_FIELDS = ("is_sufficient_info", "is_role_sufficient_info")
SYNCED_SHARE_FIELDS = (
    "role_name",
    "role_tags",
    "snarky_quote",
    "exposure_index",
    "exposure_level",
    "irreplaceability_index",
    "irreplaceability_level",
)


def _to_draft(final: dict[str, Any]) -> dict[str, Any]:
    draft = {key: value for key, value in final.items() if key not in {"metrics", "methodology"}}
    metadata = {key: value for key, value in draft["report_metadata"].items() if key not in COMPUTED_METADATA_FIELDS}
    draft["report_metadata"] = metadata
    draft["tasks"] = [
        {key: value for key, value in task.items() if key not in COMPUTED_TASK_FIELDS}
        for task in draft.get("tasks", [])
    ]
    share_card = {key: value for key, value in draft["share_card"].items() if key not in SYNCED_SHARE_FIELDS}
    draft["share_card"] = share_card
    return draft


def migrate_report(final: dict[str, Any]) -> dict[str, Any]:
    version = final.get("schema_version")
    if version not in MIGRATABLE_VERSIONS:
        raise ValueError(
            f"仅迁移 {'/'.join(MIGRATABLE_VERSIONS)} 报告，当前为 {version}；"
            "当前版本不需要再迁移，避免双翻；请直接渲染"
        )
    return finalize_report(_to_draft(final))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Legacy report with model-authored v5 role and share fields")
    parser.add_argument("--output", required=True, type=Path, help="Current final report JSON")
    args = parser.parse_args()

    final = json.loads(args.input.read_text(encoding="utf-8"))
    migrated = migrate_report(final)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    old_role = final.get("profile", {}).get("role", {}).get("code", "?")
    old_name = LEGACY_ROLE_NAMES.get(old_role, final.get("profile", {}).get("role", {}).get("name", "?"))
    new_role = migrated["profile"]["role"]
    print(
        f"MIGRATED path={args.output.resolve()} "
        f"role={old_role}({old_name})->{new_role['code']}({new_role['name']}) "
        f"display_index={migrated['metrics']['irreplaceability_index']} "
        f"level={migrated['metrics']['irreplaceability_level']} "
        f"raw_score={migrated['metrics']['raw_score']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
