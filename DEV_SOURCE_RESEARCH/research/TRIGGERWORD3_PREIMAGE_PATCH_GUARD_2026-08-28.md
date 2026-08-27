# Triggerword 3 — preimage-bound patch guard

**Classification:** `CURRENT_SOURCE` + `LOCAL_DETERMINISTIC_TEST` + `OPEN_INTEGRATION_GATE`  
**Scope:** Frankenstein model-assisted source mutation only.  
**Runtime/product credit added:** `0`.

## Why this exists

Supervisor 9.13Q records executable counterevidence against whole-file model rewrites: the first live direct-dispatch attempted to replace `tools/grid10_fabric.py` with an 87-line fabrication where the real file had 672 lines. The commits were contained before origin push. The subsequent current-content injection and 50%-shrink heuristic are useful defenses, but the supervisor explicitly requires a stronger successor: prefer patch/diff-based modification or prove full-file-hash / unchanged-region invariants.

A length threshold alone is not a general preservation proof. A destructive rewrite can remain above the threshold through padding, same-length substitution or unrelated deletion. Whole-file responses also leave a lost-update/TOCTOU problem if the source used to generate the response is not bound to the source present at apply time.

## New source primitive

`research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_patch_guard_v1.py`

The primitive is intentionally **preflight-only and write-free**. It accepts a unified Git patch plus a task-scoped `PatchPolicy`, then fails closed unless all declared invariants hold:

- exact repository root;
- exact expected Git `HEAD`;
- explicit allowed-path set;
- exact SHA-256 preimage for every existing allowed file;
- explicit `None` preimage only for allowed new files;
- path containment and symlink rejection;
- binary patch rejection;
- rename/copy rejection by default;
- file deletion rejection by default;
- bounded patch bytes, touched-file count, additions, deletions and total changed lines;
- actual touched paths must be a subset of the task allowlist;
- `git apply --check --index --whitespace=error-all` must succeed against the exact current index/worktree.

Passing returns `FRANKENSTEIN_PATCH_GUARD_PREFLIGHT/v1` with `applied: false`. It does not modify source, run model/provider code or mint runtime credit.

## Deterministic regression

Local provider-independent regression against the repo-shaped source/test layout:

```text
python -m pytest -q tests/test_frankenstein_patch_guard_v1.py
.........                                                                [100%]
9 passed in 0.18s
```

Covered cases:

1. bounded small patch passes while the target file stays byte-identical because preflight never applies;
2. wrong `HEAD` fails closed;
3. wrong base SHA-256 fails closed;
4. unauthorized touched path fails closed;
5. padded whole-file replacement is rejected by deletion budget even when resulting size is not tiny;
6. a dirty/concurrently changed touched path fails `git apply --check --index` even if the caller updates the policy digest to that dirty working-tree copy;
7. explicitly declared new file can be preflighted without creation;
8. deletion is forbidden by default;
9. rename is forbidden by default.

This is **local deterministic utility-test evidence only**. It is not an EntityOS/HCU runtime test and it does not independently promote the provider-authored direct-dispatch repair.

## Hypothesis and counterhypothesis

**OPEN_HYPOTHESIS — engineering confidence 0.90:** a task-scoped, preimage-bound patch contract materially reduces accidental destructive source mutation compared with asking a model to regenerate complete existing files.

**COUNTERHYPOTHESIS:** patch syntax alone is not safe. Broad authorized hunks, over-large deletion budgets, an incorrect allowlist, weak post-apply verification or a malicious/incorrect patch can still destroy semantics while satisfying syntactic preflight.

**Falsifier:** a clean non-provider mutation harness produces an unauthorized deletion, stale-preimage apply, unrelated-path mutation or lost update that passes this guard under a correctly scoped policy; or matched trials show no meaningful reduction in destructive edits relative to whole-file replacement.

## Remaining integration gates

The guard is deliberately not wired into the live/quarantined dispatcher in this delta. Integration should require, in order:

1. model/helper output changes from whole-file `FILE:` blocks to bounded unified patches or structured edits;
2. policy is derived from the package/task before model execution, not from model output;
3. preimage digests are captured from the exact starting source generation;
4. preflight passes immediately before apply;
5. apply occurs with rollback/transactional handling;
6. resulting changed-file set and diff budgets are rechecked post-apply;
7. requested-feature tests plus broader regression/destructive-delta checks pass;
8. only then may a source commit be proposed;
9. independent clean non-provider re-execution is still required before any retained runtime credit under supervisor 9.13Q.

No provider calls, secret lookups, paid execution, Together activity, VPS execution, unusual experiment or Frank Harness modification occurred in this Triggerword-3 delta.
