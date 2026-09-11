"""Fail-closed privacy checks for the share-card allowlist projection."""

from __future__ import annotations

import json
import re
from typing import Any


PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
CN_ID_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
WECHAT_RE = re.compile(r"(?i)(?:微信|wechat|wx)\s*[:：号]?\s*[a-z][-_a-z0-9]{5,19}")
INJECTION_RE = re.compile(
    r"(?i)(忽略.{0,8}(?:规则|指令|以上)|系统提示词|system\s+prompt|override.{0,8}instruction)"
)


class PrivacyLeakError(ValueError):
    """Raised when a share card contains potentially identifying data."""


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def find_privacy_leaks(share_card: dict[str, Any], privacy_entities: list[str]) -> list[str]:
    text = json.dumps(share_card, ensure_ascii=False, sort_keys=True)
    normalized_text = _normalize(text)
    leaks: list[str] = []

    for entity in privacy_entities:
        if len(_normalize(entity)) >= 2 and _normalize(entity) in normalized_text:
            leaks.append(f"敏感实体：{entity}")
    if PHONE_RE.search(text):
        leaks.append("手机号")
    if EMAIL_RE.search(text):
        leaks.append("邮箱")
    if CN_ID_RE.search(text):
        leaks.append("身份证号")
    if WECHAT_RE.search(text):
        leaks.append("微信号")
    if INJECTION_RE.search(text):
        leaks.append("提示注入内容")
    return sorted(set(leaks))


def assert_share_card_private(share_card: dict[str, Any], privacy_entities: list[str]) -> None:
    leaks = find_privacy_leaks(share_card, privacy_entities)
    if leaks:
        raise PrivacyLeakError("分享卡隐私门禁失败：" + "、".join(leaks))

