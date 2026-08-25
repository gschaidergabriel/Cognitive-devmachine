# Research current-state index / fast re-entry

Status: `CURRENT_INFRASTRUCTURE`

Token-efficient current-state pyramid is installed:

- L0 `NOW.md` — whole-project current synthesis;
- L1 `INDEX.tsv` / `ACTIVE.tsv` / `RECENT.tsv` — cheap scan and branch/work awareness;
- L2 `latest/<direction>.md` — newest compact result per direction;
- L3 `updates/<direction>/<FAST_RESULT>.json` — append-only worker deltas;
- L4 exact original research/source/test/receipt evidence.

Every substantive worker is required by `AGENTS.md` and the all-workers directive to emit `CLAY_FAST_RESULT/v1`; `tools/clay_current_emit_v1.py` immediately refreshes the generated cache in that checkout. The GitHub-hosted backup refresh is configured but its first observed run did not produce successful executor evidence, so it is not the sole maintenance mechanism.

Next: all researchers keep emitting small receipts; observe a green backup workflow run before crediting that redundant path as operational.

Evidence:
- `research_entity/00_CURRENT/README.md`
- `tools/clay_current_emit_v1.py`
- `tools/clay_current_refresh_v1.py`
- `AGENTS.md`
- `research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md`
- `research_entity/00_CURRENT/updates/research-current-index/20260826T032200P0700-research-current-index-gpt56sol.json`

> Cache only. Current owner/supervisor/executable evidence outranks this summary.
