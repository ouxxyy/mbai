"""Migrate legacy final reports to the current 3.0.0 irreplaceability contract.

迁移语义（docs/MIGRATION_NOTES.md）：
- 1.0.0 → 3.0.0：旧六角色重判（12 类＋影子兽）、schema 新字段、展示层翻转；
- 2.0.0 → 3.0.0：字段重命名 exposure_* → irreplaceability_*，指数按「先取整、后取补」
  翻转（90/HIGH → 10/LOW），raw_score 与任务级替代语义逐字段保留；
- 3.0.0 报告拒绝再次迁移（防双翻，schema_version 门控；幂等性由测试锁定）；
- 指数聚合算法与任务等级判定完全未动，翻转是产品决策而非回归（见 MIGRATION_NOTES）。
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

MIGRATABLE_VERSIONS = ("1.0.0", "2.0.0")

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
            "3.0.0 报告已是不可替代口径，再次迁移会造成双翻"
        )
    return finalize_report(_to_draft(final))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="1.0.0/2.0.0 final report JSON")
    parser.add_argument("--output", required=True, type=Path, help="Migrated 3.0.0 final report JSON")
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
