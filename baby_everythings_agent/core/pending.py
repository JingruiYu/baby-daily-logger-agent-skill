"""BabyEveryThings 多轮补全的持久化 pending 状态。"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from baby_everythings_agent.core.common import data_directory, now_local

PENDING_FILE_NAME = "pending_records.json"
PENDING_EXPIRATION_HOURS = 12
DEFAULT_SESSION_KEY = "default"


def pending_file_path(workspace_root: Path) -> Path:
    """返回 pending 记录 JSON 路径。"""
    return data_directory(workspace_root) / PENDING_FILE_NAME


def read_pending_records(workspace_root: Path) -> dict[str, Any]:
    """读取所有尚未过期的 pending 记录。"""
    path = pending_file_path(workspace_root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    pending_records = data if isinstance(data, dict) else {}
    current_time = now_local()
    active_records: dict[str, Any] = {}
    for session_key, pending_record in pending_records.items():
        if not isinstance(pending_record, dict):
            continue
        expires_at = pending_record.get("expires_at")
        if not isinstance(expires_at, str):
            continue
        try:
            expiration_time = now_local().fromisoformat(expires_at)
        except ValueError:
            continue
        if expiration_time > current_time:
            active_records[session_key] = pending_record
    if active_records != pending_records:
        write_pending_records(workspace_root, active_records)
    return active_records


def write_pending_records(workspace_root: Path, pending_records: dict[str, Any]) -> None:
    """原子写入 pending 记录。"""
    path = pending_file_path(workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(pending_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(path)


def get_pending_record(workspace_root: Path, session_key: str = DEFAULT_SESSION_KEY) -> dict[str, Any] | None:
    """返回指定会话的 pending 记录；不存在则返回 None。"""
    return read_pending_records(workspace_root).get(session_key)


def save_pending_record(
    workspace_root: Path,
    parsed_result: dict[str, Any],
    *,
    session_key: str = DEFAULT_SESSION_KEY,
    original_text: str = "",
) -> None:
    """把一次缺字段解析结果保存为 pending 记录。"""
    current_time = now_local()
    pending_records = read_pending_records(workspace_root)
    pending_records[session_key] = {
        "partial_record": parsed_result.get("partial_record", {}),
        "record_type": parsed_result.get("record_type"),
        "missing_fields": parsed_result.get("missing_fields", []),
        "question": parsed_result.get("question", ""),
        "original_text": original_text,
        "created_at": current_time.isoformat(),
        "expires_at": (current_time + timedelta(hours=PENDING_EXPIRATION_HOURS)).isoformat(),
    }
    write_pending_records(workspace_root, pending_records)


def clear_pending_record(workspace_root: Path, session_key: str = DEFAULT_SESSION_KEY) -> None:
    """删除指定会话的 pending 记录。"""
    pending_records = read_pending_records(workspace_root)
    if session_key in pending_records:
        del pending_records[session_key]
        write_pending_records(workspace_root, pending_records)
