"""Baby daily log visualization helpers."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Any

from baby_daily_logger.core.common import (
    data_directory,
    datetime_from_timestamp_milliseconds,
    now_local,
    start_of_day,
    timestamp_milliseconds,
)
from baby_daily_logger.core.storage import read_data
from baby_daily_logger.plotting import save_line_chart


def plot_milk_daily_totals(workspace_root: Path, days: int = 30) -> Path:
    """绘制每日奶量合计图，并返回生成图片路径。"""
    data = read_data(workspace_root)
    end_day = start_of_day(now_local()) + timedelta(days=1)
    start_day = end_day - timedelta(days=days)
    start_timestamp = timestamp_milliseconds(start_day)
    totals: dict[str, int] = defaultdict(int)
    for timestamp, milk in data["f"]:
        if timestamp >= start_timestamp:
            day_key = datetime_from_timestamp_milliseconds(timestamp).date().isoformat()
            totals[day_key] += int(milk)

    labels = [(start_day + timedelta(days=index)).date().isoformat() for index in range(days)]
    values = [totals[label] for label in labels]

    figure_path = data_directory(workspace_root) / "figures" / "milk_daily_totals.png"
    return save_line_chart(
        labels,
        values,
        figure_path,
        title=f"Daily Milk Totals - Last {days} Days",
        ylabel="Milk (ml)",
    )


def plot_weight_trend(workspace_root: Path, days: int = 180) -> Path:
    """绘制体重趋势图，并返回生成图片路径。"""
    data = read_data(workspace_root)
    labels, values = _measurement_series(data.get("w", []), days=days)
    figure_path = data_directory(workspace_root) / "figures" / "weight_trend.png"
    return save_line_chart(
        labels,
        values,
        figure_path,
        title=f"Weight Trend - Last {days} Days",
        ylabel="Weight (kg)",
    )


def plot_height_trend(workspace_root: Path, days: int = 180) -> Path:
    """绘制身高趋势图，并返回生成图片路径。"""
    data = read_data(workspace_root)
    labels, values = _measurement_series(data.get("h", []), days=days)
    figure_path = data_directory(workspace_root) / "figures" / "height_trend.png"
    return save_line_chart(
        labels,
        values,
        figure_path,
        title=f"Height Trend - Last {days} Days",
        ylabel="Height (cm)",
    )


def plot_sleep_daily_hours(workspace_root: Path, days: int = 30) -> Path:
    """根据入睡/醒来事件估算每日睡眠时长并绘图。"""
    data = read_data(workspace_root)
    end_day = start_of_day(now_local()) + timedelta(days=1)
    start_day = end_day - timedelta(days=days)
    daily_hours = _daily_sleep_hours(data.get("s", []), start_day=start_day, days=days)
    labels = [(start_day + timedelta(days=index)).date().isoformat() for index in range(days)]
    values = [round(daily_hours[label], 2) for label in labels]
    figure_path = data_directory(workspace_root) / "figures" / "sleep_daily_hours.png"
    return save_line_chart(
        labels,
        values,
        figure_path,
        title=f"Daily Sleep Hours - Last {days} Days",
        ylabel="Sleep (hours)",
    )


def _measurement_series(records: list[list[Any]], *, days: int) -> tuple[list[str], list[float]]:
    """返回时间窗口内测量记录的标签和值。"""
    start_timestamp = timestamp_milliseconds(start_of_day(now_local()) - timedelta(days=days - 1))
    selected_records = sorted(
        (record for record in records if len(record) >= 2 and int(record[0]) >= start_timestamp),
        key=lambda record: int(record[0]),
    )
    labels = [datetime_from_timestamp_milliseconds(int(record[0])).strftime("%Y-%m-%d") for record in selected_records]
    values = [float(record[1]) for record in selected_records]
    return labels, values


def _daily_sleep_hours(records: list[list[Any]], *, start_day, days: int) -> dict[str, float]:
    """根据睡眠状态切换估算每日睡眠小时数，并按天拆分跨日睡眠。"""
    end_day = start_day + timedelta(days=days)
    start_timestamp = timestamp_milliseconds(start_day)
    end_timestamp = timestamp_milliseconds(end_day)
    sorted_records = sorted(
        (record for record in records if len(record) >= 2),
        key=lambda record: int(record[0]),
    )
    totals: dict[str, float] = defaultdict(float)
    sleep_start_timestamp: int | None = None

    for timestamp, state in sorted_records:
        timestamp = int(timestamp)
        state = int(state)
        if state == 0:
            sleep_start_timestamp = timestamp
            continue
        if state != 1 or sleep_start_timestamp is None:
            continue
        interval_start = max(sleep_start_timestamp, start_timestamp)
        interval_end = min(timestamp, end_timestamp)
        if interval_end > interval_start:
            _add_sleep_interval(totals, interval_start, interval_end)
        sleep_start_timestamp = None

    return totals


def _add_sleep_interval(totals: dict[str, float], start_timestamp: int, end_timestamp: int) -> None:
    """把一段睡眠区间累计到每日小时数中。"""
    current = datetime_from_timestamp_milliseconds(start_timestamp)
    interval_end = datetime_from_timestamp_milliseconds(end_timestamp)
    while current < interval_end:
        next_day = start_of_day(current) + timedelta(days=1)
        segment_end = min(next_day, interval_end)
        day_key = current.date().isoformat()
        totals[day_key] += (segment_end - current).total_seconds() / 3600
        current = segment_end
