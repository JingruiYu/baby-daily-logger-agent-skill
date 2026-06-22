# Baby Daily Logger Agent Skill

Use this skill when the user wants to record, parse, summarize, import, export, or visualize baby daily logs from natural language.

当用户想用自然语言记录、查询、导入、导出或可视化宝宝起居时，使用这个 skill。

This skill exports JSON compatible with the 娃事通 WeChat mini-program format.

本 skill 可导出兼容娃事通微信小程序的 JSON。

## Common user intents / 常见意图

- “刚刚喝了120奶” → parse or write a milk record.
- “10点20睡着了，11点05醒了” → write sleep state records.
- “刚刚拉屎了” → ask poop type if missing.
- “查一下今天” → show today's summary.
- “导出给小程序” → export 娃事通-compatible JSON.
- “画一下最近奶量” → generate a chart.

## CLI usage / 命令行用法

Install first:

```bash
pip install -e .
```

Parse only, without writing:

```bash
baby-daily-logger parse '刚刚喝了120奶'
```

Write a record:

```bash
baby-daily-logger --workspace ./demo record '刚刚喝了120奶'
```

Show a daily summary:

```bash
baby-daily-logger --workspace ./demo summary today
baby-daily-logger --workspace ./demo summary yesterday
baby-daily-logger --workspace ./demo summary 2026-06-22
```

Export JSON for 娃事通 import:

```bash
baby-daily-logger --workspace ./demo export --output baby_data_export.json
```

Import JSON:

```bash
baby-daily-logger --workspace ./demo import baby_data_export.json
```

Visualize records:

```bash
baby-daily-logger --workspace ./demo visualize milk_daily_totals --days 30
baby-daily-logger --workspace ./demo visualize weight_trend --days 180
baby-daily-logger --workspace ./demo visualize height_trend --days 180
baby-daily-logger --workspace ./demo visualize sleep_daily_hours --days 30
```

## Python adapter usage / Python 适配层用法

Use these framework-neutral helpers when wrapping the skill as tools in an agent host:

```python
from baby_daily_logger.adapters.simple_tools import (
    export_data,
    import_data,
    parse_record,
    query_day,
    record,
    visualize,
)

workspace = "./demo"

print(parse_record("刚刚喝了120奶"))
print(record(workspace, "刚刚喝了120奶", write=False))
print(record(workspace, "刚刚喝了120奶", write=True))
print(query_day(workspace, "today"))
print(export_data(workspace))
print(visualize(workspace, "milk_daily_totals", days=30))
```

## Confirmation-first workflow / 推荐确认流程

For safety, parse first and write only after user confirmation.

为了避免误写，建议先解析，用户确认后再写入。

1. User: `刚刚喝了120奶`
2. Agent calls `record(workspace, text, write=False)`.
3. Agent shows the parsed summary.
4. User confirms.
5. Agent calls `record(workspace, text, write=True)`.

## Missing-information workflow / 缺信息追问

If the parser returns missing information, ask the returned follow-up question. The skill stores a pending record for the session.

如果缺字段，就追问返回的问题。skill 会保存 pending 记录，用户下一句话可以补全。

Example:

1. User: `刚刚拉屎了`
2. Agent: `大便类型是普通、稀，还是干？`
3. User: `稀的`
4. Agent writes the completed poop record.

## Code structure / 代码结构

- `baby_daily_logger/cli.py`: command line entry point.
- `baby_daily_logger/adapters/simple_tools.py`: simple functions for agent hosts.
- `baby_daily_logger/core/parser.py`: natural-language parser.
- `baby_daily_logger/core/pending.py`: pending state for follow-up answers.
- `baby_daily_logger/core/schema.py`: JSON schema defaults and validation.
- `baby_daily_logger/core/storage.py`: local storage, import, export, append.
- `baby_daily_logger/core/summary.py`: daily summary.
- `baby_daily_logger/core/visualization.py`: chart data aggregation.
- `baby_daily_logger/plotting.py`: matplotlib chart writer.

## Privacy / 隐私

Do not publish real baby data, screenshots, names, birth dates, bot tokens, mini-program IDs, or exported JSON unless the user explicitly approves.

不要公开真实宝宝数据、截图、姓名、出生日期、机器人 token、小程序 ID 或导出 JSON，除非用户明确确认。
