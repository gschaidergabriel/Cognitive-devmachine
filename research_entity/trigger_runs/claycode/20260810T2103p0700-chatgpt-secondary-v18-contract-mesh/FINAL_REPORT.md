# ClayCode — V18 contract binding + Frank-v0.1 mesh repair

Run: `20260810T2103p0700-chatgpt-secondary-v18-contract-mesh`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Program: `FRANK_V0_1`  
Promotion: **NONE**

## 1. Current-program correction

The current owner-fixed program is a single Frank v0.1 product. ClayCode is one compiler/runtime component of that target; legacy BASE/H1/H2/H3 stage semantics are historical evidence only. This run therefore did not optimize a separate ClayCode release milestone. It selected executable compiler integrity work that directly constrains current Frank v0.1.

## 2. Duplicate-work avoidance

The run initially investigated the WP03 FrontendArtifact -> TypedIR frontier, then discovered fresh sibling commits had already implemented the V18 bridge and validation. That candidate was abandoned rather than duplicated.

Cross-read of the current bridge exposed a narrower unclosed defect:

- `frontend_schema` checked;
- `surface` checked;
- V18 grammar hash checked;
- canonical AST `semantic_hash` recomputed and checked;
- `source_sha256` structurally checked;
- but `contract_hash` was merely copied from the artifact into the downstream validation record.

## 3. Executable bug and repair

### Before

Using an otherwise valid V18 frontend artifact, replacing only `contract_hash` with an arbitrary 64-hex value was accepted by the bridge.

This is a receipt-integrity defect. The frontend itself defines `contract_hash` as the hash of the frontend schema identity, exact grammar hash and semantic hash. A consumer that accepts an arbitrary value can no longer claim exact receipt binding across the WP02 -> WP03 boundary.

### After

`tools/claycode_base_typed_ir_v18_bridge.py` now independently recomputes the frontend contract hash from:

- `frontend_schema`;
- exact V18 `grammar_sha256`;
- recomputed `semantic_hash`.

Missing or mismatched values fail closed with `frontend contract_hash mismatch/tamper`.

Implementation commit:

`f90c1b0382ffc7f4845d461c9c4a27bbbf43d7d6`

Regression test:

`tools/test_claycode_v18_bridge_contract_hash.py`  
commit `3642f9a0f913255cf78664351a8c783a1fb7c129`

Local deterministic post-fix discriminator:

- current valid artifact: accepted;
- contract-hash replacement: rejected;
- missing contract hash: rejected;
- semantic-hash mutation: still rejected.

Exact selected grammar identity remained:

`99a3b35acfe491081773b9666d9131dae8b2dd3b3bde7ac8569f6428a5fdb180`

No ClayCode surface or semantic-language change was required.

## 4. Second executable blocker: registry-v3 mesh drift

During the mandatory interconnect step a separate infrastructure contradiction appeared.

Current `RESEARCH_TRIGGER_REGISTRY.json` is schema 3.0 and uses Frank-v0.1-specific operational kinds such as:

- `domain_build_research`;
- `whole_target_architecture_build`;
- `multimodal_perception_research`;
- `integrated_frank_v0_1_research_foundry`;
- `direct_frank_v0_1_validation_repair`.

The legacy interconnect tool still admitted only `domain_research` and `integrated_research_foundry`. Its own exact-set fail-closed invariant therefore became unsatisfiable under the current registry: the dynamically inferred peer set and the explicit ten-peer priority sets could not match.

Repair:

- `tools/research_interconnect_preflight_v2.py` — schema-v3 operational kind classification and preserved ten-peer priorities;
- `tools/research_interconnect_preflight.py` — compatibility entrypoint so existing protocol/CI callers retain the historical command path;
- `tools/test_research_interconnect_preflight_frank_v01_registry.py` — exact-current-peer and meta-trigger exclusion regression.

Commits:

- `b551cab75d2e4653aa10e7d8abb03f45c1cd40a0`
- `58703c0070290de2ecc6118bc8a4b9303e2b73c8`
- `05da53f89948fb488e83edf134aa1564bb0308b2`

The repaired current peer set is exactly:

`clayresearch, frank, q23, gwt, emergenz, claycode, hyperposition, claygraph, unifieddb, harness`

Meta triggers such as `go`, `atomic`, `fusion`, `hypofusion`, `666`, `q12`, `dump` and `spawn` remain orchestration/research modes rather than persistent peer branches.

## 5. Whole-mesh fusion

Relevant current branch constraints were cross-read before finalizing the repair.

