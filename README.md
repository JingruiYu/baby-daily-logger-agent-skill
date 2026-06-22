# BabyEveryThings Agent Skill

Natural-language baby care logging with BabyEveryThings-compatible JSON import/export.

This project is not another baby care app. It is a small data bridge and agent skill: you can record baby care events by chatting with an agent, keep the records structured, and export them back to a JSON format compatible with the BabyEveryThings mini-program.

## Why

Baby care records are frequent, tiny, and easy to forget: milk, poop, sleep, solid food, bath, nail trimming, weight, height, and small notes.

A mini-program is useful for viewing and managing records, but real parenting moments are often inconvenient for tapping through UI screens. A natural-language agent input is often faster:

- `刚刚喝了120奶`
- `10点20睡着了，11点05醒了`
- `刚刚拉屎了，是稀的`
- `今天第一次吃了南瓜泥`

The key idea is: use the agent for input, keep the data portable, and preserve compatibility with the existing mini-program data format.

## Features

- Natural-language parsing for common baby care records.
- Missing-field detection and follow-up questions.
- Local JSON storage.
- BabyEveryThings-compatible JSON import/export.
- Daily summaries.
- Optional visualization for milk, growth, and sleep.
- Agent-friendly `SKILL.md`.

## Install

```bash
pip install -e .
```

Optional visualization support:

```bash
pip install -e '.[visualization]'
```

## CLI examples

Parse without writing:

```bash
baby-care-agent parse '刚刚喝了120奶'
```

Record into local storage:

```bash
baby-care-agent --workspace ./demo record '刚刚喝了120奶'
```

Show today's summary:

```bash
baby-care-agent --workspace ./demo summary today
```

Export JSON:

```bash
baby-care-agent --workspace ./demo export --output baby_data_export.json
```

Import JSON:

```bash
baby-care-agent --workspace ./demo import baby_data_export.json
```

## Data location

By default, records are stored under:

```text
data/baby_everythings/baby_data.json
```

inside the selected workspace.

## Agent integration

See `SKILL.md` for agent-facing usage instructions and `docs/agent-integration.md` for framework-neutral Python adapter examples.

## Compatibility note

The JSON schema is intentionally compact and compatible with BabyEveryThings-style exports. See `docs/schema.md` for field details.

## Privacy note

Do not commit real baby care data. The `data/` directory is ignored by default. See `docs/privacy.md` before publishing demos or screenshots.
