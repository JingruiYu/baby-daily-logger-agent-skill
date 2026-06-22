# Agent integration

This repo is designed to be used in two ways:

1. As an agent skill described by `SKILL.md`.
2. As a normal Python package that exposes framework-neutral helper functions.

## Python adapter

```python
from baby_everythings_agent.adapters.simple_tools import record, query_day, export_data

workspace = "./demo"

print(record(workspace, "刚刚喝了120奶", write=False))
print(record(workspace, "刚刚喝了120奶", write=True))
print(query_day(workspace, "today"))
print(export_data(workspace))
```

## Confirmation-first pattern

For safety, agent hosts should usually parse first and write only after the user confirms:

1. User: `刚刚喝了120奶`
2. Agent calls `record(workspace, text, write=False)`.
3. Agent shows the parsed summary.
4. User confirms.
5. Agent calls `record(workspace, text, write=True)`.

## Missing information pattern

If the parser returns a missing-information message, ask the follow-up question. The adapter stores a pending record for the session. The next short answer can complete the previous record.

Example:

1. User: `刚刚拉屎了`
2. Agent: `大便类型是普通、稀，还是干？`
3. User: `稀的`
4. Agent writes the completed poop record.

## Data portability

The exported JSON is compact and BabyEveryThings-compatible. This means the agent can be an input layer while the mini-program remains a viewing or legacy data client.
