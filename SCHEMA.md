# 娃事通兼容 JSON Schema

This file explains the compact JSON format used by this skill.

这里说明本 skill 使用的紧凑 JSON 字段。它用于兼容娃事通微信小程序的导入 / 导出格式。

- `v`: schema/app version. 版本号。
- `b`: baby profile field, empty by default. 宝宝信息字段，默认留空。
- `fr`: feed reminder/status flag. 喂奶相关状态字段。
- `f`: milk records, each `[timestamp_ms, milk_ml]`. 喂奶记录。
- `p`: poop records, each `[timestamp_ms, poop_type]`; `0` normal, `1` loose, `2` dry. 大便记录。
- `w`: weight records, each `[timestamp_ms, weight_kg]`. 体重记录。
- `h`: height records, each `[timestamp_ms, height_cm]`. 身高记录。
- `s`: sleep state records, each `[timestamp_ms, state]`; `0` asleep, `1` awake. 睡眠状态记录。
- `fd`: first solid food tries, each `[food_name, timestamp_ms]`. 首次尝试辅食。
- `fm`: solid food meals, each `[timestamp_ms, food_name]`. 辅食餐。
- `n`: notes, each `[timestamp_ms, note_text]`. 小事记录。
- `bath`: bath state, including `lastDate`, `interval`, and `lastTs`. 洗澡状态。
- `nail`: nail trimming state, including `lastDate`, `interval`, and `lastTs`. 剪指甲状态。
- `reminders`: optional reminders. 提醒项。

All timestamps are JavaScript-style milliseconds since Unix epoch. The default local timezone is UTC+8.

所有时间戳都是 JavaScript 风格的毫秒时间戳。默认本地时区是 UTC+8。
