"""Command line interface for baby-everythings-agent-skill."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from baby_everythings_agent.core.common import LOCAL_TIMEZONE
from baby_everythings_agent.core.parser import parse_natural_records
from baby_everythings_agent.core.storage import append_record, export_json_text, import_json_text
from baby_everythings_agent.core.summary import daily_summary


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


def main() -> None:
    parser = argparse.ArgumentParser(description="BabyEveryThings-compatible baby care agent CLI")
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

    export_parser = subparsers.add_parser("export", help="Export BabyEveryThings-compatible JSON")
    export_parser.add_argument("--output")
    export_parser.set_defaults(func=_cmd_export)

    import_parser = subparsers.add_parser("import", help="Import BabyEveryThings-compatible JSON")
    import_parser.add_argument("input")
    import_parser.set_defaults(func=_cmd_import)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
