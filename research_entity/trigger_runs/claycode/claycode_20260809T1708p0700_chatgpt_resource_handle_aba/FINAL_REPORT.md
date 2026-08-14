# ClayCode Trigger Run — Runtime Resource Handle Lifetime / ABA

Run: `claycode_20260809T1708p0700_chatgpt_resource_handle_aba`  
Trigger: `claycode`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` / IN_PROGRESS  
Primary work packages: `CC-WP-07-RUNTIME-ABI-FFI`, `CC-WP-11-FUZZ-CONFORMANCE`  
Promotion: **NONE**

## Executive result

This run deliberately avoided the concurrent ClayCode numeric-canonicalization, parser-surface and source-chain workers and tested an orthogonal BASE boundary: **runtime resource-handle lifetime identity across FFI/host-resource reuse**.

A deterministic host-runtime model compared two handle schemes under close/drop followed by deliberate slot reuse:

1. **raw reusable integer slot handle**;
2. **slot + generation/lifetime handle**.

Observed:

- compact exhaustive family: raw handle **16/16 unsafe stale uses**, generation-checked **0/16**;
- deterministic fuzz: raw handle **100,000/100,000 unsafe stale uses**, generation-checked **0/100,000**;
- representative transition: old `(slot=0,generation=1)` closed, new resource allocated at `(slot=0,generation=2)`; raw stale handle resolved to the new resource, generation-checked stale handle failed closed.

This is evidence only for the explicit constructed allocator/runtime model. It does **not** establish that current ClayCode or Frank contains this bug, does **not** prove the generation-tag mechanism is uniquely correct, and does **not** count as end-to-end ClayCode compilation evidence.

The narrow architecture conclusion is:

> ClayCode's Runtime ABI/FFI should expose **opaque, lifetime-checked live resource identity**. A dropped/released resource reference must not become valid again merely because a backend slot/index is reused. This can initially be a runtime/type-effect/broker contract; no new core syntax is justified by this result.

This refines, rather than changes, the current BASE direction: **less change, more compile**.

## Current-stage grounding

The current program stage is `BASE_CLAYCODE_RELEASE`. The release workspace still lists all 14 BASE work packages as OPEN and no mandatory application exemplar as PASS. Therefore this run does not advance a gate.

The active compiler acceptance law remains:

`preserve semantics -> freeze -> compile/lower -> execute -> test -> only change language when a real application/compiler counterexample forces it`

The current v0.1 execution/release target remains the Ubuntu Linux developer system; Android/mobile/edge and other portability targets remain outside Frank v0.1.

## Fusion 1 — current mesh constraints

### ClayCode

Recent current work already establishes several relevant separations:

- parser/lexer identity precedes deterministic typed-IR semantic identity;
- source→parser→AST→typed IR→semantic hash→lowering→artifact→execution ancestry must remain joined for compiler-gate evidence;
- program semantic identity is not execution/replay identity;
- capability/effect authority is external to model output.

The current run adds a narrower resource dimension: even a correct semantic program and valid capability reference do not identify one live host-resource lifetime.

### Clayresearch

The newest loop/effect foundry separates program semantic identity, decision snapshot identity, capability-grant identity and physical resource identity. It also proposes effect commit freshness. This run does not count that shared ancestry as independent replication. It turns one physical-resource failure mode into executable negative evidence.

### FRANK

Frank is a separate research target. FRANK's file/process/socket/database/HTTP/GPU and other host resources eventually cross the same runtime/FFI boundary. A recurrent or delayed action must not retain a stale host handle merely because its semantic intent remains unchanged.

This finding does not grant Frank authority to modify its own Harness.

### Harness

Current trace/replay work already requires explicit causal and execution receipts. The new resource-lifetime test family is suitable for APP-08 and later H1→H2 differential replay: close/drop, forced reuse, stale use, move/borrow/duplicate, async work, restart and recovery.

### ClayGraph

A ClayGraph node or relation can represent resource provenance/topology. Its graph identity, activation or salience cannot be used as a live host-resource handle or authority token. Derived graph state remains non-authoritative.

### UnifiedDB

UnifiedDB can persist resource descriptors, provenance and recovery intent. Persisted state must not silently resurrect a process-local live handle after restart. Reacquisition/reopen should produce a fresh runtime resource-instance/lifetime identity.

### GWT

Workspace selection, delivery, causal use, outcome or re-entry cannot extend a dropped resource lifetime. Globally active representation is not execution authority.

### Hyperposition

Alternative branches may retain alternative resource intents or references, but eventual execution must validate the selected branch against the current live resource instance. Coexisting alternatives cannot justify stale alias reuse.

### Emergenz

No emergence claim changes. Resource-lifetime correctness is an experimental/runtime validity condition, not evidence of causal or phenomenal emergence.

## Hypothesis generation 1

Primary hypothesis:

`H-CC-RESOURCE-LIFETIME-021`

A live FFI/runtime resource reference needs lifetime identity beyond a reusable backend slot/index. After close/drop and reuse, the stale reference should fail closed.

Counterhypothesis:

A raw reusable integer index is sufficient because another mandatory runtime layer always prevents stale reuse.

Highest-information discriminator:

Construct a minimal resource table with forced reuse and compare stale-use behavior under raw indices versus lifetime-checked opaque handles.

## Executable experiment

Experiment: `EXP-CC-RESOURCE-HANDLE-ABA-20260809-01`  
Artifact: `experiments/resource_handle_aba_probe.py`  
Receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`  
Seed: `20260809`  
Runtime: ChatGPT local Linux container / Python 3.13.5  
Source SHA-256: `689eb6b5ec2cbee8b3fd1d906852de78823b5e065a8793f5650d87e4206f3ce3`

