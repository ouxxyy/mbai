"""Turn a Claude-authored draft into a deterministic, validated final report."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.role_match import ROLE_BY_CODE, SHADOW_BEAST, analyze_roles
from scripts.score_report import aggregate_tasks
from scripts.validate_report import ReportValidationError, assert_valid_report

SUPPORTED_SCHEMA_VERSIONS = ("1.0.0", "2.0.0")
DEFAULT_INDEX_NOTE = "替代指数量的是任务，不是人。"
DEFAULT_SITUATION = "先把每项任务说清楚：输入是什么、输出到哪、由谁确认——证据齐了，结论才站得住。"

DEFAULT_METHODOLOGY = {
    "custom_rules_disclaimer": "“工作任务 AI 替代指数”是本工具自建的解释性评分：不是失业概率或裁员预测，也不是研究机构对个人的预测或认证。",
    "sources": [
        {
            "organization": "ILO",
            "title": "Generative AI and Jobs: A Refined Global Index of Occupational Exposure",
            "publication_date": "2025-05-20",
            "accessed_at": "2026-09-11",
            "url": "https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure",
            "boundary": "借鉴任务级暴露与工作转型视角；ILO 形成的是职业暴露梯度和全球估计，本工具个人分数为自建规则。",
        },
        {
            "organization": "Anthropic",
            "title": "The Anthropic Economic Index",
            "publication_date": "2025-02-10",
            "accessed_at": "2026-09-11",
            "url": "https://www.anthropic.com/research/the-anthropic-economic-index",
            "boundary": "借鉴任务级分析及 automation/augmentation 区分；Claude.ai 使用数据不代表个人失业概率或全部 AI 使用。",
        },
    ],
}


def _migrate_draft(draft: dict[str, Any]) -> dict[str, Any]:
    """读时迁移：1.0.0 草稿 → 2.0.0（角色由引擎按任务证据重判，旧六角色码弃用）。

    指数字段（tasks 的 level/score/权重、metrics 聚合）原样保留，聚合语义未动。
    """
    report = deepcopy(draft)
    report["schema_version"] = "2.0.0"
    report["rule_version"] = "2.0.0"
    profile = report.setdefault("profile", {})
    profile.setdefault("situation_paragraph", DEFAULT_SITUATION)
    profile.setdefault("index_note", DEFAULT_INDEX_NOTE)
    role = profile.setdefault("role", {})
    # 旧六角色与任何上游自报角色都不再信任，统一由引擎按 R1–R5 重判。
    role.pop("code", None)
    role.pop("name", None)
    return report


def finalize_report(draft: dict[str, Any]) -> dict[str, Any]:
    version = draft.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ReportValidationError([f"不支持的 schema_version：{version}（支持 {', '.join(SUPPORTED_SCHEMA_VERSIONS)}）"])
    report = _migrate_draft(draft)

    questions = report.get("report_metadata", {}).get("questions_asked", [])
    if not isinstance(questions, list) or len(questions) > 3:
        raise ReportValidationError(["补问最多 3 个"])

    metrics, tasks = aggregate_tasks(report.get("tasks", []))
    is_sufficient = metrics.pop("is_sufficient_info")

    # 角色匹配引擎（R1–R4）：任务级命中 + 双门槛。
    role_analysis = analyze_roles(tasks)
    role_sufficient = role_analysis["is_role_sufficient"]
    main_role_code = role_analysis["main_role"]
    for task, hit_codes in zip(tasks, role_analysis["task_roles"]):
        task["role_codes"] = hit_codes

    metrics["task_count_role_evaluable"] = role_analysis["role_evaluable"]

    role = report["profile"]["role"]
    role.setdefault("snarky_quote", DEFAULT_INDEX_NOTE)
    if role_sufficient and main_role_code:
        definition_role = ROLE_BY_CODE[main_role_code]
        role["code"] = definition_role["code"]
        role["name"] = definition_role["name"]
        role["tags"] = list(definition_role["tags"])
        role["source_task_ids"] = [
            task["task_id"] for task, hits in zip(tasks, role_analysis["task_roles"]) if main_role_code in hits
        ]
    else:
        # 主角色门槛未过 → 影子兽（R4 角色侧）。指数门槛独立判断，两者可并存。
        original_quote = role.get("snarky_quote", "证据不够，不下结论。")
        role["code"] = SHADOW_BEAST["code"]
        role["name"] = SHADOW_BEAST["name"]
        role["tags"] = list(SHADOW_BEAST["tags"])
        role["source_task_ids"] = []
        role.setdefault("snarky_quote", original_quote)

    report["tasks"] = tasks
    report["metrics"] = metrics
    report["report_metadata"]["is_sufficient_info"] = is_sufficient
    report["report_metadata"]["is_role_sufficient_info"] = role_sufficient

    report["share_card"]["role_name"] = role["name"]
    report["share_card"]["role_tags"] = role["tags"]
    report["share_card"]["snarky_quote"] = role["snarky_quote"]
    report["share_card"]["exposure_index"] = metrics["exposure_index"]
    report["share_card"]["exposure_level"] = metrics["exposure_level"]
    report["methodology"] = deepcopy(DEFAULT_METHODOLOGY)

    assert_valid_report(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Claude-authored draft JSON")
    parser.add_argument("--output", type=Path, required=True, help="Validated final JSON")
    args = parser.parse_args()

    draft = json.loads(args.input.read_text(encoding="utf-8"))
    report = finalize_report(draft)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
