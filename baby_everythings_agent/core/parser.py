"""基于规则的中文育儿记录自然语言解析器。"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from baby_everythings_agent.core.common import LOCAL_TIMEZONE, now_local, timestamp_milliseconds

_DATE_PATTERN = re.compile(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})日?")
_NUMERIC_TIME_PATTERN = re.compile(r"(?:(今天|昨天|前天)\s*)?(早上|上午|中午|下午|晚上|夜里|凌晨)?\s*(\d{1,2})[:：点](\d{1,2})?分?")
_CHINESE_TIME_PATTERN = re.compile(r"(?:(今天|昨天|前天)\s*)?(早上|上午|中午|下午|晚上|夜里|凌晨)?\s*([零一二两三四五六七八九十]{1,3})点(半|[零一二两三四五六七八九十]{1,3}分?)?")
_CHINESE_DIGITS = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_RECORD_SEPARATORS = re.compile(r"[，,；;。\n]+|(?<=\d)\s*又\s*(?=\d|[早上上午中午下午晚上夜里凌晨今昨前])")


def parse_natural_records(text: str, reference_time: datetime | None = None) -> dict[str, Any]:
    """把自然语言文本解析成一条或多条 BabyEveryThings 记录。"""
    reference = reference_time or now_local()
    normalized_text = text.strip()
    if not normalized_text:
        return _missing_result(None, {}, ["record_type"])

    sleep_interval_records = _parse_sleep_interval(normalized_text, reference)
    if sleep_interval_records:
        return {
            "status": "parsed_many",
            "records": sleep_interval_records,
            "summary": "；".join(summarize_record(record) for record in sleep_interval_records),
        }

    clauses = _split_record_clauses(normalized_text)
    if len(clauses) <= 1:
        return parse_natural_record(normalized_text, reference)

    records: list[dict[str, Any]] = []
    summaries: list[str] = []
    inherited_record_type: str | None = None
    for clause in clauses:
        parsed = parse_natural_record(clause, reference, default_record_type=inherited_record_type)
        if parsed["status"] != "parsed":
            # 常见口语会把时间和事件用逗号隔开，例如“10点20，娃睡着了”。
            # 这种情况下整句其实是一条完整记录，不能把前半句当成独立记录追问。
            whole_record = parse_natural_record(normalized_text, reference, default_record_type=inherited_record_type)
            if whole_record["status"] == "parsed":
                return whole_record
            return parsed
        record = parsed["record"]
        inherited_record_type = record["type"]
        records.append(record)
        summaries.append(parsed["summary"])

    return {"status": "parsed_many", "records": records, "summary": "；".join(summaries)}


def parse_natural_record(
    text: str,
    reference_time: datetime | None = None,
    default_record_type: str | None = None,
) -> dict[str, Any]:
    """解析一条自然语言育儿记录，并报告缺失字段。"""
    reference = reference_time or now_local()
    normalized_text = text.strip()
    record_type = _infer_record_type(normalized_text) or default_record_type
    if record_type is None:
        return _missing_result(None, {}, ["record_type"])

    timestamp = _parse_timestamp(normalized_text, reference)
    missing_fields: list[str] = []
    record: dict[str, Any] = {"type": record_type}
    if timestamp is None:
        missing_fields.append("time")
    else:
        record["timestamp_ms"] = timestamp_milliseconds(timestamp)

    _fill_record_fields(record, normalized_text, missing_fields)
    if missing_fields:
        return _missing_result(record_type, record, missing_fields)
    return {"status": "parsed", "record": record, "summary": summarize_record(record)}


def parse_followup_for_pending(text: str, pending_record: dict[str, Any]) -> dict[str, Any]:
    """把用户追答合并进 pending 的部分记录。"""
    normalized_text = text.strip()
    record = dict(pending_record.get("partial_record", {}))
    record_type = record.get("type")
    missing_fields = list(pending_record.get("missing_fields", []))
    if not record_type:
        parsed_record_type = _infer_record_type(normalized_text)
        if parsed_record_type:
            record["type"] = parsed_record_type
            record_type = parsed_record_type
            missing_fields = [field_name for field_name in missing_fields if field_name != "record_type"]

    if "time" in missing_fields:
        timestamp = _parse_timestamp(normalized_text, now_local())
        if timestamp is not None:
            record["timestamp_ms"] = timestamp_milliseconds(timestamp)
            missing_fields.remove("time")

    if record_type:
        before_fields = set(record.keys())
        _fill_record_fields(record, normalized_text, missing_fields)
        after_fields = set(record.keys())
        for field_name in _required_fields_for_type(record_type):
            if field_name in after_fields and field_name not in before_fields and field_name in missing_fields:
                missing_fields.remove(field_name)

    missing_fields = [field_name for field_name in _required_fields_for_type(str(record.get("type", ""))) if field_name not in record]
    if missing_fields:
        return _missing_result(record.get("type"), record, missing_fields)
    return {"status": "parsed", "record": record, "summary": summarize_record(record)}


def summarize_record(record: dict[str, Any]) -> str:
    """为标准化记录生成简短中文确认句。"""
    timestamp_text = datetime.fromtimestamp(record["timestamp_ms"] / 1000, tz=LOCAL_TIMEZONE).strftime("%Y-%m-%d %H:%M")
    record_type = record["type"]
    if record_type == "feed":
        return f"{timestamp_text} 喂奶 {record['milk_ml']}ml"
    if record_type == "poop":
        poop_type_names = {0: "普通大便", 1: "稀便", 2: "干便"}
        return f"{timestamp_text} {poop_type_names.get(record['poop_type'], '大便')}"
    if record_type == "weight":
        return f"{timestamp_text} 体重 {record['weight_kg']}kg"
    if record_type == "height":
        return f"{timestamp_text} 身高 {record['height_cm']}cm"
    if record_type == "sleep":
        return f"{timestamp_text} {'入睡' if record['sleep_state'] == 0 else '醒来'}"
    if record_type == "food_first_try":
        return f"{timestamp_text} 首次尝试辅食：{record['food_name']}"
    if record_type == "food_meal":
        return f"{timestamp_text} 辅食：{record['food_name']}"
    if record_type == "note":
        return f"{timestamp_text} 小事记：{record['note_text']}"
    if record_type == "care":
        return f"{timestamp_text} {'洗澡' if record['care_type'] == 'bath' else '剪指甲'}"
    return f"{timestamp_text} {record_type}"


def _fill_record_fields(record: dict[str, Any], text: str, missing_fields: list[str]) -> None:
    record_type = record["type"]
    if record_type == "feed":
        milk_amount = _parse_milk_amount(text)
        if milk_amount is None:
            _append_missing_field(missing_fields, "milk_ml")
        else:
            record["milk_ml"] = int(round(milk_amount))
    elif record_type == "poop":
        poop_type = _parse_poop_type(text)
        if poop_type is None:
            _append_missing_field(missing_fields, "poop_type")
        else:
            record["poop_type"] = poop_type
    elif record_type == "weight":
        weight = _parse_number_before_units(text, ["kg", "公斤", "千克", "斤"])
        if weight is None:
            _append_missing_field(missing_fields, "weight_kg")
        else:
            if "斤" in text and "公斤" not in text:
                weight = weight / 2
            record["weight_kg"] = round(float(weight), 3)
    elif record_type == "height":
        height = _parse_number_before_units(text, ["cm", "厘米", "公分"])
        if height is None:
            _append_missing_field(missing_fields, "height_cm")
        else:
            record["height_cm"] = round(float(height), 2)
    elif record_type == "sleep":
        sleep_state = _parse_sleep_state(text)
        if sleep_state is None:
            _append_missing_field(missing_fields, "sleep_state")
        else:
            record["sleep_state"] = sleep_state
    elif record_type in {"food_first_try", "food_meal"}:
        food_name = _parse_food_name(text)
        if not food_name:
            _append_missing_field(missing_fields, "food_name")
        else:
            record["food_name"] = food_name
    elif record_type == "note":
        note_text = _parse_note_text(text)
        if not note_text:
            _append_missing_field(missing_fields, "note_text")
        else:
            record["note_text"] = note_text
    elif record_type == "care":
        care_type = _parse_care_type(text)
        if care_type is None:
            _append_missing_field(missing_fields, "care_type")
        else:
            record["care_type"] = care_type


def _infer_record_type(text: str) -> str | None:
    if any(keyword in text for keyword in ["喂奶", "喝奶", "奶量", "吃奶"]):
        return "feed"
    if re.search(r"(喝|吃).{0,4}\d+(?:\.\d+)?\s*(?:ml|毫升|奶)?", text, flags=re.IGNORECASE):
        return "feed"
    if re.search(r"\d+(?:\.\d+)?\s*(?:ml|毫升)\s*奶?", text, flags=re.IGNORECASE):
        return "feed"
    if any(keyword in text for keyword in ["大便", "便便", "拉屎", "粑粑"]):
        return "poop"
    if any(keyword in text for keyword in ["体重", "重了", "称重"]):
        return "weight"
    if any(keyword in text for keyword in ["身高", "身长"]):
        return "height"
    if any(keyword in text for keyword in ["入睡", "睡了", "睡着", "睡觉", "开始睡", "睡到"]):
        return "sleep"
    if any(keyword in text for keyword in ["醒了", "醒来", "睡醒"]):
        return "sleep"
    if any(keyword in text for keyword in ["首次", "第一次", "新食物"]):
        if any(keyword in text for keyword in ["辅食", "吃", "尝试"]):
            return "food_first_try"
    if "辅食" in text:
        return "food_meal"
    if "洗澡" in text or "剪指甲" in text or "指甲" in text:
        return "care"
    if any(keyword in text for keyword in ["记录", "小事", "第一次", "会", "翻身", "抬头"]):
        return "note"
    return None


def _parse_sleep_interval(text: str, reference: datetime) -> list[dict[str, Any]]:
    if "睡到" not in text and "睡至" not in text:
        return []
    split_match = re.split(r"睡到|睡至", text, maxsplit=1)
    if len(split_match) != 2:
        return []
    start_text = split_match[0] + "睡了"
    end_text = split_match[1] + "醒来"
    start_timestamp = _parse_timestamp(start_text, reference)
    end_timestamp = _parse_timestamp(end_text, reference)
    if start_timestamp is None or end_timestamp is None:
        return []
    if end_timestamp <= start_timestamp:
        end_timestamp += timedelta(days=1)
    return [
        {"type": "sleep", "timestamp_ms": timestamp_milliseconds(start_timestamp), "sleep_state": 0},
        {"type": "sleep", "timestamp_ms": timestamp_milliseconds(end_timestamp), "sleep_state": 1},
    ]


def _split_record_clauses(text: str) -> list[str]:
    clauses = [clause.strip() for clause in _RECORD_SEPARATORS.split(text) if clause.strip()]
    return clauses or [text]


def _parse_timestamp(text: str, reference: datetime) -> datetime | None:
    base_date = _parse_base_date(text, reference)
    numeric_time_match = _NUMERIC_TIME_PATTERN.search(text)
    if numeric_time_match:
        day_text, period_text, hour_text, minute_text = numeric_time_match.groups()
        base_date = _base_date_from_day_text(day_text, reference, base_date)
        hour = _adjust_hour_by_period(int(hour_text), period_text)
        minute = int(minute_text or 0)
        return datetime(base_date.year, base_date.month, base_date.day, hour, minute, tzinfo=LOCAL_TIMEZONE)

    chinese_time_match = _CHINESE_TIME_PATTERN.search(text)
    if chinese_time_match:
        day_text, period_text, hour_text, minute_text = chinese_time_match.groups()
        base_date = _base_date_from_day_text(day_text, reference, base_date)
        hour = _adjust_hour_by_period(_chinese_number_to_int(hour_text), period_text)
        minute = _parse_chinese_minute(minute_text)
        return datetime(base_date.year, base_date.month, base_date.day, hour, minute, tzinfo=LOCAL_TIMEZONE)

    if any(keyword in text for keyword in ["刚刚", "刚才", "现在", "这会", "此刻"]):
        return reference
    if _DATE_PATTERN.search(text) or any(keyword in text for keyword in ["今天", "昨天", "前天"]):
        return datetime(base_date.year, base_date.month, base_date.day, reference.hour, reference.minute, tzinfo=LOCAL_TIMEZONE)
    return None


def _parse_base_date(text: str, reference: datetime):
    date_match = _DATE_PATTERN.search(text)
    if date_match:
        return datetime(
            int(date_match.group(1)),
            int(date_match.group(2)),
            int(date_match.group(3)),
            tzinfo=LOCAL_TIMEZONE,
        ).date()
    if "前天" in text:
        return (reference - timedelta(days=2)).date()
    if "昨天" in text:
        return (reference - timedelta(days=1)).date()
    return reference.date()


def _base_date_from_day_text(day_text: str | None, reference: datetime, default_date):
    if day_text == "前天":
        return (reference - timedelta(days=2)).date()
    if day_text == "昨天":
        return (reference - timedelta(days=1)).date()
    return default_date


def _adjust_hour_by_period(hour: int, period_text: str | None) -> int:
    if period_text in {"下午", "晚上", "夜里"} and hour < 12:
        return hour + 12
    if period_text == "中午" and hour < 10:
        return hour + 12
    if period_text == "凌晨" and hour == 12:
        return 0
    return hour


def _parse_chinese_minute(minute_text: str | None) -> int:
    if not minute_text:
        return 0
    if minute_text == "半":
        return 30
    return _chinese_number_to_int(minute_text.replace("分", ""))


def _chinese_number_to_int(text: str) -> int:
    if text in _CHINESE_DIGITS:
        return _CHINESE_DIGITS[text]
    if text == "十":
        return 10
    if text.startswith("十"):
        return 10 + _CHINESE_DIGITS.get(text[1:], 0)
    if "十" in text:
        high_text, low_text = text.split("十", maxsplit=1)
        return _CHINESE_DIGITS.get(high_text, 0) * 10 + (_CHINESE_DIGITS.get(low_text, 0) if low_text else 0)
    return 0


def _parse_milk_amount(text: str) -> float | None:
    amount = _parse_number_before_units(text, ["ml", "毫升", "奶"])
    if amount is not None:
        return amount
    match = re.search(r"(?:喝|吃|喂).{0,3}?(\d+(?:\.\d+)?)", text, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))
    numeric_values = _numbers_not_used_as_time(text)
    if numeric_values:
        return float(numeric_values[-1])
    return None


def _parse_number_before_units(text: str, units: list[str]) -> float | None:
    unit_pattern = "|".join(re.escape(unit) for unit in units)
    match = re.search(rf"(\d+(?:\.\d+)?)\s*(?:{unit_pattern})", text, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _numbers_not_used_as_time(text: str) -> list[float]:
    values: list[float] = []
    for match in re.finditer(r"\d+(?:\.\d+)?", text):
        previous_character = text[match.start() - 1] if match.start() > 0 else ""
        next_character = text[match.end()] if match.end() < len(text) else ""
        if previous_character in {":", "："} or next_character in {":", "：", "点", "分"}:
            continue
        values.append(float(match.group(0)))
    return values


def _parse_poop_type(text: str) -> int | None:
    if any(keyword in text for keyword in ["稀", "水", "软"]):
        return 1
    if any(keyword in text for keyword in ["干", "硬"]):
        return 2
    if any(keyword in text for keyword in ["普通", "正常", "一般"]):
        return 0
    return None


def _parse_sleep_state(text: str) -> int | None:
    if any(keyword in text for keyword in ["入睡", "睡了", "睡着", "睡觉", "开始睡"]):
        return 0
    if any(keyword in text for keyword in ["醒了", "醒来", "睡醒"]):
        return 1
    return None


def _parse_food_name(text: str) -> str:
    cleaned = re.sub(r"(今天|昨天|前天|刚刚|刚才|现在|首次|第一次|尝试|吃了|吃|辅食|记录|宝宝|孩子)", " ", text)
    cleaned = _NUMERIC_TIME_PATTERN.sub(" ", cleaned)
    cleaned = _CHINESE_TIME_PATTERN.sub(" ", cleaned)
    cleaned = _DATE_PATTERN.sub(" ", cleaned)
    return " ".join(cleaned.split()).strip("，。,. ")


def _parse_note_text(text: str) -> str:
    cleaned = re.sub(r"^(记录|小事|宝宝|孩子)[:：，, ]*", "", text.strip())
    return cleaned.strip()


def _parse_care_type(text: str) -> str | None:
    if "洗澡" in text:
        return "bath"
    if "剪指甲" in text or "指甲" in text:
        return "nail"
    return None


def _required_fields_for_type(record_type: str) -> list[str]:
    fields_by_type = {
        "feed": ["type", "timestamp_ms", "milk_ml"],
        "poop": ["type", "timestamp_ms", "poop_type"],
        "weight": ["type", "timestamp_ms", "weight_kg"],
        "height": ["type", "timestamp_ms", "height_cm"],
        "sleep": ["type", "timestamp_ms", "sleep_state"],
        "food_first_try": ["type", "timestamp_ms", "food_name"],
        "food_meal": ["type", "timestamp_ms", "food_name"],
        "note": ["type", "timestamp_ms", "note_text"],
        "care": ["type", "timestamp_ms", "care_type"],
    }
    return fields_by_type.get(record_type, ["type"])


def _append_missing_field(missing_fields: list[str], field_name: str) -> None:
    if field_name not in missing_fields:
        missing_fields.append(field_name)


def _missing_result(record_type: str | None, partial_record: dict[str, Any], missing_fields: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "missing_information",
        "missing_fields": missing_fields,
        "question": _question_for_missing(record_type, missing_fields),
    }
    if record_type:
        result["record_type"] = record_type
    if partial_record:
        result["partial_record"] = partial_record
    return result


def _question_for_missing(record_type: str | None, missing_fields: list[str]) -> str:
    if "record_type" in missing_fields:
        return "你想记录哪一类信息？例如喂奶、大便、睡觉、体重、身高、辅食、小事、洗澡或剪指甲。"
    if "time" in missing_fields:
        return "这条记录发生在什么时候？可以说“刚刚”“今天 10:30”或“昨天 21:00”。"
    if record_type == "feed" and "milk_ml" in missing_fields:
        return "这次喂奶是多少 ml？"
    if record_type == "poop" and "poop_type" in missing_fields:
        return "大便类型是普通、稀，还是干？"
    if record_type == "weight" and "weight_kg" in missing_fields:
        return "体重是多少 kg？"
    if record_type == "height" and "height_cm" in missing_fields:
        return "身高是多少 cm？"
    if record_type == "sleep" and "sleep_state" in missing_fields:
        return "是入睡还是醒来？"
    if "food_name" in missing_fields:
        return "食物名称是什么？"
    if "note_text" in missing_fields:
        return "要记录的小事内容是什么？"
    if "care_type" in missing_fields:
        return "是洗澡还是剪指甲？"
    return "这条记录还缺少信息，请补充一下。"
