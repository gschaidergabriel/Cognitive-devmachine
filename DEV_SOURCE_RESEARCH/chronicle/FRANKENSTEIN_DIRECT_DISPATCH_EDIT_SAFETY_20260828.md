# Frankenstein direct-dispatch edit safety — 2026-08-28

**Scope:** Project Frankenstein Triggerword-3 research/evidence synthesis.  
**Base observed before branch:** `e697e13578aaeccedfa162e93b24690f73cb3ea1`.  
**Runtime promotion:** none.

## 1. Current observed evidence

### R0 / CURRENT_SOURCE + NEGATIVE_RESULT

Current `SUPERVISOR_INBOX.json` (schema `9.13`, delta `9.13Q_NON_AUTHORITY`) records a concrete executable counterexample: the first live Frankenstein direct-dispatch on the VPS rewrote `tools/grid10_fabric.py` from **672 lines to 87 lines** while attempting a narrow edit. The local commits were contained and reset before origin push.

The inbox therefore keeps `frankenstein_direct_dispatch_retained_runtime_pass=false` and requires independent clean non-provider review/re-execution before retained runtime credit.

### R0 / CURRENT_SOURCE

Current donor implementation:

`research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py`

At the reviewed source identity, it contains two immediate defenses:

1. `extract_referenced_existing_files()` injects current contents of referenced existing files into the helper prompt.
2. `_looks_like_destructive_truncation()` rejects replacement content below 50% of the previous character length for sufficiently large files.

Current regression source in `tests/test_frankenstein_orchestrator_v1.py` includes a case where a short destructive replacement would satisfy its own `acceptance_criteria="true"` but must still be rejected and leave the original file unchanged.

These are useful defenses. They do **not** establish retained runtime PASS because current supervisor authority explicitly requires independent clean re-review/re-execution of provider-authored Frankenstein core changes.

## 2. Failure mechanism

The failure is not simply “the model made a bad edit.” The mechanism is more specific:

```text
narrow requested change
→ whole-file generation protocol
→ incomplete/no exact preimage supplied to model
→ model reconstructs unseen regions
→ plausible partial file
→ narrow acceptance test may still pass
→ unrelated code can disappear
```

This is a **scope mismatch** between the requested semantic delta and the mutation primitive.

A whole-file replacement asks the generator to reproduce every unchanged byte correctly even when the intended task concerns only a small region. That enlarges the failure surface for no corresponding task benefit.

## 3. Current guard is necessary but insufficient

### Hypothesis H1 — patch-first editing reduces accidental unrelated deletion

**OPEN_HYPOTHESIS — confidence 0.90 (engineering confidence, not runtime credit).**

For modifications to tracked existing text files, defaulting to a bounded patch/diff against an exact preimage should reduce destructive reconstruction failures compared with unconstrained whole-file regeneration.

Primary Git behavior supporting the mechanism:

- `git apply --check` checks whether a patch applies to the current tree/index without applying it.
- `git apply` normally fails the whole patch when a hunk cannot be applied; context-free patches are explicitly discouraged because context is a safety measure.
- `git diff --check` can reject conflict markers/whitespace errors.
- full-index diff form can expose pre/post blob object names, and `git hash-object` computes content object IDs.

These Git properties are mechanisms, not Project-Frankenstein runtime evidence.

### Counterhypothesis C1 — patch syntax alone does not solve destructive edits

A patch can intentionally or accidentally contain a large deletion hunk. If the acceptance test covers only the newly requested behavior, the deletion can still pass.

Therefore:

```text
PATCH_PRESENT != SAFE_EDIT
```

Patch-first must be combined with an edit policy.

### Counterhypothesis C2 — a size threshold can reject legitimate refactors and miss harmful edits

The current 50% shrink guard catches the observed 672→87 failure class, but:

- a harmful edit deleting 40% can pass;
- a small but critical deletion can pass;
- a legitimate explicit rewrite may intentionally exceed the threshold;
- line/character ratio says nothing about semantic preservation.

The size guard is defense-in-depth, not the primary correctness proof.

## 4. Proposed deterministic edit contract

For an existing tracked text file, the default mutation path should be:

```text
1. resolve repo root and exact path
2. capture exact preimage identity
3. require bounded unified diff against that preimage
4. reject paths outside repo root
5. git apply --check against the expected tree/index
6. apply atomically
7. compute post-edit diff
8. enforce declared scope/invariants
9. run claim-matching tests
10. commit only after all gates pass
11. on any failure restore exact preimage
```

### Minimum scope invariants

A package should declare, machine-readably where possible:

- allowed changed paths;
- whether file creation/deletion/rename is allowed;
- expected base commit/blob identity;
- maximum deletion budget or explicit permission for broad rewrite;
- required preserved anchors/regions when the task is additive;
- acceptance command(s);
- clean rollback requirement.

A rewrite outside those declared rights is rejected before commit even if tests pass.

## 5. Higher-information discriminator

The next useful test is adversarial, not another happy-path example.

Construct a fixture with:

- one large existing file containing unrelated functions A, B, C;
- a task requesting only function D;
- acceptance criteria that test only D;
- candidate edits including:
  1. additive patch preserving A/B/C;
  2. patch deleting B/C but adding D;
  3. whole-file replacement retaining >50% length but deleting one critical unrelated function;
  4. stale-base patch generated against the wrong blob;
  5. explicit authorized broad refactor.

Expected result:

- (1) admitted;
- (2) rejected by scope/preservation policy despite target test PASS;
- (3) rejected even though the current 50% guard may miss it;
- (4) rejected by exact-preimage/apply check;
- (5) admitted only with explicit rewrite authority plus broader verification.

This directly discriminates H1 from “50% threshold is enough.”

## 6. Independent execution status in this Trigger-3 organ

An attempt to clone the current repository into the isolated local execution environment failed because the environment could not resolve `github.com` via DNS. That is an **infrastructure/network limitation**, not a product test failure.

Consequently this pass performs independent source review and research synthesis only. It does **not** claim repository-bound re-execution of the 76-test Frankenstein suite and does not satisfy the supervisor's retained-runtime promotion gate.

## 7. Credit boundary

At this frontier:

- direct-dispatch retained runtime PASS: **false**;
- provider execution: **HARD_OFF / not admitted** under current task authority;
- whole EntityOS runtime credit: **0**;
- full HCU runtime credit: **0**;
- Physical GRID10 runtime credit: **0**;
- canonical semantics credit: **0**;
- training credit: **0**.

## 8. Source anchors

Current project anchors:

- `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_9_13Q_DELTA_2026-08-28T0146P0700_GPT56SOL.json`
- `research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py`
- `tests/test_frankenstein_orchestrator_v1.py`
- commit `a624461e4745870f918dfee2c541ef046cc93f97` (reported immediate guard fix; retained runtime credit still withheld by current supervisor)

External primary mechanism references:

- Git `git-apply`: https://git-scm.com/docs/git-apply
- Git `git-diff`: https://git-scm.com/docs/git-diff
- Git `git-hash-object`: https://git-scm.com/docs/git-hash-object

## 9. Synthesis

The durable lesson is not “never let a model edit files.” It is:

> **Match mutation authority to requested semantic scope.**

For a narrow edit, make the default primitive a narrow, source-bound change. Require exact preimage identity, fail-closed application, explicit changed-path/scope rights, claim-matching verification, and exact rollback. Whole-file generation should be an explicit high-authority operation rather than the default implementation path for small modifications.