### Model

The experiment uses two deterministic tables with identical allocation policy.

#### Arm A — raw reusable integer handle

`open(resource) -> slot:int`

`close(slot)` frees the slot. A later `open(new_resource)` may reuse it. `use(old_slot)` simply looks up the current slot.

#### Arm B — generation/lifetime-checked handle

`open(resource) -> {slot,generation}`

Each allocation of a reused slot increments generation. `use(handle)` succeeds only if both slot and generation match the current resource instance.

### Ground-truth property

After a resource has been closed/dropped, an old handle must not resolve to a different newly allocated resource merely because the storage slot/index was reused.

### Exhaustive compact family

Resource label: B or C.  
Post-reallocation churn: 0..7.  
Total: **16 cases**.

Observed:

- raw reusable integer handle: **16 unsafe stale resolutions**;
- generation/lifetime checked: **0 unsafe stale resolutions**.

### Deterministic fuzz

Cases: **100,000**.  
Randomized labels and surrounding allocator churn; free-list policy deliberately exercises slot reuse.

Observed:

- raw reusable integer handle: **100,000 unsafe stale resolutions**;
- generation/lifetime checked: **0 unsafe stale resolutions**.

### Interpretation boundary

The experiment is deliberately adversarial: it forces the exact slot-reuse condition under examination. Therefore it demonstrates a mechanism failure of raw reusable-slot identity **inside this allocator model**. It does not estimate the natural frequency of such reuse in a production backend.

The result also does not prove generation tags are uniquely required. Equivalent safe candidates may include backend-native opaque handles, non-reusing identities or a broker-maintained lifetime token.

## External triangulation / Fusion 2

Primary/official specifications provide independent mechanism analogues.

### POSIX file descriptors

The Open Group `close()` specification states that closing a file descriptor deallocates it and makes the descriptor available for future allocation. This provides a concrete host-level example where a small integer identifier can later refer to a different live resource if higher-level code retains it incorrectly.

This does not mean every ClayCode resource must be a POSIX file descriptor; it establishes that backend identifier reuse is a real systems mechanism rather than a purely artificial naming concern.

### WebAssembly Component Model resources

The WebAssembly Component Model/WIT resource model uses abstract resource types passed indirectly through handles. `own` and `borrow` distinguish ownership/lifetime relationships, and runtime-managed handle tables mediate those resources rather than exposing arbitrary physical pointers as ordinary values.

This independently supports the design class **opaque typed resource handle + explicit lifetime discipline**. It does not select ClayCode syntax and does not prove the generation-tag implementation.

## Goodman anti-echo review

Prior Clay/FRANK/ClayCode work already proposed separating physical resource identity from semantic and capability identities. This run does not count that project agreement as replication.

Independent support used here:

1. direct local executable stale-reuse discriminator;
2. POSIX descriptor deallocation/reuse semantics;
3. Component Model typed runtime resource handles and ownership/borrowing semantics.

Verdict: **REFINED**.

Refinement:

- preserve the identity split;
- make stale-use fail-closed a Runtime ABI/FFI conformance property;
- keep implementation mechanism open;
- do not add a core language primitive unless a real application/FRANK counterexample shows existing typed resources cannot lower safely.

## Negative results

### `N-CC-RAW-REUSABLE-HANDLE-ABA-20260809`

