"""Simple synchronous tool functions for agent hosts.

These helpers intentionally avoid any specific agent framework. A host can wrap
these functions as OpenAI tools, MCP tools, Claude Code tools, or custom CLI
commands.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from baby_daily_logger.core.common import LOCAL_TIMEZONE
from baby_daily_logger.core.parser import parse_followup_for_pending, parse_natural_records
from baby_daily_logger.core.pending import (
    DEFAULT_SESSION_KEY,
    clear_pending_record,
    get_pending_record,
    save_pending_record,
)
from baby_daily_logger.core.storage import append_record, export_json_text, import_json_text
from baby_daily_logger.core.summary import daily_summary
from baby_daily_logger.core.visualization import (
    plot_height_trend,
    plot_milk_daily_totals,
    plot_sleep_daily_hours,
    plot_weight_trend,
)


def parse_record(text: str) -> str:
    """Parse a natural-language baby daily record without writing it."""
    parsed = parse_natural_records(text)
    if parsed["status"] == "missing_information":
        return (
            "Missing information; no data was written.\n"
            f"Missing fields: {', '.join(parsed['missing_fields'])}\n"
            f"Follow-up question: {parsed['question']}"
        )
    return f"Parsed but not written: {parsed['summary']}"


def record(
    workspace_root: str | Path,
    text: str,
    *,
    write: bool = False,
    session_key: str = DEFAULT_SESSION_KEY,
) -> str:
    """Parse and optionally write baby daily records.

    Set `write=False` for confirmation-first workflows. Set `write=True` after
    the user confirms the parsed summary.
    """
    root = Path(workspace_root)
    pending_record = get_pending_record(root, session_key)
    parsed = parse_natural_records(text)
    if pending_record and parsed["status"] == "missing_information":
        parsed = parse_followup_for_pending(text, pending_record)

    if parsed["status"] == "missing_information":
        save_pending_record(root, parsed, session_key=session_key, original_text=text)
        return (
            "Missing information; no data was written. A pending record was saved.\n"
            f"Missing fields: {', '.join(parsed['missing_fields'])}\n"
            f"Follow-up question: {parsed['question']}"
        )

    records = parsed["records"] if "records" in parsed else [parsed["record"]]
    if not write:
        return f"Parsed but not written: {parsed['summary']}\nCall again with write=True after confirmation."

    for parsed_record in records:
        append_record(root, parsed_record)
    clear_pending_record(root, session_key)
    return f"Written: {parsed['summary']}"


def query_day(workspace_root: str | Path, date: str = "today") -> str:
    """Return a daily summary for today, yesterday, or YYYY-MM-DD."""
    return daily_summary(Path(workspace_root), _parse_day(date))


def export_data(workspace_root: str | Path) -> str:
    """Return 娃事通-compatible compact JSON."""
    return export_json_text(Path(workspace_root))


def import_data(workspace_root: str | Path, text: str) -> str:
    """Import 娃事通-compatible JSON or segmented clipboard text."""
    data = import_json_text(Path(workspace_root), text)
    return f"Imported: feeds={len(data['f'])}, poops={len(data['p'])}, sleeps={len(data['s'])}"


def visualize(workspace_root: str | Path, chart: str, *, days: int = 30) -> str:
    """Generate a chart and return the generated image path."""
    root = Path(workspace_root)
    if chart == "milk_daily_totals":
        figure_path = plot_milk_daily_totals(root, days=days)
    elif chart == "weight_trend":
        figure_path = plot_weight_trend(root, days=days)
    elif chart == "height_trend":
        figure_path = plot_height_trend(root, days=days)
    elif chart == "sleep_daily_hours":
        figure_path = plot_sleep_daily_hours(root, days=days)
    else:
        raise ValueError(f"Unsupported chart: {chart}")
    return str(figure_path)


def _parse_day(text: str) -> datetime:
    normalized = text.strip().lower()
    current = datetime.now(LOCAL_TIMEZONE)
    if normalized in {"", "today", "今天"}:
        return current
    if normalized in {"yesterday", "昨天"}:
        return current - timedelta(days=1)
    return datetime.strptime(normalized, "%Y-%m-%d").replace(tzinfo=LOCAL_TIMEZONE)
