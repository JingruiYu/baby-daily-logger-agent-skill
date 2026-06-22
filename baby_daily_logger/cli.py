"""Command line interface for Baby Daily Logger."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from baby_daily_logger.core.common import LOCAL_TIMEZONE
from baby_daily_logger.core.parser import parse_natural_records
from baby_daily_logger.core.storage import append_record, export_json_text, import_json_text
from baby_daily_logger.core.summary import daily_summary
from baby_daily_logger.core.visualization import (
    plot_height_trend,
    plot_milk_daily_totals,
    plot_sleep_daily_hours,
    plot_weight_trend,
)


def _parse_day(text: str) -> datetime:
    normalized = text.strip().lower()
    current = datetime.now(LOCAL_TIMEZONE)
    if normalized in {"", "today", "今天"}:
        return current
    if normalized in {"yesterday", "昨天"}:
        return current - timedelta(days=1)
    return datetime.strptime(normalized, "%Y-%m-%d").replace(tzinfo=LOCAL_TIMEZONE)


def _cmd_parse(args: argparse.Namespace) -> None:
    parsed = parse_natural_records(args.text)
    if parsed["status"] == "missing_information":
        print("Missing information:", ", ".join(parsed["missing_fields"]))
        print(parsed["question"])
        return
    print(parsed["summary"])


def _cmd_record(args: argparse.Namespace) -> None:
    workspace_root = Path(args.workspace).resolve()
    parsed = parse_natural_records(args.text)
    if parsed["status"] == "missing_information":
        print("Missing information:", ", ".join(parsed["missing_fields"]))
        print(parsed["question"])
        return
    records = parsed["records"] if "records" in parsed else [parsed["record"]]
    for record in records:
        append_record(workspace_root, record)
    print(parsed["summary"])


def _cmd_summary(args: argparse.Namespace) -> None:
    workspace_root = Path(args.workspace).resolve()
    print(daily_summary(workspace_root, _parse_day(args.date)))


def _cmd_export(args: argparse.Namespace) -> None:
    workspace_root = Path(args.workspace).resolve()
    output = export_json_text(workspace_root)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


def _cmd_import(args: argparse.Namespace) -> None:
    workspace_root = Path(args.workspace).resolve()
    text = Path(args.input).read_text(encoding="utf-8")
    data = import_json_text(workspace_root, text)
    print(f"Imported: feeds={len(data['f'])}, poops={len(data['p'])}, sleeps={len(data['s'])}")


def _cmd_visualize(args: argparse.Namespace) -> None:
    workspace_root = Path(args.workspace).resolve()
    if args.chart == "milk_daily_totals":
        figure_path = plot_milk_daily_totals(workspace_root, days=args.days)
    elif args.chart == "weight_trend":
        figure_path = plot_weight_trend(workspace_root, days=args.days)
    elif args.chart == "height_trend":
        figure_path = plot_height_trend(workspace_root, days=args.days)
    elif args.chart == "sleep_daily_hours":
        figure_path = plot_sleep_daily_hours(workspace_root, days=args.days)
    else:
        raise ValueError(f"Unsupported chart: {args.chart}")
    print(figure_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Baby Daily Logger CLI")
    parser.add_argument("--workspace", default=".", help="Workspace directory for data/baby_everythings storage")
    subparsers = parser.add_subparsers(required=True)

    parse_parser = subparsers.add_parser("parse", help="Parse a natural-language record without writing it")
    parse_parser.add_argument("text")
    parse_parser.set_defaults(func=_cmd_parse)

    record_parser = subparsers.add_parser("record", help="Parse and write a natural-language record")
    record_parser.add_argument("text")
    record_parser.set_defaults(func=_cmd_record)

    summary_parser = subparsers.add_parser("summary", help="Show a daily summary")
    summary_parser.add_argument("date", nargs="?", default="today")
    summary_parser.set_defaults(func=_cmd_summary)

    export_parser = subparsers.add_parser("export", help="Export 娃事通-compatible JSON")
    export_parser.add_argument("--output")
    export_parser.set_defaults(func=_cmd_export)

    import_parser = subparsers.add_parser("import", help="Import 娃事通-compatible JSON")
    import_parser.add_argument("input")
    import_parser.set_defaults(func=_cmd_import)

    visualize_parser = subparsers.add_parser("visualize", help="Generate a chart")
    visualize_parser.add_argument("chart", choices=["milk_daily_totals", "weight_trend", "height_trend", "sleep_daily_hours"])
    visualize_parser.add_argument("--days", type=int, default=30)
    visualize_parser.set_defaults(func=_cmd_visualize)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
