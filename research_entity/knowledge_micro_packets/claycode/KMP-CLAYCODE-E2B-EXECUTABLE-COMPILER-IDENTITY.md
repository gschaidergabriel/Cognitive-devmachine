# KMP — ClayCode executable compiler loop on E2B

**Evidence class:** remote executable compiler/runtime experiment  
**Primary receipt:** `research_entity/runtime/executable_research_receipts/claycode-e2b-20260808T2034p0700.json`  
**Sandbox:** E2B / `e2b_sandbox` — runtime verified  
**Candidate context:** CC-RC1.5 ICSL + current CC11 multi-rail compiler research  
**Promotion:** none

## What changed

ClayCode now has a working external executable research loop rather than only synthetic/reference execution:

`ClayCode hypothesis -> parser/compiler -> canonical contract -> host lowering -> isolated E2B execution -> counterexample -> compiler/tool repair -> E2B rerun -> durable evidence`.

The first loop produced two separate learnings.

### 1. Research-tooling negative

A one-line E2B smoke test passed, but the first multiline compiler run failed because the repo-runner constructed `python3 -c` with JSON escaping. This proved that a provider smoke test is weaker than a representative workload test.

Repair:
- shell-safe multiline quoting in `research_tool_bridge.py`;
- `run_python()` added to `tools/e2b_sandbox.py` so multiline semantics live in the adapter, not ad-hoc bridge code.

The same compiler workload then passed remotely.

### 2. Semantic identity versus provenance identity

ClayCode-Lab v0.1 compiled and executed correctly but exposed a canonicalization problem:
- reordering independent `hard` constraints changed the sole contract hash;
- duplicating an identical hard constraint also changed it.

Blindly sorting everything would erase useful source/provenance distinctions. ClayCode-Lab v0.2 therefore separates:

- `semantic_hash`: canonical executable meaning; for fields explicitly typed as sets it is reorder-invariant and duplicate-idempotent;
- `contract_hash`: exact committed contract instance; remains bound to Proposal/Adequacy provenance and can differ even when semantic meaning is equal.

E2B v0.2 result:
- semantic hash equal under comments/whitespace, reordered set constraints, and duplicate set constraints;
- contract instance hash equal for parser-inert comments/whitespace but distinct for reordered/duplicated source proposals because their proposal/adequacy ancestry differs;
- generated host process exit code 0;
- effect-critical unknown remained blocked.

## New hypotheses / negatives

### H-CC-EXEC-001
ClayCode should carry separate semantic and provenance/instance identities across contracts, projections and executable lowerings.

**Falsifier:** a formally specified single identity can preserve both semantic equivalence and exact ancestry without false inequality/equality across all required operations.

### N-CC-EXEC-001
A monolithic provenance-bound contract hash is not sufficient as the only semantic-equivalence identity for set-typed semantics.

### N-TOOL-E2B-001
Provider smoke success does not imply representative compiler workload success. Preserve workload-class verification separately.

## Mesh transfer

- **ClayCode:** compiler/type/effect contracts should declare collection semantics (`SET`, `ORDERED`, `MULTISET`, later possibly `WEIGHTED`) explicitly before canonical hashing.
- **ClayGraph:** distinguish semantic entity/relation identity from event/provenance instance identity; do not use one hash for both roles.
- **FRANK:** intent/view equality may use semantic identity while safety/replay retains exact ancestry identity.
- **Hyperposition:** equality and firebreak checks must name the identity axis being compared.
- **GWT/Emergenz:** causal arms should pin semantic identity separately from source/view/provenance identity where either can change outcomes.

## Next executable agenda

1. extend ClayCode-Lab with explicit collection kinds instead of implicit set treatment;
2. fuzz semantic-equivalence transformations and verify semantic-hash invariance;
3. mutate provenance only and verify contract-instance divergence without semantic drift;
4. implement a minimal type/effect checker for CC11 multi-rail boundaries;
5. lower the same ClayCode program to at least two host backends and differential-test outputs once a second multi-language sandbox is available;
6. progressively move compiler rules themselves into ClayCode-defined tables/contracts, while retaining a small trusted bootstrap runtime.
