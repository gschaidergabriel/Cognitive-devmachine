# Clay Current — fast, token-efficient research state layer

This directory is a **generated current-state cache**, not a second authority.

Purpose: any fresh model/worker should understand the newest research state in seconds without recursively searching the repository.

## Read order

1. `NOW.md` — L0: compact synthesis of all research directions.
2. `INDEX.tsv` — L1: one token-cheap line per direction.
3. `ACTIVE.tsv` — L1: active branch/PR/issue/request refs plus recent repo branches.
4. `RECENT.tsv` — L1: latest commits.
5. `latest/<direction>.md` — L2: compact newest result for one research direction.
6. Only then open the cited original evidence/result artifacts.

Current authority still comes from explicit owner authority + `SUPERVISOR_INBOX.json` + selected steering + exact executable evidence. Generated files here never outrank them.

## Worker write law

Every substantive researcher/worker that creates a material result MUST, in the same work lane, emit a tiny append-only `CLAY_FAST_RESULT/v1` receipt for the affected research direction(s).

Preferred command:

```bash
python3 tools/clay_current_emit_v1.py \
  --direction hcu-grid \
  --status NEEDS_RUNTIME \
  --headline 'Fused GRID10 source ready; exact runtime receipt pending.' \
  --next 'Execute exact pinned source after current authority gates.' \
  --evidence path/to/original_result.json \
  --branch my/work-branch
```

Rules:

- receipts are **append-only**; do not rewrite old receipts;
- keep receipts tiny: summarize the delta, do not duplicate the research artifact;
- cite the exact original result/source/receipt paths;
- if one result materially changes multiple research directions, emit one tiny receipt per affected direction;
- never put secrets, long logs, model transcripts or large payloads in FAST_RESULT receipts;
- never hand-edit generated `NOW.md`, `INDEX.tsv`, `ACTIVE.tsv`, `RECENT.tsv`, `MANIFEST.json` or `latest/*`;
- a branch receipt becomes global current state only after it reaches `main`; recent remote branches are still surfaced in `ACTIVE.tsv` as awareness only;
- a current-cache entry is a navigation/synthesis aid, not promotion evidence.

## Why append-only receipts

All workers editing one global list causes races and accidental state loss. Append-only per-direction receipts allow parallel workers to write independently. `tools/clay_current_refresh_v1.py` deterministically selects the newest committed receipt per direction and builds the top layer.

## Automatic refresh

`.github/workflows/clay-current-index.yml` refreshes the generated layer after normal pushes to `main` and commits only the generated cache delta. It ignores its own generated-cache commits to avoid recursion.

Local workers can refresh immediately with:

```bash
python3 tools/clay_current_refresh_v1.py
```

## Layer model

```text
L0  research_entity/00_CURRENT/NOW.md
      summary of all current directions

L1  INDEX.tsv | ACTIVE.tsv | RECENT.tsv
      cheap scan / branch and work awareness

L2  latest/<direction>.md + .json
      newest compact direction state

L3  updates/<direction>/<immutable receipt>.json
      append-only worker deltas

L4  original research / tests / receipts / source
      full evidence only when needed
```

The upper layers are deliberately lossy summaries. Follow evidence refs downward when a claim matters.
