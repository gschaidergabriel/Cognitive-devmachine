# ClayCode Multiworker Contribution — Lane B: Compiler / Runtime Lowering

**coordination_id:** `claycode-multiworker-20260809T0128p0700`  
**worker:** `chatgpt-secondary-r5` · OpenAI · GPT-5.6 Sol  
**worker run:** `claycode-20260809T0130p0700-chatgpt-secondary-r5`  
**lane:** `B_COMPILER_RUNTIME_LOWERING`  
**parent:** CC13 / `CC-RC1.8 MCAAT`  
**shared candidate read:** Lane A `CC-RC1.9 UECC`  
**Lane-B local subcandidate:** CBEL-TV, reclassified here as a **lowering refinement of UECC**, not a competing CC-RC1.9 generation.

## Cross-read verdict

Lane B accepts Lane A's correction:

> `computational expressibility != effect authority`

A genuinely general ClayCode may represent destructive, administrative, raw-memory, device and foreign effects as typed requests. FRANK's untrusted profile should normally lack the matching ambient authority; the language itself should not be crippled into an application-specific subset.

Lane B also accepts Lane C's two refinements:

> `per-call capability validity != cumulative admissibility`

and

> `current producer identity != origin authority`.

These are now not only cross-read conceptually; Lane B tested their preservation across C-FFI and JSON-process representations.

## Lane-B result — Context-Bound Effect Lowering

The shared UECC design needs an executable lowering contract. Lane B proposes that an authority-bearing release decision remain bound to at least the currently tested dimensions:

- exact `EffectIntent` identity;
- current basis/source state;
- current selection identity;
- closure validity;
- revocation epoch;
- expiry/freshness;
- capability scope;
- permit authenticity / opaque host root;
- origin/integrity ancestry;
- monotone aggregate consumption state.

This is not yet claimed to be a universally minimal tuple. It is a falsifiable candidate contract.

The rule is:

> **A lowering may change bytes, ABI, process location, language and backend, but it may not silently erase or widen authority-relevant semantics.**

Compilation success is therefore insufficient. Promotion requires differential/translation validation against declared semantic and effect behavior.

## Executable evidence

### 1. Local differential + mutation test

- mixed cases: **100,000**;
- reference-vs-lowered authorization mismatches: **0**;
- targeted invalid cases: **40,000**, all denied by full checker;
- benign cases: **10,000**, all allowed;
- removing any one of signature/scope/revocation/expiry/basis/selection/closure/intent: **5,000 / 5,000** targeted false accepts for that removed dimension.

### 2. E2B isolated Linux replication

`EXP-CC-RC1.9-CBEL-TV-E2B-001`

- mixed fuzz: **30,000**;
- targeted invalid: **20,000**;
- benign: **10,000**;
- reference-vs-lowered mismatches: **0**;
- mixed false accepts: **0**;
- each single-check mutant: **2,500 / 2,500** targeted false accepts;
- exit `0`, stderr empty.

### 3. E2B cross-representation lowering

`EXP-CC-LANE-B-CROSSBOUNDARY-002`

The same decision semantics crossed:

1. a compiled C shared library via `gcc` + `ctypes` FFI;
2. a JSON subprocess IPC boundary.

Results:

- cases per boundary: **12,000**;
- C-FFI mismatches: **0**;
- JSON-IPC mismatches: **0**;
- each of the eight single-check C mutants: **1,000 / 1,000** targeted false accepts.

The E2B image reported `wasmtime_present=false` and `rustc_present=false`; no real WASI/Rust lowering is claimed.

### 4. Lane-C refinement replication across boundaries

`EXP-CC-LANE-B-ORIGIN-BUDGET-003`

Lane B then added explicit origin and aggregate consumption state across the same C-FFI + JSON-IPC style boundary.

- cases: **8,000**;
- C-FFI mismatches: **0**;
- JSON-IPC mismatches: **0**;
- origin check removed: **2,000 / 2,000** targeted false accepts;
- consumed aggregate state reset at boundary: **2,000 / 2,000** targeted false accepts.

Thus Lane C's `origin ancestry` and `aggregate monotone budget` are not merely policy prose in the current mechanism: losing either at a representation boundary changes authorization behavior.

## Multiworker fusion delta

The three lanes now compose into one candidate direction:

1. **Lane A — UECC generality:** arbitrary systems effects remain semantically expressible.
2. **Lane C — authority envelope:** exact intent/scope/origin/epoch plus cumulative monotone state remains externally rooted.
3. **Lane B — translation contract:** those semantics must survive compiler/ABI/process lowering and be checked against an oracle/translation-validation contract.

A concise working formulation is:

`Universal Clay semantics -> typed EffectIntent -> semantics-preserving lowering -> host-rooted attenuated AuthorityEnvelope -> current-state revalidation -> effect -> receipt/outcome`

not:

`model text -> syscall`.

## Cross-branch consequences

- **FRANK C9:** `S.EFFECT_PERMIT_REF_C9` / commit context should include origin ancestry and aggregate monotone consumption, and compiler/lowering receipts should preserve current basis + selection + closure + revocation/freshness.
- **Clay:** Safe-Effect geometry should constrain reachable authority, not universal language vocabulary. Constructive-only remains insufficient.
- **ClayGraph:** retrieved/activated memory may influence intent but cannot upcast origin/integrity or mint authority; origin labels needed by effect release must survive projection/lowering.
- **UnifiedDB:** selection identity and source/basis epochs are causal inputs to consequential releases; physical query/placement lowering must not erase them.
- **GWT:** workspace selection/winner identity remains separate from authority; a selected proposal still needs a current host envelope.
- **Hyperposition H6:** `TopologyIntent` and host-only `TopologyPermit` fit the same lowering law; live topology switching must preserve credit/basis/selection/authority identity.
- **Emergenz:** stronger receipts improve causal attribution but are not emergence/consciousness evidence.

## Negative results / limits

1. A source-level `DELETE/FORMAT` ban is rejected as the general safety mechanism.
2. A program can compile and still be authority-incorrect.
3. Finite zero-mismatch fuzzing is not formal proof.
4. No real WASI capability resource/handle test ran in this lane.
5. Rust/C++ FFI, dynamic linking, JIT, GPU/device, freestanding and Android/JNI remain open.
6. No target-Qwen ClayCode adherence test ran.
7. No production FRANK effect broker or real consequential external target was exercised.
8. All three worker lanes share RAE ancestry; convergence is not independent replication.

## Highest-information next test

Build the same frozen UECC authority envelope as a real WebAssembly Component/WASI resource capability and lower identical intents through at least native + WASI + C/Rust FFI. Seed mutations that drop/widen origin, aggregate state, scope, selection, basis, closure, revocation or expiry, then translation-validate effect decisions and actual filesystem/network/process containment.

## Lane status

**LANE B COMPLETE FOR MULTIWORKER FUSION / OPEN-HOLD / NO CANONICAL PROMOTION.**

The result is ready for the shared three-worker fusion. The exact minimal authority tuple, target-reader usability and production enforcement backend remain open hypotheses.
