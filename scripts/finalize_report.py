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

from scripts.score_report import aggregate_tasks
from scripts.validate_report import ReportValidationError, assert_valid_report


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


def finalize_report(draft: dict[str, Any]) -> dict[str, Any]:
    report = deepcopy(draft)
    questions = report.get("report_metadata", {}).get("questions_asked", [])
    if not isinstance(questions, list) or len(questions) > 3:
        raise ReportValidationError(["补问最多 3 个"])

    metrics, tasks = aggregate_tasks(report.get("tasks", []))
    is_sufficient = metrics.pop("is_sufficient_info")
    report["tasks"] = tasks
    report["metrics"] = metrics
    report["report_metadata"]["is_sufficient_info"] = is_sufficient

    if not is_sufficient:
        original_quote = report["profile"].get("role", {}).get(
            "snarky_quote", "简历不是沉默，是任务证据还没上线。"
        )
        report["profile"]["role"] = {
            "code": "LOCKED_ROLE",
            "name": "待解锁职业角色",
            "tags": ["证据待补充"],
            "source_task_ids": [],
            "snarky_quote": original_quote,
        }

    role = report["profile"]["role"]
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
