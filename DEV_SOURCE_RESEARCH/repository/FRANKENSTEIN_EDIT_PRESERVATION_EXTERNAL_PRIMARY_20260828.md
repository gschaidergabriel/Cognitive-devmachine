# External primary anchors — preimage-bound edit preservation

**Trigger-3 role:** external engineering context for `FRANKENSTEIN_DIRECT_DISPATCH_NEGATIVE_RESULT_2026-08-28.md`.  
**Classification:** `EXTERNAL_PRIMARY` + `DESIGN_INPUT`; **not** project runtime evidence.

## Git mechanisms that support the proposed discriminator

Primary documentation checked on 2026-08-28:

- Git `git-apply`: https://git-scm.com/docs/git-apply
- Git `git-diff`: https://git-scm.com/docs/git-diff
- Git `git-hash-object`: https://git-scm.com/docs/git-hash-object

### 1. Applicability can be checked without applying

Git documents `git apply --check` as checking whether a patch is applicable to the current working tree and/or index without applying it.

Design implication for Frankenstein:

```text
model proposes patch
-> parse/path-scope validation
-> git apply --check
-> preservation/deletion-policy checks
-> only then apply
```

Boundary: patch applicability does **not** prove semantic correctness or preservation of unrelated behavior.

### 2. `--index` adds a useful preimage consistency constraint

Git documents that `git apply --index` applies to both index and working tree, and expects the relevant index entries and working-tree copies to be identical in content and metadata; it errors when they differ even if the patch could apply to each in isolation.

This is directly relevant to the 2026-08-28 destructive-rewrite failure because it supplies a built-in stale/preimage mismatch fence that whole-file generation did not have.

Boundary: `--index` consistency is still not the complete project contract; it does not establish task intent, allowed deletion scope, regression safety, or downstream behavior.

### 3. Patch context is a safety input

Git states that normal unified patches are expected to contain context and explicitly discourages context-free patches (`--unidiff-zero`) because context checking provides safety.

Design implication:

- require contextual hunks for ordinary model-authored edits;
- reject or separately authorize zero-context/broad-delete patches;
- bind the patch to the exact pre-edit source identity.

### 4. Patch format can carry blob identity

Git documents that newer diff output can embed index information identifying original blobs, and `--3way` can use recorded blob identity when the original blobs are locally available.

This supports a stronger form of the Trigger-3 proposal:

```text
path name alone
< path + contextual patch
< path + contextual patch + preimage blob identity
< previous + declared edit scope + unchanged-region/policy checks + tests
```

### 5. Exact content identities are available as Git object IDs

`git hash-object` computes the object ID for file content (with documented filtering behavior). This gives the mutation protocol a native way to bind pre/post content identity.

Important boundary: the project should record which representation is hashed (Git-filtered blob vs raw bytes) so an identity receipt is not ambiguous.

### 6. `git diff --check` is useful but narrow

Git documents `git diff --check` as detecting conflict markers and whitespace errors. It is useful as one inexpensive validation stage, but it does **not** detect destructive semantic deletion by itself.

## Resulting Trigger-3 engineering discriminator

The external Git mechanisms support—but do not prove—the proposed architecture:

```text
exact current preimage identity
-> contextual patch with declared scope
-> path-safety validation
-> git apply --check [and index/preimage consistency where appropriate]
-> deletion/unchanged-region policy
-> apply
-> git diff --check
-> requested-feature + regression tests
-> changed-path / diffstat policy
-> commit only on exact-scope PASS
```

Counterhypothesis remains active: a patch can still be semantically destructive, overly broad, malicious, stale, or wrongly scoped. Therefore the patch transport is only one layer; preservation and regression invariants remain necessary.

## Evidence boundary

These are Git's documented mechanisms. They do not establish that the current Frankenstein implementation uses them, that the proposed protocol is implemented, or that it improves safety until a clean exact-current non-provider executable test demonstrates the claimed scope.
