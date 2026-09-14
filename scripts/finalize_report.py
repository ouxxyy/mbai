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

from scripts.display_metrics import to_display_metrics
from scripts.role_match import ROLE_BY_CODE
from scripts.score_report import aggregate_tasks
from scripts.validate_report import ReportValidationError, assert_valid_report
from scripts.version import RULE_VERSION, SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS

DEFAULT_INDEX_NOTE = "分数越高，当前工作越依赖人的判断、协作或现场处理。"
DEFAULT_SITUATION = "先把每项任务说清楚：输入是什么、输出到哪、由谁确认——证据齐了，结论才站得住。"

DEFAULT_METHODOLOGY = {
    "custom_rules_disclaimer": "“工作任务 AI 不可替代指数”是本工具自建的解释性评分：不可替代指数 = 100 − 取整后的任务替代分，分数越高表示工作任务越依赖你本人。它不是失业概率或裁员预测，也不是研究机构对个人的预测或认证。",
    "sources": [
        {
            "organization": "ILO",
            "title": "Generative AI and Jobs: A Refined Global Index of Occupational Exposure",
            "publication_date": "2025-05-20",
            "accessed_at": "2026-09-14",
            "url": "https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure",
            "boundary": "参考如何分析任务可能受到的影响，以及工作如何改变。ILO 的职业暴露梯度不等于个人失业概率；本工具未复现其评分。",
        },
        {
            "organization": "Anthropic",
            "title": "The Anthropic Economic Index",
            "publication_date": "2025-02-10",
            "accessed_at": "2026-09-14",
            "url": "https://www.anthropic.com/research/the-anthropic-economic-index",
            "boundary": "参考如何区分 AI 直接完成任务与人机协作。本链接是 2025 年首期，观察的是 Claude.ai 实际使用，不能代表全部劳动者或所有 AI 的能力。",
        },
    ],
}


def _migrate_draft(draft: dict[str, Any]) -> dict[str, Any]:
    """更新版本；保留模型分类，不机械推测旧角色。"""
    report = deepcopy(draft)
    report["schema_version"] = SCHEMA_VERSION
    report["rule_version"] = RULE_VERSION
    profile = report.setdefault("profile", {})
    profile.setdefault("situation_paragraph", DEFAULT_SITUATION)
    profile.setdefault("index_note", DEFAULT_INDEX_NOTE)
    profile.setdefault("role", {})
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
    # 展示层翻转（3.0.0 起）：替代聚合 → 不可替代指数（唯一翻转点在 display_metrics）。
    metrics = to_display_metrics(metrics)

    # 模型直接选类；不从动词、信号、分数或时间占比重新分类。
    role = report["profile"]["role"]
    code = role.get("code")
    if not isinstance(code, str) or code not in ROLE_BY_CODE or not role.get("reason") or not role.get("source_task_ids"):
        raise ReportValidationError(["ROLE_REANALYSIS_REQUIRED：请由模型从 12 类选择主角色，填写 reason、confidence 和来源任务；不支持神秘工或自动猜测迁移"])
    definition_role = ROLE_BY_CODE[code]
    role["name"] = definition_role["name"]
    role["tags"] = list(definition_role["tags"])
    for task in tasks:
        task.pop("role_codes", None)

    report["tasks"] = tasks
    report["metrics"] = metrics
    report["report_metadata"]["is_sufficient_info"] = is_sufficient
    report["report_metadata"].pop("is_role_sufficient_info", None)

    report["share_card"]["role_name"] = role["name"]
    report["share_card"]["role_tags"] = role["tags"]
    report["share_card"]["snarky_quote"] = role["snarky_quote"]
    report["share_card"]["irreplaceability_index"] = metrics["irreplaceability_index"]
    report["share_card"]["irreplaceability_level"] = metrics["irreplaceability_level"]
    report["share_card"]["confidence_label"] = {"HIGH": "任务依据清楚", "MEDIUM": "按现有任务归类", "LOW": "暂按现有描述归类"}.get(role.get("confidence"), "暂按现有描述归类")
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
