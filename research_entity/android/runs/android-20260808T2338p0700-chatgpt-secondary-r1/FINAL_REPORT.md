# ANDROID SECONDARY RESEARCH ARM — R1 FINAL REPORT

**run_id:** `android-20260808T2338p0700-chatgpt-secondary-r1`  
**actor:** `chatgpt-secondary`  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c`  
**role:** permanent secondary cross-cutting Android research arm  
**reference platform:** Linux  
**decision:** COMPLETE R1 / NO CANONICAL SCIENTIFIC PROMOTION

## 1. Architecture decision

Android is now a permanent research arm of FRANK/RAE, but it is deliberately **not** a ninth peer scientific branch and not the reference deployment target.

The fixed relationship is:

> **FRANK stays Linux-primary. Android is a secondary adversarial efficiency, portability and edge-runtime projection of the same Clay-native semantics.**

Android must retrieve current material from all eight authoritative branches (`clay`, `frank`, `gwt`, `emergenz`, `claycode`, `hyperposition`, `claygraph`, `unifieddb`) before a full run. Every completed Android run must emit a material delta or explicit no-change receipt back to every branch.

Android-local observations retain Android provenance. A mechanism that looks general becomes an OPEN `GENERALIZABLE_CANDIDATE`, not an automatic Linux/FRANK fact. Strong cross-platform claims require matched Linux replication.

## 2. Live remote Android path is proven

The complete cloud-only execution path was exercised without the user's local machine:

`GitHub Actions -> Firebase service-account authentication -> Android/Gradle build -> Firebase Test Lab -> virtual ARM Android -> instrumentation result`.

The authenticated service account successfully queried Test Lab device models and Android versions. The workflow also demonstrated that the required Google APIs can be enabled from the remote service-account lane under the current project permissions.

### Implementation negatives retained

Two failures occurred before scientific device allocation:

1. AndroidX instrumentation dependencies were present without `android.useAndroidX=true`. The build failed and was repaired.
2. `toolresults.googleapis.com` was disabled. Test submission was blocked before a device run and the workflow then enabled the required APIs.

These are kept as negative pipeline evidence rather than erased from history.

## 3. Device experiment results

### EXP-ANDROID-R1-INFRA-001

Firebase matrix: `matrix-3mqon98nc2zsk`  
Device: `MediumPhone.arm` · Android 35 · virtual ARM

Result: **2/2 PASS**

- typed arithmetic/assertion produced `42`;
- unknown reference was rejected deterministically.

This established the first real Android execution receipt for the constructed ClayCode-like semantic harness.

### EXP-ANDROID-R1-PORTABILITY-BUNDLE-002

Firebase matrix: `matrix-322nxfmnphtz2`

Devices:
- `MediumPhone.arm` · Android 35;
- `SmallPhone.arm` · Android 30.

Result: **9/9 PASS on each device = 18/18**.

The nine bundled controls were:

1. typed arithmetic/assertion preserves value `42`;
2. 1000 repeated evaluations are deterministic;
3. unknown references are rejected;
4. integer overflow is rejected;
5. ORDERED / SET / MULTISET controls remain semantically distinguishable;
6. repeated canonical replay produces equal state while a damaged missing-tail replay differs;
7. a model-like proposal cannot self-mint effect authority when the external capability is false;
8. the constructed compact Clay-like source uses fewer bytes than the verbose JSON-like control;
9. the selected Android runtime generation is explicitly recorded/checked.

Across both live matrices R1 therefore recorded **20/20 successful instrumentation test executions**.

## 4. Scientific interpretation

The strongest justified R1 conclusion is not “FRANK runs on Android”. It is:

> **Android is now a functioning real-device-class experimental substrate for deterministic Clay/ClayCode/FRANK invariants and constrained-runtime research.**

The selected constructed invariants were stable on two virtual ARM Android generations. This makes cross-version Android differential testing practical and shows that many independent checks can be bundled into one matrix without spending one device invocation per hypothesis.

The current harness is intentionally small and written as a constructed Java implementation. Therefore R1 does **not** establish:

- full Clay semantics;
- full ClayCode compiler conformance;
- complete FRANK Android feasibility;
- Qwen 4B model feasibility or quality;
- real UnifiedDB persistence behavior;
- ClayGraph activation/traversal performance;
- GWT mechanisms;
- physical-device thermal, battery, RAM or accelerator behavior;
- Linux equivalence.

## 5. Efficiency research consequence

Android is useful beyond Android itself because tight constraints can expose expensive architectural choices earlier.

The main generalizable research questions are now:

- Which Clay representations minimize bytes/tokens **without increasing parse/model reconstruction cost**?
- Which state should remain resident versus be rebuilt from canonical state?
- Which module boundaries copy or serialize too much?
- How much memory and latency are consumed by ClayGraph Assemblies, GWT WorkspaceEpisodes and UnifiedDB sidecars?
- How much do bounded Clay views reduce context/KV/prefill cost for the target Qwen-class 4B?
- Which Android-derived optimizations also improve Linux under matched semantics?

R1's compact-source byte check is only a sanity result. It must not be upgraded into token, latency or reasoning-efficiency evidence until those quantities are measured directly.

## 6. Bidirectional research mesh — implemented and tested

A first retrieval validation exposed an important architecture defect: writing a cross-branch packet did **not** guarantee that a high-volume branch would include it in its bounded active context. A second test showed that even branch-specific Android packets could be displaced in `clay`, `frank`, `gwt` and `claycode` by ordinary relevance/category selection.

That negative result produced a general fix:

`research_entity/global/MANDATORY_ACTIVE_KNOWLEDGE.json`

and generic support in `tools/research_interconnect_preflight.py`.

Mandatory pins:
- guarantee retrieval presence only;
- consume the normal bounded packet budget;
- preserve the packet's original evidence/provenance status;
- do **not** promote a claim.

Validation workflow run `31267946992`, job `93129040517`, then returned:

`ANDROID_MESH_RETRIEVAL_PASS`

for all eight branches. This turns the user's emit/retrieve requirement into a tested mechanism rather than a documentation promise.

Eight branch-specific Android R1 packets are pinned and active. They contain the R1 evidence boundary plus the next branch-specific falsifiers.

## 7. Quota discipline

R1 intentionally consumed:

- virtual Test Lab device invocations: **3**;
- physical Test Lab device invocations: **0**.

Using the nominal 10 virtual/day planning budget, R1 stopped with approximately **7 virtual invocations left for other workers**. No further device test is justified in this cycle because the next useful step needs target-model/runtime integration first and can initially be done in CI without device quota.

## 8. Next Android research programme

Highest-information next experiment:

### EXP-ANDROID-R2-QWEN-RUNTIME-003

First package a quantized Qwen-class 4B-capable Android runtime entirely in CI. Do not spend a Test Lab invocation until native/model packaging succeeds.

Then use one virtual ARM device to establish:
- exact model/runtime/quantization identity;
- successful model load;
- one deterministic inference path;
- observable memory/runtime receipts where available.

After that, bundle:

### EXP-ANDROID-R2-CONTEXT-KV-004

Test bounded Clay/MOSAIC views versus larger controls while separating:
- context/input size;
- prefill/first-token latency;
- decode throughput;
- total task latency;
- memory pressure;
- task correctness.

This directly addresses G12 hypotheses H-G12-057 and H-G12-059.

Further queued experiments:
- reader-rail cost/equivalence;
- GWT stage costs with candidate/projection/re-entry orthogonalized;
- ClayGraph sparse activation vs conditional traversal;
- UnifiedDB embedded persistence + process-death replay;
- physical-device sustained thermal test only when model runtime is ready;
- matched Linux-vs-Android differential to promote general efficiency findings.

## 9. Branch feedback

All eight authoritative branches now receive Android R1 via explicit active packets. The routing rule is:

- Android-specific constraints stay Android-local unless they affect another branch;
- generalizable mechanisms are emitted as OPEN candidates;
- main branches perform their normal falsification/promotion work;
- Linux replication is required for general FRANK/Linux claims;
- one Android experiment reused by eight branches remains one shared evidence ancestry.

## 10. Final decision

**Android secondary arm: ESTABLISHED.**  
**Cloud Android experiment lane: VERIFIED LIVE.**  
**R1 selected Android invariant bundle: PASS.**  
**Bidirectional eight-branch emit/retrieve: VERIFIED.**  
**Device campaign: STOPPED AT QUOTA BOUNDARY.**  
**Canonical scientific promotion: NONE.**

The most valuable consequence is broader than mobile deployment: Android is now a real constrained substrate that can continuously challenge FRANK's efficiency assumptions and feed the resulting mechanisms back into the entire research mesh while Linux remains the reference platform.
