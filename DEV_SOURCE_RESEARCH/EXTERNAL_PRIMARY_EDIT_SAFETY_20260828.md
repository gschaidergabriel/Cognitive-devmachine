# External primary note — bounded edit safety for Frankenstein

This note is `EXTERNAL_PRIMARY` context plus project-side inference. It is **not** EntityOS/Frankenstein runtime evidence.

## Git patch applicability

Primary Git documentation: <https://git-scm.com/docs/git-apply>

The current Git 2.55 documentation states that `git apply --check` checks whether a patch applies to the current working tree/index without applying it. Git also documents context-bearing unified diffs as a safety measure and discourages context-free patches. This supports a project rule that an edit should be checked against the intended preimage instead of treating generated complete-file content as self-authenticating.

Project boundary: patch applicability is not semantic correctness. A broad but syntactically applicable patch can still delete required behavior. Frankenstein therefore needs exact preimage identity, declared scope, changed-file-set closure and regression checks in addition to patch applicability.

## JSON Patch

Primary standard: RFC 6902, *JavaScript Object Notation (JSON) Patch*.

RFC 6902 defines an ordered sequence of operations such as `test`, `add`, `remove`, `replace`, `move`, and `copy` against a target JSON document. The standard's examples show `test`-style preconditions and HTTP conditional use as mechanisms for bounded partial update semantics.

Project boundary: RFC 6902 does not grant repository authority and does not prove a patch preserves project semantics. It is a structured-edit donor pattern only.

## Transfer rule into Project Frankenstein

```text
external mechanism
  -> exact preimage / target binding
  -> explicit partial operation
  -> applicability/precondition failure closes the edit

project additions
  -> repository-relative normalized path
  -> declared touched preimage region(s)
  -> exact changed-file set
  -> deletion intent/budget as defense in depth
  -> requested-feature + regression checks
  -> deterministic postimage hash
  -> verify-before-commit
```

The 2026-08-28 `672 -> 87` destructive direct-dispatch incident is project evidence for the need; Git/RFC material only informs the mechanism design.
