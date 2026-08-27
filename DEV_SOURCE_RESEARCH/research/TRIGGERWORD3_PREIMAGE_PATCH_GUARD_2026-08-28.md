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
- exact Git index Stage-0 blob OID and mode for every existing allowed file;
- exact expected-HEAD tree blob OID/type/mode for every existing allowed file;
- Git index blob must equal expected-HEAD tree blob, preventing staged-but-uncommitted basis drift under an unchanged `HEAD`;
- existing preimages must be tracked regular non-executable `100644` blobs;
- explicit `None` preimage only for paths absent from filesystem, Git index **and** expected HEAD;
- path containment and existing-symlink rejection;
- control-character / ambiguous path spelling rejection;
- binary patch rejection;
- rename/copy rejection by default;
- file deletion rejection by default;
- existing-file mode changes rejected;
- new files restricted to regular non-executable mode `100644`, rejecting symlink/submodule/executable-file mode mutations by default;
- bounded patch bytes, touched-file count, additions, deletions and total changed lines;
- actual touched paths must be a subset of the task allowlist;
- `git apply --check --index --whitespace=error-all` must succeed against the exact current index/worktree.

Passing returns `FRANKENSTEIN_PATCH_GUARD_PREFLIGHT/v1` with `applied: false`. It does not modify source, run model/provider code or mint runtime credit.

## Deterministic regression

Local provider-independent regression against the repo-shaped source/test layout after repeated adversarial review:

```text
python -m pytest -q tests/test_frankenstein_patch_guard_v1.py
................                                                         [100%]
16 passed in 0.35s
```

Covered cases include:

1. bounded small patch passes while the target file stays byte-identical because preflight never applies;
2. successful evidence binds Git Stage-0 mode/blob OID and expected-HEAD tree mode/type/blob OID;
3. wrong `HEAD` fails closed;
4. wrong base SHA-256 fails closed;
5. unauthorized touched path fails closed;
6. padded whole-file replacement is rejected by deletion budget even when resulting size is not tiny;
7. a dirty/concurrently changed touched path fails `git apply --check --index` even if the caller updates the policy digest to that dirty working-tree copy;
8. explicitly declared regular new file can be preflighted without creation and must be absent from index and expected HEAD;
9. deletion is forbidden by default;
10. rename is forbidden by default;
11. existing-file mode-only change is forbidden;
12. a new symlink-mode patch is forbidden;
13. task policy paths containing control characters are forbidden;
14. an untracked existing file cannot masquerade as a valid preimage;
15. a tracked executable base is rejected;
16. a staged modified base is rejected even when index and working tree match, and a staged deletion cannot reclassify an expected-HEAD file as `new`.

This is **local deterministic utility-test evidence only**. It is not an EntityOS/HCU runtime test and it does not independently promote the provider-authored direct-dispatch repair.

## Hypothesis and counterhypothesis

**OPEN_HYPOTHESIS — engineering confidence 0.92:** a task-scoped, preimage-bound patch contract that binds expected HEAD, HEAD-tree object, index object and working bytes materially reduces accidental destructive source mutation compared with asking a model to regenerate complete existing files.

**COUNTERHYPOTHESIS:** patch syntax and preimage identity alone are not safe. Broad authorized hunks, over-large deletion budgets, an incorrect allowlist, weak post-apply verification or a malicious/incorrect patch can still destroy semantics while satisfying syntactic preflight. A separate race can also occur **after** this write-free preflight and **before** a later apply unless integration holds a mutation lock or re-verifies the same identities atomically at apply time.

**Falsifier:** a clean non-provider mutation harness produces an unauthorized deletion, stale/untracked/wrong-mode/staged-drift preimage apply, unrelated-path mutation, special-file/mode mutation or lost update that passes this guard under a correctly scoped policy; or matched trials show no meaningful reduction in destructive edits relative to whole-file replacement.

## Remaining integration gates

The guard is deliberately not wired into the live/quarantined dispatcher in this delta. Integration should require, in order:

1. model/helper output changes from whole-file `FILE:` blocks to bounded unified patches or structured edits;
2. policy is derived from the package/task before model execution, not from model output;
3. preimage digests plus expected-HEAD tree and Git-index identity are captured from the exact starting source generation;
4. acquire a bounded repository mutation lock or equivalent serialization primitive;
5. preflight and re-verify the same identities immediately before apply;
6. apply occurs transactionally/with exact rollback handling;
7. resulting changed-file set, mode/type and diff budgets are rechecked post-apply;
8. requested-feature tests plus broader regression/destructive-delta checks pass;
9. only then may a source commit be proposed;
10. independent clean non-provider re-execution is still required before any retained runtime credit under supervisor 9.13Q.

No provider calls, secret lookups, paid execution, Together activity, VPS execution, unusual experiment or Frank Harness modification occurred in this Triggerword-3 delta.
