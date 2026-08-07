# Dump command smoke contract

CI must prove in an isolated repository copy that a payload placed in `dump/` can be frozen with content hashes, verified unchanged, and moved to `dump archive/<batch_id>/original/` only after a matching `DUMP_RESULT.json` declares `pipeline_complete=true`.

This smoke test validates queue mechanics only. It does not claim that literature research, hypothesis quality, or scientific promotion were validated by the filesystem test.
