# BabyEveryThings-compatible JSON schema

The default data object uses compact field names to stay compatible with BabyEveryThings-style exports.

- `v`: schema/app version.
- `b`: baby name or profile field, left empty by default.
- `fr`: feed reminder/status flag.
- `f`: milk feeding records, each `[timestamp_ms, milk_ml]`.
- `p`: poop records, each `[timestamp_ms, poop_type]`; `0` normal, `1` loose, `2` dry.
- `w`: weight records, each `[timestamp_ms, weight_kg]`.
- `h`: height records, each `[timestamp_ms, height_cm]`.
- `s`: sleep state records, each `[timestamp_ms, state]`; `0` asleep, `1` awake.
- `fd`: first solid food tries, each `[food_name, timestamp_ms]`.
- `fm`: solid food meal records, each `[timestamp_ms, food_name]`.
- `n`: notes, each `[timestamp_ms, note_text]`.
- `bath`: bath state, including `lastDate`, `interval`, and `lastTs`.
- `nail`: nail trimming state, including `lastDate`, `interval`, and `lastTs`.
- `reminders`: optional reminder records.

All timestamps are JavaScript-style milliseconds since Unix epoch. The default local timezone is UTC+8.