- **Frank/effect authority:** current target-VPS effect policy has partial PASS evidence, but exact-current-source frontend/TypedIR, lifecycle/replay, real-provider reconciliation and verified outcome -> provenance re-entry remain open. The contract-hash fix directly tightens this receipt path but does not close it.
- **UnifiedDB:** current work emphasizes temporal identity/state lineage and is now also exploring EUDI as a provisional physical-layout hypothesis. Neither semantic persistence nor physical co-location permits unchecked compiler receipt fields to become trusted state.
- **ClayGraph:** current lineage-topology evidence explicitly rejects collapsing equal digests into one SELF. Contract hashes identify exact compiler/frontend contracts, not entity identity.
- **GWT:** recent negative evidence favors simpler restart/current-evidence behavior over special reboot echoes/twins/quorum machinery. No GWT mechanism change follows from this compiler repair.
- **q23:** current multimodal frontier keeps cache/embedding lifetime and feature-source assumptions explicit and unpromoted. Perceptual/model confidence remains non-authoritative.
- **Hyperposition/Emergenz:** no mechanism promotion follows; this run is compiler/governance infrastructure evidence.
- **Harness:** contract-hash mutation becomes a direct Frank v0.1 regression test; Harness remains a validation method, not a product stage.

## 6. Goodman / counterhypothesis result

Strongest counterhypothesis:

> `contract_hash` is redundant metadata because grammar identity plus recomputed semantic hash already determine the frontend interpretation.

Current result: **not sufficient as an implementation argument**. The frontend deliberately emits a contract identity over schema + grammar + semantics. Once that value is exposed as a receipt field, passing an arbitrary value through a downstream boundary destroys exact receipt equivalence even when underlying semantics happen to remain unchanged.

This is not a claim that the contract hash is an authority token. It is an integrity/provenance binding only.

Second counterhypothesis:

> The old interconnect kind filter remains adequate after the unified Frank-v0.1 registry migration.

Refuted by the current registry taxonomy: it omits multiple operational peer kinds and activates the tool's fail-closed governance-drift error.

## 7. Target-VPS escalation

A dedicated read-only self-hosted regression workflow was added:

`.github/workflows/claycode-frank-v01-regression.yml`

Commit:

`e5d0a483d4122573f6e26f6511102c95cbde50f9`

It binds execution to the exact GitHub SHA and checks:

1. exact V18 grammar hash;
2. current frontend artifact validity;
3. contract-hash tamper rejection;
4. both regression unittest suites;
5. exact ten-peer registry-v3 mesh classification;
6. exact priority permutations.

Its persisted receipt target is:

`research_entity/claycode/base/receipts/CLAYCODE_FRANK_V01_REGRESSION_LATEST.json`

At final-report creation the persisted VPS receipt had not yet appeared, so **no remote PASS is claimed here**.

## 8. Architecture decision

**NO CLAYCODE SEMANTIC CHANGE.**

The two discriminated failures are implementation/governance realization defects. Existing frozen semantics remain adequate for this slice. This supports the project law:

`less change, more compile`

## 9. Frank-v0.1 impact

Directly affected packages:

- `F-V01-02-CLAYCODE-COMPILER-RUNTIME` — integrity improvement, but TypedIR/type-effect remain OPEN;
- `F-V01-09-EFFECT-AUTHORITY` — exact-current-source frontend/TypedIR path de-risked, not closed;
- `F-V01-13-SECURITY-RECOVERY-OBSERVABILITY` — receipt tamper and mesh-governance regressions added.

No package status was promoted from local evidence.

## 10. Next falsifiers

1. Persist the target-VPS regression receipt for the exact tested commit.
2. Feed the exact current target `frank_effects.clay` and ingress authority declarations through V18 frontend -> receipt-bound TypedIR.
3. Implement/execute the production type/effect checker over those declarations, including opaque capability possession, revocation/stale epochs, open-web taint and direct-token scoped intent.
4. Differentially test brokered/opaque capability handling against deliberately ambient and structurally forgeable negative controls.
5. Run exact-current-source crash/replay/reconciliation and verified outcome -> UnifiedDB re-entry -> DONE on the target VPS.

## 11. Durable artifacts

- `INTERCONNECT_MANIFEST.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `EXECUTABLE_RESEARCH_RECEIPT.json`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- this `FINAL_REPORT.md`

Research delta: **COMMITTED**.  
Final Frank v0.1 acceptance: **NOT PASS**.  
Paid/final training: **NOT STARTED / NOT AUTHORIZED**.
