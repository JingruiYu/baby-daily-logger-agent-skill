"""Baby daily log summary helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from baby_daily_logger.core.common import (
    end_of_day,
    start_of_day,
    timestamp_milliseconds,
)
from baby_daily_logger.core.storage import format_time, read_data, records_for_range


def daily_summary(workspace_root: Path, day: datetime) -> str:
    """返回某个本地日期的中文日报总结。"""
    data = read_data(workspace_root)
    start_timestamp = timestamp_milliseconds(start_of_day(day))
    end_timestamp = timestamp_milliseconds(end_of_day(day))
    records = records_for_range(data, start_timestamp, end_timestamp)
    date_text = day.date().isoformat()

    lines = [f"# Baby Daily Logger {date_text} 记录总结", ""]
    feed_records = records["f"]
    total_milk = sum(int(record[1]) for record in feed_records)
    lines.append(f"- 喂奶：{len(feed_records)} 次，共 {total_milk} ml")
    for timestamp, milk in feed_records:
        lines.append(f"  - {format_time(timestamp)}：{milk} ml")

    poop_records = records["p"]
    poop_names = {0: "普通", 1: "稀", 2: "干"}
    lines.append(f"- 大便：{len(poop_records)} 次")
    for timestamp, poop_type in poop_records:
        lines.append(f"  - {format_time(timestamp)}：{poop_names.get(poop_type, poop_type)}")

    sleep_records = records["s"]
    lines.append(f"- 睡眠事件：{len(sleep_records)} 条")
    for timestamp, state in sleep_records:
        lines.append(f"  - {format_time(timestamp)}：{'入睡' if state == 0 else '醒来'}")

    food_meal_records = records["fm"]
    first_food_records = records["fd"]
    if food_meal_records or first_food_records:
        lines.append("- 辅食：")
        for timestamp, food_name in food_meal_records:
            lines.append(f"  - {format_time(timestamp)}：{food_name}")
        for food_name, timestamp in first_food_records:
            lines.append(f"  - {format_time(timestamp)}：首次尝试 {food_name}")

    note_records = records["n"]
    if note_records:
        lines.append("- 小事记：")
        for timestamp, note_text in note_records:
            lines.append(f"  - {format_time(timestamp)}：{note_text}")

    growth_lines = _growth_lines(records)
    if growth_lines:
        lines.append("- 生长记录：")
        lines.extend(growth_lines)

    return "\n".join(lines).strip()


def _growth_lines(records: dict[str, list[list[Any]]]) -> list[str]:
    lines: list[str] = []
    for timestamp, weight in records["w"]:
        lines.append(f"  - {format_time(timestamp)}：体重 {weight} kg")
    for timestamp, height in records["h"]:
        lines.append(f"  - {format_time(timestamp)}：身高 {height} cm")
    return lines
