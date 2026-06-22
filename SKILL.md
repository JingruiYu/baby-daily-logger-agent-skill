# BabyEveryThings Agent Skill

Use this skill when the user wants to record, parse, summarize, import, export, or visualize baby care logs from natural language while keeping the data compatible with the BabyEveryThings mini-program JSON format.

## Use cases

- Record baby care events from short natural-language messages.
- Parse a message first and ask for confirmation before writing data.
- Ask a follow-up question when a required field is missing.
- Summarize a day of baby care records.
- Import an existing BabyEveryThings JSON export.
- Export the current data as BabyEveryThings-compatible JSON that can be imported back into the mini-program.
- Generate simple charts for milk totals, growth, and sleep when visualization dependencies are available.

## Supported records

- Milk feeding: amount in milliliters.
- Poop: normal, loose, or dry.
- Sleep state changes: asleep / awake.
- Weight and height measurements.
- Solid food meals and first tries.
- Notes.
- Care events such as bath and nail trimming.

## Typical workflow

1. Parse the user's message with `parse_natural_records`.
2. If the parser returns `missing_information`, ask the returned question.
3. If the user confirms, write the returned record(s) with `append_record`.
4. Use `daily_summary` for date-based summaries.
5. Use `export_json_text` to produce BabyEveryThings-compatible JSON.

## Examples

User: `刚刚喝了120奶`

Expected behavior: parse and optionally write a milk feeding record for the current local time.

User: `10点20睡着了，11点05醒了`

Expected behavior: parse and write two sleep state records.

User: `导出数据给小程序导入`

Expected behavior: call the JSON export path and return/save the generated JSON.

## Privacy

Baby care logs are personal family data. Do not publish real exported JSON files, baby names, birth dates, family identifiers, or chat logs unless the user explicitly asks and understands the privacy impact.
