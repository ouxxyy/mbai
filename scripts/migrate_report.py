"""Migrate a frozen 1.0.0 final report to the 2.0.0 twelve-role contract.

迁移语义（docs/MIGRATION_NOTES.md）：
- 指数算法与聚合语义不动：旧报告的 exposure_index / exposure_level / 任务等级逐字段保留；
- 旧六角色 code 弃用，角色由匹配引擎按任务证据重判（冻结版②迁移映射的确定性落法）；
- 旧 LOCKED_ROLE 单门槛兜底改为 R4 双门槛：“有指数＋影子兽”并存态允许出现；
- 新增字段：profile.situation_paragraph / index_note、tasks[].role_codes、
  metrics.task_count_role_evaluable、report_metadata.is_role_sufficient_info。
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

COMPUTED_TASK_FIELDS = ("score", "effective_weight", "weight_source", "role_codes")
COMPUTED_METADATA_FIELDS = ("is_sufficient_info", "is_role_sufficient_info")
SYNCED_SHARE_FIELDS = ("role_name", "role_tags", "snarky_quote", "exposure_index", "exposure_level")


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
    if final.get("schema_version") != "1.0.0":
        raise ValueError(f"仅迁移 1.0.0 报告，当前为 {final.get('schema_version')}")
    return finalize_report(_to_draft(final))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="1.0.0 final report JSON")
    parser.add_argument("--output", required=True, type=Path, help="Migrated 2.0.0 final report JSON")
    args = parser.parse_args()

    final = json.loads(args.input.read_text(encoding="utf-8"))
    migrated = migrate_report(final)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    old_role = final.get("profile", {}).get("role", {}).get("code", "?")
    old_name = LEGACY_ROLE_NAMES.get(old_role, "?")
    new_role = migrated["profile"]["role"]
    print(
        f"MIGRATED path={args.output.resolve()} "
        f"role={old_role}({old_name})->{new_role['code']}({new_role['name']}) "
        f"index={final['metrics']['exposure_index']}->{migrated['metrics']['exposure_index']} "
        f"level={final['metrics']['exposure_level']}->{migrated['metrics']['exposure_level']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
