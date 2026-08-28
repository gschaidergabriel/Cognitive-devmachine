# SAFE EXISTING FILE EDITS

Use this when an AI/tool must change a file that already exists.

**Do not rebuild the whole file from memory for a small edit.**

## Minimal route

1. Find the real repo root. Do not assume Downloads, `$HOME`, attachment path, or current directory.
2. Read current authority. Stop if the requested write is not allowed.
3. Resolve the exact existing file inside the repo. Refuse `..`/absolute path escape.
4. Capture the exact pre-edit identity: current commit/blob and current bytes.
5. For a normal small edit, ask for a **unified diff/patch**, not a complete replacement file.
6. Run `git apply --check` against the expected current source. If it does not apply cleanly: `BLOCKED`.
7. Apply the patch.
8. Inspect the actual changed paths and diff. Refuse undeclared files, deletes, renames, or broad unrelated removal.
9. Run `git diff --check` and the task's real acceptance tests.
10. Commit only if every gate passes.
11. On any failure, restore the exact pre-edit bytes.

## Whole-file replacement

Whole-file replacement is a higher-risk operation. Use it only when the task explicitly requires a rewrite or when the host cannot safely apply a patch.

Then require all of these:

- exact original content was supplied to the editor;
- rewrite permission is explicit;
- changed-path scope is explicit;
- preservation/deletion rules are explicit;
- post-edit diff is inspected;
- broad enough tests cover the rewrite claim;
- exact rollback is available.

A simple file-size threshold is only defense-in-depth. It can miss a harmful smaller deletion and can reject a legitimate large refactor.

## Why this exists

A real 2026-08-28 Frankenstein direct-dispatch tried to make a narrow change to `tools/grid10_fabric.py` and generated an 87-line replacement for a 672-line existing file. The bad local commits were contained/reset before origin push. Current source has additional guards, but retained runtime credit remains unpromoted pending independent clean non-provider review/re-execution.

## Result label

For the edit operation itself:

- `NATIVE` — host provides and you verified the required source-bound patch/write/test/rollback path.
- `ADAPTED` — an adapter provides equivalent verified behavior.
- `DEGRADED` — write is possible but one or more preservation/lifecycle proofs are missing; do not claim full installation success from the edit.
- `BLOCKED` — authority, source identity, safe mutation, verification, or rollback cannot be established.

A successful model response is not a successful edit. A passing narrow test is not proof that unrelated code survived.