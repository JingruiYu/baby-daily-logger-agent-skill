"""BabyEveryThings 工具共享常量与路径 helper。"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from pathlib import Path

DATA_DIRECTORY = Path("data/baby_everythings")
DATA_FILE_NAME = "baby_data.json"
APP_VERSION = 7
LOCAL_TIMEZONE = timezone(timedelta(hours=8))


def data_directory(workspace_root: Path) -> Path:
    """返回工作区下的 BabyEveryThings 数据目录。"""
    return workspace_root / DATA_DIRECTORY


def data_file_path(workspace_root: Path) -> Path:
    """返回 BabyEveryThings 标准数据 JSON 路径。"""
    return data_directory(workspace_root) / DATA_FILE_NAME


def now_local() -> datetime:
    """返回当前北京时间。"""
    return datetime.now(LOCAL_TIMEZONE)


def timestamp_milliseconds(moment: datetime) -> int:
    """把 datetime 转成 JavaScript 风格的毫秒时间戳。"""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=LOCAL_TIMEZONE)
    return int(moment.timestamp() * 1000)


def datetime_from_timestamp_milliseconds(timestamp: int) -> datetime:
    """把 JavaScript 风格的毫秒时间戳转成本地 datetime。"""
    return datetime.fromtimestamp(timestamp / 1000, tz=LOCAL_TIMEZONE)


def start_of_day(moment: datetime) -> datetime:
    """返回给定时间所在本地日期的开始时间。"""
    return datetime.combine(moment.date(), time.min, tzinfo=LOCAL_TIMEZONE)


def end_of_day(moment: datetime) -> datetime:
    """返回给定时间所在本地日期的右开结束时间。"""
    return start_of_day(moment) + timedelta(days=1)
