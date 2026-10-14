# Troubleshooting

The symptom -> cause -> fix table moved into the structured registry (every row is now an entry with root cause,
reuse condition, reference, verification and regression test): **`SOLUTIONS.md`** (generated from `knowledge/solutions.json`).

```
python3 tools/memory/kb.py diagnose error.log     # match an error text against known symptoms
python3 tools/memory/kb.py search tts chunk       # find a solution by words
```

Add a new fix with `kb.py add ENTRY.json` (it refuses duplicates, dangling references and secrets), then `kb.py render`.
Do not add problem rows to this file again - that would duplicate the registry.
