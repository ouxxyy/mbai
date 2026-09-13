"""展示层语义翻转的唯一落点（schema 3.0.0）。

内部评分链（score_report.py）保持纯替代语义、零改动：任务级 0/50/100、
时间占比加权、EQUAL_FALLBACK、ROUND_HALF_UP_TO_5 全部不变。
对外展示改为「工作任务 AI 不可替代指数」：

- 唯一换算口径：**先取整、后取补**——显示分 = 100 − round_half_up_to_five(raw)。
  禁止「先取补再取整」（87.5 先补得 12.5 再取整为 15，是错误值；正确为 10）。
- 等级按翻转表镜像：替代 HIGH↔不可替代 LOW、MEDIUM↔MEDIUM、LOW↔HIGH；
  对应展示带域 ≤20 LOW / 25–60 MEDIUM / ≥65 HIGH。
- `raw_score` 字段名与替代语义原样保留，是可追溯性的唯一锚。
- 除本模块外，任何脚本不得出现 100− 取补运算（tests/test_semantic_flip.py 的
  SingleFlipPointTest 用源码扫描锁定这一点）；渲染层禁止二次换算。
"""

from __future__ import annotations

from typing import Any

from scripts.score_report import round_half_up_to_five

LEVEL_FLIP = {
    "LOW": "HIGH",
    "MEDIUM": "MEDIUM",
    "HIGH": "LOW",
    "UNKNOWN": "UNKNOWN",
}

DISPLAY_TRANSFORM_NOTE = "irreplaceability_index = 100 − ROUND_HALF_UP_TO_5(raw_replacement_score)"


def _complement(rounded_value: int) -> int:
    """取补：整个代码库唯一执行 100 − 运算的位置。"""
    return 100 - rounded_value


def to_irreplaceability(raw_score: float) -> int:
    """先取整、后取补：100 − round5(raw)。这是对外换算的唯一入口。"""
    return _complement(round_half_up_to_five(raw_score))


def to_display_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """把 score_report 的替代语义聚合结果翻译为 3.0.0 展示字段。

    输入是 aggregate_tasks 的输出（exposure_index 已按 ROUND_HALF_UP_TO_5 取整、
    exposure_level 为替代等级）；输出重命名为 irreplaceability_*，其余字段原样保留。
    """
    display = {
        key: value
        for key, value in metrics.items()
        if key not in {"exposure_index", "exposure_level"}
    }
    replacement_index = metrics.get("exposure_index")
    display["irreplaceability_index"] = None if replacement_index is None else _complement(replacement_index)
    display["irreplaceability_level"] = LEVEL_FLIP.get(metrics.get("exposure_level"), "UNKNOWN")
    return display
