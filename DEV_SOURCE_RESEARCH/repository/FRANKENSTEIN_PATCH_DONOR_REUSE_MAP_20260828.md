# Frankenstein patch-safety donor reuse map — 2026-08-28

**Trigger:** `3` / `triggerword 3`  
**Classification:** `CURRENT_SOURCE_DONOR_MAPPING` + `INFERENCE`; not runtime acceptance.  
**Rule:** reuse the existing deterministic patch path; do not create a competing patch/execution authority.

## Exact-current donor inspected

At re-entry head `63dc45e09dac9930dd4bf7ca169cf693190b2c71`:

- `tools/free_swarm_patch_pipeline.py`
- `tests/test_free_swarm_patch_pipeline.py`

The patch pipeline explicitly has no provider/network code and delegates exact source rehydration to the existing `forge_source_rehydration` authority.

## Already solved by the donor

The donor already implements several requirements independently derived from the Frankenstein 672→87-line destructive-rewrite counterexample:

| Needed safety property | Existing donor mechanism | Evidence class |
|---|---|---|
| Exact source commit binding | 40-hex `source_head`, commit existence check, detached checkout of exact head | `CURRENT_SOURCE` |
| Exact target source binding | rehydrated `git_blob`, SHA-256, source tree/binding identities | `CURRENT_SOURCE` |
| Actual source shown to patch synthesizer | exact target content capsule | `CURRENT_SOURCE` |
| Path safety | `safe_target(...)` + reject unsafe patch header paths | `CURRENT_SOURCE` |
| Declared target scope | patch-declared paths must equal stage-1 target set | `CURRENT_SOURCE` |
| No fuzzy repair | ordinary apply check; only hunk-count recount normalization is admitted | `CURRENT_SOURCE` |
| Fresh exact-source preflight | local no-hardlinks clone + detached exact source checkout | `CURRENT_SOURCE` |
| Patch applicability | `git apply --check --whitespace=nowarn -` | `CURRENT_SOURCE` |
| Recount repair boundedness | if recount succeeds, regenerate diff then ordinary apply-check again on another fresh exact-source clone | `CURRENT_SOURCE` |
| Regression coverage | tests reject path escape, context mismatch, target-set mismatch and verify exact source/blob prompt binding | `CURRENT_SOURCE_TEST_SOURCE` |

This is materially stronger than the whole-file direct-dispatch design that produced the destructive counterexample.

## What the donor does **not yet prove/implement** for this incident class

Inspection of the current donor and its focused test file did not establish a general policy for:

1. maximum or intent-bound deletion volume;
2. preservation of declared unchanged regions;
3. rejection of a semantically destructive patch that is syntactically applicable and touches only an allowed file;
4. explicit before/after diffstat or removed-line budget;
5. task-local test success being subordinate to preservation-policy failure;
6. concurrent source movement between preflight and the eventual authoritative apply/commit boundary, unless the downstream consumer independently rebinds the exact source identity there.

These are **gaps**, not claims that the donor is unsafe. They define the next discriminator.

## Convergence decision

Do **not** build a second Frankenstein patch executor.

Preferred architecture:

```text
Frankenstein task/proposal
    -> existing forge_source_rehydration authority
    -> existing free_swarm_patch_pipeline exact-source patch synthesis/preflight
    -> NEW narrow preservation policy layer
         - deletion intent/budget
         - unchanged-region or equivalent preservation invariant
         - before/after changed-path + diffstat envelope
         - stale-source rebind at final apply/commit boundary
    -> requested feature + regression tests
    -> existing deterministic effect/commit authority
```

The preservation policy should be a reusable primitive callable by both Free-Swarm/Forge and Frankenstein paths, not a Frankenstein-only fork.

## High-information regression matrix

Add exact-current, provider-free deterministic tests around the donor path:

| Case | Expected |
|---|---|
| one-line additive edit | PASS |
| valid patch deleting ~90% of allowed file without explicit deletion intent | REJECT |
| valid patch deleting ~40% (evades current whole-file 50% shrink heuristic) | REJECT unless policy explicitly permits |
| broad deletion + requested feature where task-local test passes | REJECT |
| stale source/preimage | REJECT |
| context mismatch | already REJECTED by donor; retain regression |
| path escape | already REJECTED by donor; retain regression |
| target-set mismatch | already REJECTED by donor; retain regression |
| legitimate large refactor with explicit bounded deletion intent | PASS only if declared policy + regression suite pass |
| source moves after preflight before final apply | REJECT/re-preflight against new exact identity |

## Hypothesis update

Previous hypothesis: preimage-bound patch/diff editing materially reduces destructive whole-file hallucination.

After donor inspection:

- mechanism availability confidence: **high** — the repository already contains most of the deterministic transport/preflight primitive;
- safety-effect hypothesis remains **unverified** until the destructive-deletion matrix is executed at exact current identity;
- implementation recommendation changes from **build patch path** to **reuse donor + add preservation policy + rebind at final effect boundary**.

## Evidence boundary

Source inspection and test-source inspection are not execution evidence. No test suite was executed by this curation organ. No provider, network, secret, training, VPS or unusual-experiment action was performed. Whole EntityOS/HCU, HCU, J-Space, provider and training credit remain unchanged.
