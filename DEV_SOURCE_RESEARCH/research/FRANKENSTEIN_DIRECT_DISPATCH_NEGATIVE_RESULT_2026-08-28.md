# Frankenstein direct-dispatch destructive rewrite — preserved negative result

**Trigger:** `3` / `triggerword 3`  
**Date of observed incident:** 2026-08-28  
**Curation re-entry head before this write:** `e697e13578aaeccedfa162e93b24690f73cb3ea1`  
**Role:** append-only Trigger-3 research synthesis; this file is **not** an authority surface and grants **no** runtime, provider, HCU, J-Space, training, or whole-product credit.

## Evidence classification

- `NEGATIVE_RESULT`
- `PROJECT_EXECUTABLE_COUNTEREXAMPLE`
- `CURRENT_SOURCE_REPAIR_PRESENT`
- `RETAINED_RUNTIME_CREDIT_BLOCKED_PENDING_INDEPENDENT_NON_PROVIDER_REVIEW_REEXECUTION`

Current authority/evidence must be re-read from `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` and its selected steering before reuse.

## What happened

The first live Frankenstein direct-dispatch attempt on 2026-08-28 exposed a destructive whole-file replacement failure in the provider-authored donor path.

The A1 task asked for a narrow modification to `tools/grid10_fabric.py`, but the direct dispatcher requested **complete file content** from the model without first supplying the actual current file content. The model returned a plausible but incomplete replacement. The observed result recorded by commit `a624461e4745870f918dfee2c541ef046cc93f97` was:

```text
existing file: tools/grid10_fabric.py
before: 672 lines
proposed/replaced result: 87 lines
local VPS commit: dc0c003cd (reported in the repair commit message)
origin impact: contained before push
containment: VPS clone reset to origin/main
```

The critical epistemic point is not the particular line count. It is that a **narrow acceptance criterion can pass while unrelated existing code is silently deleted**.

Therefore:

```text
requested delta is small
+ generated file parses
+ task-local acceptance test passes
!= unchanged regions preserved
!= semantic non-regression
!= safe repository mutation
```

## Why this matters to Project Frankenstein

This counterexample connects several historical Frankenstein failure families that previously looked separate:

1. **Parser/co-author effects:** the transformation layer can materially alter what is evaluated.
2. **Prompt-vs-state mismatch:** asking for a complete artifact without providing the canonical current artifact invites reconstruction from model priors rather than state-bound editing.
3. **Narrow-test Goodharting:** a test focused on the requested feature can miss deletion of unrelated behavior.
4. **TOCTOU/source-identity failures:** correctness requires binding the mutation to the exact pre-edit source identity, not merely a path name.
5. **Effect authority:** a model proposal is a candidate mutation, not permission to replace canonical source.

This is a modern executable instance of the broader historical rule:

```text
model output != repository truth
verification of requested feature != preservation of unrelated invariants
```

## Source repair now present

Commit `a624461e4745870f918dfee2c541ef046cc93f97` added two defenses to the quarantined provider-authored orchestrator donor:

1. `extract_referenced_existing_files(...)` injects current content for referenced existing files into the model prompt.
2. `_looks_like_destructive_truncation(...)` rejects large shrinkage before task-local verification can bless the result.

The same commit added regression tests including a case where the proposed rewrite would satisfy its own acceptance criterion but must still be rejected because it destroys most pre-existing content.

The commit reports `76/76` Frankenstein tests green.

### Evidence boundary

Under Supervisor `9.13Q`, this repair is **useful source evidence but not retained runtime promotion**. The current supervisor explicitly requires independent clean **non-provider** review and re-execution of the destructive-truncation guard and other provider-authored core changes before retained runtime credit.

So the correct state is:

```text
counterexample observed                    = YES
origin damage                              = CONTAINED / NO PUSH REPORTED
source guard present                       = YES
provider-authored local test report        = YES, 76/76 reported by commit
independent clean non-provider revalidation= NOT YET CREDITED BY CURRENT SUPERVISOR
whole Frankenstein runtime pass            = NO
EntityOS whole runtime pass                = NO
HCU full runtime pass                       = NO
training credit                            = 0
```

## Stronger successor invariant: edit-preservation contract

The 50% shrink heuristic is valuable defense-in-depth, but it is not a general proof of safe modification. A destructive change can preserve more than half the bytes, and a legitimate refactor can intentionally shrink more than half.

A stronger general contract for **existing-file modification** is:

```text
PREIMAGE
  exact path
  + exact blob/content hash
  + exact source generation/commit

PROPOSAL
  patch/diff or structured edit operation
  + declared touched regions
  + declared intent

PRESERVATION
  unchanged-region identity or semantic invariants
  + explicit deletion budget / deletion intent
  + path boundary checks

VALIDATION
  requested-feature tests
  + file/module regression tests
  + destructive-delta checks
  + repository cleanliness / expected changed-file set

COMMIT
  only if preimage still matches
  + validation passes
  + resulting changed-file set matches declared scope
```

This binds the **edit** to source identity instead of treating a generated complete file as self-authenticating.

## Hypothesis / counterhypothesis

### H1 — Patch/diff-based editing materially reduces destructive whole-file hallucination

`OPEN_HYPOTHESIS`, engineering confidence: **0.88**.

Reason: patch application naturally constrains edits to declared hunks and exposes deletion size/location, while whole-file generation invites reconstruction of unrelated content.

### Counterhypothesis

Patch generation can still be destructive through broad hunks, incorrect context, intentional deletion, stale preimages, or a patch applier that accepts fuzzy/ambiguous matches. Therefore **patch format alone is insufficient**.

### Cheapest high-information discriminator

On a clean exact-current non-provider checkout, run a deterministic mutation harness over existing files with cases for:

- narrow additive edit;
- proposed 80–90% deletion;
- 40% deletion (below the existing 50% guard threshold);
- deletion plus feature addition where task-local tests pass;
- stale preimage hash;
- wrong path / traversal;
- broad legitimate refactor explicitly declaring deletion intent;
- concurrent/preimage-changing edit between proposal and apply.

Acceptance should require:

1. unauthorized broad deletion is rejected;
2. stale preimage is rejected;
3. unchanged regions remain exact where the edit contract declares them unchanged;
4. task-local tests cannot override preservation failure;
5. no provider calls or secret lookups occur under current HARD_OFF;
6. no runtime/product promotion is granted beyond the exact tested scope.

## Failure-driven architecture move

This incident forces one concrete progression in the Frankenstein engineering lineage:

```text
whole-file model reconstruction
    ↓ executable counterexample
current-content injection + shrink guard
    ↓ still heuristic
preimage-bound patch/diff edit contract
    ↓
changed-region + unchanged-region invariants
    ↓
verify-before-commit with exact source identity
```

That is the research value of the failure: it converts an intuitive safety rule into a falsifiable mutation protocol.

## Source anchors

- `a624461e4745870f918dfee2c541ef046cc93f97` — executable incident report + source repair + reported focused regression suite.
- `94ba128cbd95a3999ccac45421a325ea86570eb8` — Supervisor 9.13Q restores FREE_ONLY/HARD_OFF and quarantines retained runtime credit for provider-authored changes pending independent clean non-provider review/re-execution.
- `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` — current selected authority/frontier surface at the time of this curation pass.
- `research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py` — quarantined donor implementation containing the repair.
- `tests/test_frankenstein_orchestrator_v1.py` — regression tests, including destructive rewrite rejection.

## Non-promotion footer

This note preserves an observed failure and derives a stronger engineering discriminator. It does not reinterpret source presence, reported tests, or containment as integrated runtime acceptance.
