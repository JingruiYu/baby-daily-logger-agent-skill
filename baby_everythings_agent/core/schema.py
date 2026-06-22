"""BabyEveryThings v7 数据 schema helper。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from baby_everythings_agent.core.common import APP_VERSION


def default_data() -> dict[str, Any]:
    """返回一个兼容 BabyEveryThings v7 的空数据对象。"""
    return {
        "v": APP_VERSION,
        "b": "",
        "fr": 0,
        "f": [],
        "p": [],
        "w": [],
        "h": [],
        "s": [],
        "fd": [],
        "fm": [],
        "n": [],
        "bath": {"lastDate": "", "interval": 2, "lastTs": None},
        "nail": {"lastDate": "", "interval": 7, "lastTs": None},
        "reminders": [],
    }


def normalize_data(data: dict[str, Any]) -> dict[str, Any]:
    """补齐缺失字段，并尽量保留未知键。"""
    normalized = deepcopy(default_data())
    normalized.update(data)
    normalized["v"] = APP_VERSION
    for key in ["f", "p", "w", "h", "s", "fd", "fm", "n", "reminders"]:
        if not isinstance(normalized.get(key), list):
            normalized[key] = []
    for key, interval in [("bath", 2), ("nail", 7)]:
        value = normalized.get(key)
        if not isinstance(value, dict):
            value = {}
        normalized[key] = {
            "lastDate": value.get("lastDate", ""),
            "interval": value.get("interval", interval),
            "lastTs": value.get("lastTs"),
        }
    return normalized


def validate_data(data: dict[str, Any]) -> list[str]:
    """返回数据对象的人类可读校验错误。"""
    errors: list[str] = []
    if data.get("v") != APP_VERSION:
        errors.append(f"version should be {APP_VERSION}, got {data.get('v')!r}")
    array_fields = ["f", "p", "w", "h", "s", "fd", "fm", "n"]
    for field_name in array_fields:
        if not isinstance(data.get(field_name), list):
            errors.append(f"{field_name} should be a list")
    return errors
