"""Semantic validation for the frozen report contract (schema 2.0.0)."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.privacy import PrivacyLeakError, assert_share_card_private
from scripts.role_match import ROLE_NAMES, analyze_roles, match_task_roles
from scripts.score_report import aggregate_tasks

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

    if report.get("schema_version") != "2.0.0" or report.get("rule_version") != "2.0.0":
        errors.append("schema_version 与 rule_version 必须为 2.0.0")

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
            if item.get("role_codes"):
                errors.append(f"{prefix} UNKNOWN 任务不得命中角色")
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

    # —— 角色侧（R1–R4 双门槛）：重算命中并与报告核对 ——
    role_analysis = analyze_roles(tasks)
    role_sufficient = bool(role_analysis["is_role_sufficient"])
    expected_main = role_analysis["main_role"]
    for index, expected_roles in enumerate(role_analysis["task_roles"]):
        if tasks[index].get("role_codes") != expected_roles:
            errors.append(f"tasks[{index}].role_codes 与命中引擎不一致")
    if actual_metrics.get("task_count_role_evaluable") != role_analysis["role_evaluable"]:
        errors.append("metrics.task_count_role_evaluable 与命中引擎不一致")
    if metadata.get("is_sufficient_info") is not sufficient:
        errors.append("report_metadata.is_sufficient_info 与任务可判断比例不一致")
    if metadata.get("is_role_sufficient_info") is not role_sufficient:
        errors.append("report_metadata.is_role_sufficient_info 与主角色门槛不一致")

    role = profile.get("role", {})
    role_code = role.get("code")
    if ROLE_NAMES.get(role_code) != role.get("name"):
        errors.append("角色 code/name 不符合冻结映射")
    if role_sufficient:
        if role_code != expected_main:
            errors.append(f"主角色门槛已过，主角色必须为引擎判定结果 {expected_main}")
    elif role_code != "SHADOW_BEAST":
        errors.append("主角色门槛未过时角色必须为 SHADOW_BEAST（影子兽）")
    if role_code == "SHADOW_BEAST":
        if _refs(role):
            errors.append("影子兽不得引用任务作为角色来源")
        if role.get("tags") != ["证据待补充"]:
            errors.append("影子兽标签必须为 [证据待补充]")
    # R4 不变量：命中任务 ⊆ 暴露可判任务，因此“无指数却有主角色”不允许出现。
    if role_code != "SHADOW_BEAST" and not sufficient:
        errors.append("指数门槛未过时不允许出现主角色（无指数却有主角色）")

    task_id_set = set(task_ids)
    grounded_values: list[tuple[str, dict[str, Any]]] = [("profile.role", role)]
    grounded_values.extend((f"skill_panel.{key}", value) for key, value in report["skill_panel"].items())
    grounded_values.extend((f"human_edge[{index}]", value) for index, value in enumerate(report["human_edge"]))
    grounded_values.extend((f"action_plan.{key}", value) for key, value in report["action_plan"].items())
    for prefix, value in grounded_values:
        for task_id in _refs(value):
            if task_id not in task_id_set:
                errors.append(f"{prefix} 引用了不存在的任务 {task_id}")

    if role_sufficient and role_code != "SHADOW_BEAST":
        expected_sources = [
            task["task_id"] for task in tasks if role_code in match_task_roles(task)
        ]
        if _refs(role) != expected_sources:
            errors.append("主角色 source_task_ids 必须恰好等于该角色命中的任务")

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
    if share_card.get("exposure_index") != metrics.get("exposure_index"):
        errors.append("share_card.exposure_index 与 metrics 不一致")
    if share_card.get("exposure_level") != metrics.get("exposure_level"):
        errors.append("share_card.exposure_level 与 metrics 不一致")
    if share_card.get("role_name") != role.get("name"):
        errors.append("share_card.role_name 与角色不一致")
    highlights = share_card.get("task_highlights")
    if not isinstance(highlights, list) or not 1 <= len(highlights) <= 2:
        errors.append("分享卡必须有 1–2 个任务切片")
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
    print(f"REPORT_VALID path={args.input.resolve()} tasks={len(report['tasks'])} index={report['metrics']['exposure_index']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
