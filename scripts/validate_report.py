"""Semantic validation for the frozen report contract (version source: scripts/version.py)."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.display_metrics import to_display_metrics
from scripts.privacy import PrivacyLeakError, assert_share_card_private
from scripts.role_match import ROLE_NAMES, ROLE_BY_CODE
from scripts.score_report import aggregate_tasks
from scripts.version import RULE_VERSION, SCHEMA_VERSION

ROOT_KEYS = {
    "schema_version",
    "rule_version",
    "report_metadata",
    "source",
    "profile",
    "metrics",
    "skill_panel",
    "tasks",
    "human_edge",
    "action_plan",
    "share_card",
    "methodology",
}


class ReportValidationError(ValueError):
    def __init__(self, errors: Iterable[str]):
        self.errors = list(errors)
        super().__init__("报告契约校验失败：" + "；".join(self.errors))


def _refs(value: Any) -> list[str]:
    return list(value.get("source_task_ids", [])) if isinstance(value, dict) else []


def _check_required_text(errors: list[str], obj: dict[str, Any], keys: Iterable[str], prefix: str) -> None:
    for key in keys:
        if not isinstance(obj.get(key), str) or not obj[key].strip():
            errors.append(f"{prefix}.{key} 必须是非空文本")


def assert_valid_report(report: dict[str, Any]) -> None:
    errors: list[str] = []

    missing = ROOT_KEYS - set(report)
    extra = set(report) - ROOT_KEYS
    if missing:
        errors.append("缺少根字段 " + ", ".join(sorted(missing)))
    if extra:
        errors.append("出现未授权根字段 " + ", ".join(sorted(extra)))
    if errors:
        raise ReportValidationError(errors)

    if report.get("schema_version") != SCHEMA_VERSION or report.get("rule_version") != RULE_VERSION:
        errors.append(f"schema_version 与 rule_version 必须为 {SCHEMA_VERSION}")

    metadata = report["report_metadata"]
    questions = metadata.get("questions_asked", [])
    if not isinstance(questions, list) or len(questions) > 3:
        errors.append("补问最多 3 个")

    profile = report["profile"]
    _check_required_text(errors, profile, ["sanitized_category", "situation_paragraph", "index_note"], "profile")

    tasks = report["tasks"]
    if not isinstance(tasks, list) or not tasks:
        errors.append("tasks 至少包含一项任务")
        task_ids: list[str] = []
    else:
        task_ids = [item.get("task_id") for item in tasks]
        if any(not isinstance(task_id, str) or not task_id for task_id in task_ids):
            errors.append("每项任务必须有 task_id")
        if len(task_ids) != len(set(task_ids)):
            errors.append("task_id 必须唯一")

    for index, item in enumerate(tasks):
        prefix = f"tasks[{index}]"
        _check_required_text(
            errors,
            item,
            ["task_name", "ai_can_do", "human_must_do", "evidence", "reason"],
            prefix,
        )
        level = item.get("exposure_level")
        if level == "UNKNOWN":
            if item.get("score") is not None or item.get("effective_weight") is not None:
                errors.append(f"{prefix} UNKNOWN 任务的 score/effective_weight 必须为 null")
            if item.get("weight_source") != "NOT_APPLICABLE":
                errors.append(f"{prefix} UNKNOWN 任务权重来源必须为 NOT_APPLICABLE")

        elif level in {"LOW", "MEDIUM", "HIGH"}:
            expected_score = {"LOW": 0, "MEDIUM": 50, "HIGH": 100}[level]
            if item.get("score") != expected_score:
                errors.append(f"{prefix}.score 与 exposure_level 不一致")
        else:
            errors.append(f"{prefix}.exposure_level 无效")

    try:
        expected_metrics, expected_tasks = aggregate_tasks(tasks)
        expected_sufficient = expected_metrics["is_sufficient_info"]
        expected_metrics.pop("is_sufficient_info")
        expected_metrics = to_display_metrics(expected_metrics)
        actual_metrics = report["metrics"]
        for key, expected in expected_metrics.items():
            actual = actual_metrics.get(key)
            if key == "raw_score" and expected is not None and isinstance(actual, (int, float)):
                if not math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-12):
                    errors.append("metrics.raw_score 与任务聚合不一致")
            elif actual != expected:
                errors.append(f"metrics.{key} 与任务聚合不一致")
        for index, expected in enumerate(expected_tasks):
            for key in ("score", "effective_weight", "weight_source"):
                if tasks[index].get(key) != expected.get(key):
                    errors.append(f"tasks[{index}].{key} 与冻结规则不一致")
    except ValueError as exc:
        errors.append(str(exc))
        expected_sufficient = False

    sufficient = bool(expected_sufficient)

    if metadata.get("is_sufficient_info") is not sufficient:
        errors.append("report_metadata.is_sufficient_info 与任务可判断比例不一致")
    role = profile.get("role", {})
    role_code = role.get("code")
    if not isinstance(role_code, str) or role_code not in ROLE_BY_CODE:
        errors.append("主角色必须从现有 12 类选择，不支持神秘工")
    elif role.get("name") != ROLE_NAMES[role_code] or role.get("tags") != ROLE_BY_CODE[role_code]["tags"]:
        errors.append("主角色 code/name/tags 不符合目录映射")
    _check_required_text(errors, role, ["reason", "snarky_quote"], "profile.role")
    refs = role.get("source_task_ids")
    if not isinstance(refs, list) or not refs or any(not isinstance(x, str) for x in refs) or len(refs) != len(set(refs)):
        errors.append("主角色必须有不重复的来源任务引用")
    if role.get("confidence") not in {"LOW", "MEDIUM", "HIGH"}:
        errors.append("主角色 confidence 必须为 LOW/MEDIUM/HIGH")
    if "is_role_sufficient_info" in metadata or "task_count_role_evaluable" in report["metrics"] or any("role_codes" in t for t in tasks):
        errors.append("5.0 已移除角色命中计数与门槛字段")

    task_id_set = set(task_ids)
    grounded_values: list[tuple[str, dict[str, Any]]] = [("profile.role", role)]
    grounded_values.extend((f"skill_panel.{key}", value) for key, value in report["skill_panel"].items())
    grounded_values.extend((f"human_edge[{index}]", value) for index, value in enumerate(report["human_edge"]))
    grounded_values.extend((f"action_plan.{key}", value) for key, value in report["action_plan"].items())
    for prefix, value in grounded_values:
        for task_id in _refs(value):
            if not isinstance(task_id, str) or task_id not in task_id_set:
                errors.append(f"{prefix} 引用了不存在的任务 {task_id}")

    for key in ("execution", "discretion", "coordination", "accountability"):
        item = report["skill_panel"].get(key, {})
        if item.get("is_known") is False and (item.get("score") is not None or item.get("source_task_ids")):
            errors.append(f"skill_panel.{key} 未知时必须 score=null 且无任务引用")
        if item.get("is_known") is True and not item.get("source_task_ids"):
            errors.append(f"skill_panel.{key} 已知时必须引用任务")

    action_plan = report["action_plan"]
    expected_actions = {"hand_to_ai", "level_up", "proof_7d"}
    if set(action_plan) != expected_actions:
        errors.append("action_plan 必须恰好包含三类行动")
    else:
        titles = []
        for key, action in action_plan.items():
            _check_required_text(
                errors,
                action,
                ["title", "action", "deliverable", "acceptance_criteria", "human_checkpoint", "grounded_evidence"],
                f"action_plan.{key}",
            )
            titles.append(action.get("title"))
            if not _refs(action):
                errors.append(f"action_plan.{key} 必须引用任务证据")
        if len(set(titles)) != 3:
            errors.append("三个升级动作必须不同")

    metrics = report["metrics"]
    share_card = report["share_card"]
    if share_card.get("irreplaceability_index") != metrics.get("irreplaceability_index"):
        errors.append("share_card.irreplaceability_index 与 metrics 不一致")
    if share_card.get("irreplaceability_level") != metrics.get("irreplaceability_level"):
        errors.append("share_card.irreplaceability_level 与 metrics 不一致")
    if share_card.get("role_name") != role.get("name"):
        errors.append("share_card.role_name 与角色不一致")
    share_keys = {"category", "role_name", "role_tags", "confidence_label", "irreplaceability_index", "irreplaceability_level", "snarky_quote", "value_line", "source_task_ids", "disclaimer"}
    if set(share_card) != share_keys:
        errors.append("share_card 必须严格使用脱敏 allowlist 字段")
    _check_required_text(errors, share_card, ["category", "value_line", "disclaimer", "confidence_label"], "share_card")
    if share_card.get("snarky_quote") != role.get("snarky_quote") or share_card.get("role_tags") != role.get("tags"):
        errors.append("分享卡外号文案与角色不一致")
    expected_confidence_label = {"HIGH": "任务依据清楚", "MEDIUM": "按现有任务归类", "LOW": "暂按现有描述归类"}.get(role.get("confidence"))
    if share_card.get("confidence_label") != expected_confidence_label:
        errors.append("分享卡必须如实呈现角色置信度")
    for key, maximum in {"category": 36, "snarky_quote": 80, "value_line": 80, "disclaimer": 100}.items():
        value = share_card.get(key)
        if isinstance(value, str) and len(value) > maximum:
            errors.append(f"share_card.{key} 超过 {maximum} 字，请精简而非截断")
    share_refs = share_card.get("source_task_ids")
    if not isinstance(share_refs, list) or not share_refs or any(not isinstance(x, str) or x not in task_id_set for x in share_refs):
        errors.append("分享卡价值说明必须引用真实任务")
    try:
        assert_share_card_private(share_card, report["source"].get("privacy_entities", []))
    except PrivacyLeakError as exc:
        errors.append(str(exc))

    methodology = report["methodology"]
    disclaimer = methodology.get("custom_rules_disclaimer", "")
    if "自建" not in disclaimer or "不是失业概率" not in disclaimer:
        errors.append("方法声明必须写明自建规则且不是失业概率")
    organizations = {source.get("organization") for source in methodology.get("sources", [])}
    if not {"ILO", "Anthropic"}.issubset(organizations):
        errors.append("方法来源必须包含 ILO 与 Anthropic")
    for source in methodology.get("sources", []):
        _check_required_text(errors, source, ["title", "publication_date", "accessed_at", "url", "boundary"], "methodology.sources")

    if errors:
        raise ReportValidationError(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    assert_valid_report(report)
    print(f"REPORT_VALID path={args.input.resolve()} tasks={len(report['tasks'])} index={report['metrics']['irreplaceability_index']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
