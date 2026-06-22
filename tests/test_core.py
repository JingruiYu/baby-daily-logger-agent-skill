from pathlib import Path

from baby_everythings_agent.core.parser import parse_natural_records
from baby_everythings_agent.core.storage import append_record, export_json_text, import_json_text, read_data
from baby_everythings_agent.core.summary import daily_summary


def test_parse_milk_record():
    parsed = parse_natural_records("刚刚喝了120奶")
    assert parsed["status"] == "parsed"
    assert parsed["record"]["type"] == "feed"
    assert parsed["record"]["milk_ml"] == 120


def test_import_export_roundtrip(tmp_path: Path):
    text = '{"v":7,"b":"","fr":0,"f":[],"p":[],"w":[],"h":[],"s":[],"fd":[],"fm":[],"n":[],"bath":{"lastDate":"","interval":2,"lastTs":null},"nail":{"lastDate":"","interval":7,"lastTs":null},"reminders":[]}'
    import_json_text(tmp_path, text)
    exported = export_json_text(tmp_path)
    assert '"v":7' in exported
    assert read_data(tmp_path)["f"] == []


def test_append_and_summary(tmp_path: Path):
    parsed = parse_natural_records("刚刚喝了120奶")
    append_record(tmp_path, parsed["record"])
    summary = daily_summary(tmp_path, __import__("datetime").datetime.now(__import__("datetime").timezone(__import__("datetime").timedelta(hours=8))))
    assert "120 ml" in summary