Raw reusable integer slot identity fails the constructed stale-use invariant: 16/16 exhaustive and 100,000/100,000 fuzz cases resolved a stale reference after reuse.

Scope: constructed forced-reuse allocator only; no production ClayCode/FRANK bug claim.

### `N-CC-GENERATION-TAG-UNIQUE-SOLUTION-NOT-ESTABLISHED-20260809`

Generation tags eliminated the tested failure but are not established as uniquely optimal or necessary. Backend-native opaque handles, non-reusing IDs or other lifetime-token schemes remain live alternatives.

## Architecture delta

Minimal candidate Runtime ABI invariant:

```text
resource_use(handle, operation) requires:
    handle_type_matches
    && resource_instance_is_alive
    && handle_lifetime_is_current
    && capability_is_current_for(operation)
    && broker/resource_scope_is_current
```

Important non-collapses:

```text
program_semantic_identity
!= decision_snapshot_identity
!= capability_grant_identity
!= physical_resource_instance_identity
!= handle_lifetime_identity
```

A backend slot/index may be part of an implementation locator, but it is not by itself sufficient live resource identity under reuse.

This candidate belongs first in:

- Runtime ABI;
- typed FFI/resource adapter;
- type/effect checker obligations where ownership/lifetime facts are statically knowable;
- runtime broker checks where they are dynamic;
- execution/recovery receipts.

It should become new ClayCode syntax only if an executable real-program counterexample proves the existing semantic forms cannot express/lower the invariant.

## Cross-branch feedback

Written to `BRANCH_FEEDBACK_MANIFEST.json` for all nine registered scientific branches.

Most material feedback:

- **ClayCode:** add stale-handle lifetime conformance to WP-07/WP-11; no core syntax change.
- **Harness:** add drop/reuse/stale-use and async/recovery cases to APP-08 and H1/H2 differential replay.
- **FRANK:** reacquire fresh live resource identity after close/restart; stale recurrent intent cannot extend resource authority.
- **UnifiedDB:** persist descriptors/provenance, not resurrected live process handles.
- **ClayGraph:** graph resource identity/activation cannot substitute for live runtime handle authority.
- **Clayresearch:** Safe-Effect Geometry gains a concrete FFI/resource-lifetime failure family.
- **GWT/Hyperposition/Emergenz:** no authority or emergence promotion follows.

## Highest-information next execution

Do not redesign ClayCode again from this result.

1. Implement a production-bound opaque resource table/adapter behind the current typed resource/FFI concepts.
2. Compare at least two mechanisms: generation/lifetime-checked table versus backend-native opaque handles where available.
3. Exercise files, processes, sockets/HTTP, DB handles and one FRANK-relevant resource class.
4. Test open/use/drop/reopen/reuse, double-drop, forged handle, moved ownership, borrow lifetime, duplicate/clone policy, async outstanding operations and callback re-entry.
5. Add crash/restart recovery: persisted descriptors may be restored, but process-local live handle identity must not be resurrected.
6. Measure stale-use accepts, false rejects, capability forgery accepts, alias errors, latency and memory overhead.
7. Run on the actual Ubuntu developer target before promotion.
8. Once the production frontend exists, bind the entire evidence chain:

`source_hash -> parser identity -> AST_hash -> typed_IR_hash -> semantic_hash -> lowering identity -> artifact_hash -> resource-ABI receipt -> execution receipt`

9. If existing ClayCode typed resources cannot represent this without an escape hatch, preserve the minimized executable counterexample and only then reopen language semantics.

## Completion boundary

Completed in this run:

- verified canonical join and current stage;
- current trigger/protocol routing;
- manual fail-closed nine-branch interconnect assembly with ClayGraph/UnifiedDB deep inputs;
- concurrent-worker de-duplication;
- falsifiable hypothesis/counterhypothesis generation;
- executable 16-case exhaustive + 100,000-case fuzz discriminator;
- independent primary-source mechanism triangulation;
- Goodman anti-echo review;
- hypotheses and negative results;
- Tool Execution Manifest;
- branch feedback manifest;
- executable research receipt;
- durable GitHub report.

Not completed and not falsely claimed:

- repository-local `research_interconnect_preflight.py` execution;
- repository-local `goodman_filter_check.py` execution;
- E2B execution;
- production ClayCode parser/compiler execution;
- Andreas Ubuntu target execution;
- APP-01..10 PASS;
- any CC work-package PASS;
- BASE/GENERAL_PURPOSE gate PASS;
- canonical revision promotion.

The result is a scoped BASE Runtime ABI/FFI research delta, not a release claim.
