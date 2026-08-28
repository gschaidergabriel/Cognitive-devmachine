# Generation 204 — Stable-ID fix closes positional aliasing, but opens content-prefix aliasing

## Bound evidence

- AgentZero export: `4ef16dc7a86c21b1db6ed6435664e3041802f6a2` (Generation 204)
- Supervisor state before this analysis: `fb37cb498e61855b2d1052c1a096fb12203b2b3e`
- Executable test receipt: `664 green / 1 red`; only persistent red remains `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`.
- Whole-GWT credit remains blocked because Hyperposition/world-model content still bypasses broadcast competition.

## Positive architecture delta

Generation 204 repairs the previously identified `POSITIONAL_ID_ALIASING` defect for non-corpus GWT candidates. Memory, recent-turn, collision, interpretation and self-model candidates no longer use positional identities such as `gedaechtnis:0` or `verlauf:1`. `_kennung(prefix, text)` now derives an identity from normalized content, so ordinary list reordering no longer transfers learned credit to the object that happens to occupy the old slot.

This is real mechanism progress and closes the original slot-permutation failure mode.

## New defect: CONTENT_PREFIX_ID_ALIASING

The replacement identity is still not object-stable in the strong sense required by persistent learning:

```python
kern = " ".join(str(text or "").split()).lower()[:400]
return f"{praefix}:{hashlib.sha1(kern.encode('utf-8')).hexdigest()[:8]}"
```

Two independent alias channels follow.

### 1. Deterministic prefix alias

Any two same-prefix candidates whose normalized first 400 characters are identical receive exactly the same persistent learning key even if their decisive content differs after character 400. This is not a probabilistic hash collision; it is guaranteed by construction.

This matters for precisely the candidate classes used here: durable memories, previous turns, collision summaries, world-model interpretations and self-model claims can share boilerplate/provenance prefixes while differing only later. A learned boost can therefore follow a shared textual prefix rather than the semantic object.

### 2. 32-bit hash namespace

Only eight hexadecimal SHA-1 characters are retained, i.e. a 32-bit identifier inside each prefix namespace. Random collision risk is much lower than the deterministic 400-character alias above, but a long-lived persistent learner should not silently treat a 32-bit digest as object identity.

## Credit boundary

- Positional aliasing fix: **MECHANISM CREDIT = YES**.
- Persistent object-identity credit: **NO** until prefix/truncation and digest-collision falsifiers pass.
- GWT causal/outcome credit: still **0**, independently blocked by the Hyperposition/world-model side channel and endogenous citation reward.

## Highest-information falsifiers

### A. Prefix-twin test

Create two same-source candidates:

- same normalized first 400 characters;
- mutually contradictory answer-bearing suffixes after character 400.

Reward candidate A on turn 1. On turn 2 present candidate B only. Hard invariant: B must not inherit A's learned boost.

Current implementation predicts aliasing and should fail this test.

### B. Stable provenance test

For memory/history/collision/world-model candidates, bind identity to an actual durable object identifier where one exists (`memory_id`, `turn_id`, `relation_id`, episode/checkpoint/source-row id), plus a content/version digest. Reordering, prefix-preserving edits and truncation must not migrate credit between objects.

### C. Mutation semantics test

If the same durable object changes content, define the intended policy explicitly:

- identity stays stable while a version/content digest changes; or
- a new immutable object/version is created.

Do not let content hashing accidentally decide this lifecycle policy.

### D. Collision guard

At candidate admission, detect duplicate persistent IDs within a turn. If two non-identical payload digests map to the same learning key, fail closed for persistent learning and emit an alias receipt instead of applying shared credit.

## Proposed receipt

`GWT_CANDIDATE_IDENTITY_RECEIPT/v1`

Required fields:

- `candidate_id`
- `candidate_kind`
- `durable_object_id` where available
- `source_version_id`
- `full_payload_sha256`
- `identity_material_sha256`
- `identity_algorithm`
- `truncation_applied`
- `collision_detected`
- `learning_key`
- `learning_update_applied`

Hard invariants:

1. distinct durable objects must not share a persistent learning key;
2. prefix-preserving content divergence must not alias;
3. positional reorder must not alter identity;
4. detected collisions disable persistent learning for the conflicting key;
5. learning credit must follow the object/version contract, not list position or text prefix.

## Current frontier

1. Keep `TEST_EXPORT_ATOMIC_RECEIPT/v1` and full exact-source binding as the top acceptance gate.
2. Reproduce the persistent Claude-Code adapter red on exact Ubuntu.
3. Close the Hyperposition/world-model global-workspace bypass with channel lesions.
4. Replace prefix-truncated 32-bit content identities with provenance-bound stable identities plus version digest.
5. Run prefix-twin + reorder + mutation + collision falsifiers before granting persistent GWT-learning credit.

Whole Clay Machine remains **NOT CLAIMED**.