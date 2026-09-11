"""Deterministic scoring for the frozen 1.0.0 exposure rules."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


LEVEL_SCORES = {"LOW": 0, "MEDIUM": 50, "HIGH": 100}


def round_half_up_to_five(value: float | Decimal) -> int:
    """Round a score to the nearest five with exact half values going up."""
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    return int((decimal_value / Decimal("5")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 5)


def _summary_level(index: int | None) -> str:
    if index is None:
        return "UNKNOWN"
    if index <= 35:
        return "LOW"
    if index <= 75:
        return "MEDIUM"
    return "HIGH"


def _validate_time_share(value: Any) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("time_share_percent must be a number or null")
    if value <= 0 or value > 100:
        raise ValueError("time_share_percent must be greater than 0 and at most 100")


def aggregate_tasks(tasks: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Enrich tasks and return the exact aggregate required by the frozen rules."""
    enriched: list[dict[str, Any]] = []
    evaluable_weights: list[Decimal] = []
    weighted_scores: list[Decimal] = []
    has_user_weight = False
    has_equal_weight = False

    for original in tasks:
        item = deepcopy(original)
        level = item.get("exposure_level")
        if level not in {*LEVEL_SCORES, "UNKNOWN"}:
            raise ValueError("exposure_level must be LOW, MEDIUM, HIGH, or UNKNOWN")

        time_share = item.get("time_share_percent")
        _validate_time_share(time_share)

        if level == "UNKNOWN":
            item["score"] = None
            item["effective_weight"] = None
            item["weight_source"] = "NOT_APPLICABLE"
        else:
            item["score"] = LEVEL_SCORES[level]
            if time_share is None:
                weight = Decimal("1")
                item["weight_source"] = "EQUAL_FALLBACK"
                has_equal_weight = True
            else:
                weight = Decimal(str(time_share))
                item["weight_source"] = "USER_CONFIRMED"
                has_user_weight = True
            item["effective_weight"] = float(weight) if weight % 1 else int(weight)
            evaluable_weights.append(weight)
            weighted_scores.append(Decimal(item["score"]) * weight)

        enriched.append(item)

    total = len(enriched)
    evaluable = len(evaluable_weights)
    is_sufficient = total > 0 and evaluable * 2 >= total

    if not evaluable_weights:
        weight_mode = "NOT_APPLICABLE"
    elif has_user_weight and has_equal_weight:
        weight_mode = "MIXED_WEIGHTED"
    elif has_user_weight:
        weight_mode = "USER_WEIGHTED"
    else:
        weight_mode = "EQUAL_WEIGHTED"

    if is_sufficient:
        raw_decimal = sum(weighted_scores, Decimal("0")) / sum(evaluable_weights, Decimal("0"))
        raw_score: float | None = float(raw_decimal)
        exposure_index: int | None = round_half_up_to_five(raw_decimal)
    else:
        raw_score = None
        exposure_index = None

    metrics = {
        "is_sufficient_info": is_sufficient,
        "exposure_index": exposure_index,
        "exposure_level": _summary_level(exposure_index),
        "task_count_total": total,
        "task_count_evaluable": evaluable,
        "weight_mode": weight_mode,
        "rounding_mode": "ROUND_HALF_UP_TO_5",
        "raw_score": raw_score,
    }
    return metrics, enriched
