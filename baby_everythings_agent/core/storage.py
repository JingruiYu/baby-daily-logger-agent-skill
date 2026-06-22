"""BabyEveryThings 数据读写、导入导出与变更逻辑。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from baby_everythings_agent.core.common import (
    data_file_path,
    datetime_from_timestamp_milliseconds,
)
from baby_everythings_agent.core.schema import default_data, normalize_data, validate_data

SORTED_RECORD_FIELDS = ["f", "p", "w", "h", "s", "fd", "fm", "n"]


def ensure_data_store(workspace_root: Path) -> Path:
    """确保数据目录和数据文件存在。"""
    path = data_file_path(workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        write_data(workspace_root, default_data())
    return path


def read_data(workspace_root: Path) -> dict[str, Any]:
    """读取 BabyEveryThings 数据；缺文件时创建空数据。"""
    path = ensure_data_store(workspace_root)
    data = json.loads(path.read_text(encoding="utf-8"))
    normalized = normalize_data(data)
    errors = validate_data(normalized)
    if errors:
        raise ValueError("Invalid BabyEveryThings data: " + "; ".join(errors))
    return normalized


def write_data(workspace_root: Path, data: dict[str, Any]) -> None:
    """原子写入 BabyEveryThings 数据。"""
    path = data_file_path(workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_data(data)
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def sort_records(data: dict[str, Any]) -> dict[str, Any]:
    """按时间戳排序记录，同时保持 BabyEveryThings 字段约定。"""
    for field_name in ["f", "p", "w", "h", "s", "fm", "n"]:
        data[field_name] = sorted(data.get(field_name, []), key=lambda record: record[0])
    data["fd"] = sorted(data.get("fd", []), key=lambda record: record[1] if len(record) > 1 else 0)
    return data


def append_record(workspace_root: Path, record: dict[str, Any]) -> dict[str, Any]:
    """追加一条标准化记录到数据文件，并返回已保存记录。"""
    data = read_data(workspace_root)
    record_type = record["type"]
    timestamp = int(record["timestamp_ms"])

    if record_type == "feed":
        data["f"].append([timestamp, int(record["milk_ml"])])
        data["fr"] = 1
    elif record_type == "poop":
        data["p"].append([timestamp, int(record["poop_type"])])
    elif record_type == "weight":
        data["w"].append([timestamp, float(record["weight_kg"])])
    elif record_type == "height":
        data["h"].append([timestamp, float(record["height_cm"])])
    elif record_type == "sleep":
        data["s"].append([timestamp, int(record["sleep_state"])])
    elif record_type == "food_first_try":
        data["fd"].append([str(record["food_name"]), timestamp])
    elif record_type == "food_meal":
        data["fm"].append([timestamp, str(record["food_name"])])
    elif record_type == "note":
        data["n"].append([timestamp, str(record["note_text"])])
    elif record_type == "care":
        care_type = str(record["care_type"])
        if care_type not in {"bath", "nail"}:
            raise ValueError(f"unsupported care type: {care_type}")
        care_date = datetime_from_timestamp_milliseconds(timestamp).date().isoformat()
        data[care_type]["lastDate"] = care_date
        data[care_type]["lastTs"] = timestamp
    else:
        raise ValueError(f"unsupported record type: {record_type}")

    write_data(workspace_root, sort_records(data))
    return record


def records_for_range(
    data: dict[str, Any],
    start_timestamp: int,
    end_timestamp: int,
) -> dict[str, list[list[Any]]]:
    """返回 [start_timestamp, end_timestamp) 范围内的记录。"""
    result: dict[str, list[list[Any]]] = {}
    for field_name in ["f", "p", "w", "h", "s", "fm", "n"]:
        result[field_name] = [
            record for record in data.get(field_name, [])
            if start_timestamp <= int(record[0]) < end_timestamp
        ]
    result["fd"] = [
        record for record in data.get("fd", [])
        if len(record) > 1 and start_timestamp <= int(record[1]) < end_timestamp
    ]
    return result


def load_json_text(text: str) -> dict[str, Any]:
    """加载普通 JSON 或小程序剪贴板分段文本。"""
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty import text")
    if stripped.startswith("[") and "]{" in stripped[:20]:
        parts: list[tuple[int, str]] = []
        for line in stripped.splitlines():
            line = line.strip()
            if not line:
                continue
            if not line.startswith("["):
                continue
            closing = line.find("]")
            index_text = line[1:closing].split("/", maxsplit=1)[0]
            parts.append((int(index_text), line[closing + 1 :]))
        stripped = "".join(part for _, part in sorted(parts))
    return normalize_data(json.loads(stripped))


def import_json_text(workspace_root: Path, text: str) -> dict[str, Any]:
    """把 JSON 文本导入为标准数据文件。"""
    data = load_json_text(text)
    errors = validate_data(data)
    if errors:
        raise ValueError("Invalid BabyEveryThings import: " + "; ".join(errors))
    write_data(workspace_root, sort_records(data))
    return data


def export_json_text(workspace_root: Path) -> str:
    """返回可供小程序导入的紧凑 JSON。"""
    return json.dumps(read_data(workspace_root), ensure_ascii=False, separators=(",", ":"))


def format_time(timestamp: int) -> str:
    """把毫秒时间戳格式化为 HH:MM。"""
    return datetime_from_timestamp_milliseconds(timestamp).strftime("%H:%M")


def iso_datetime(timestamp: int) -> str:
    """把毫秒时间戳格式化为本地 ISO datetime。"""
    return datetime_from_timestamp_milliseconds(timestamp).isoformat()
