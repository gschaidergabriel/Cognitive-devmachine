# EntityOS HCU compatibility subtree

Status: **CURRENT ENTITYOS/HCU INTEGRATION SURFACE — COMPATIBILITY PATH**

This directory is retained at `the artefact/MicroEntity/hcu/` for exact historical path, receipt, package and donor provenance. The path name **MicroEntity is not a current product identity**.

Current authority:

- **EntityOS** is the sole current product/system identity.
- **HCU** is the sole current integrated cognition/compute architecture.
- Clay is the persistent research entity; temporary workers and HCU logical cells are organs/functions, not new entities.
- UnifiedDB, or the current compatibility MiniUnifiedDB substrate while exact migration remains incomplete, is the canonical durable state/evidence authority.
- EffectGate + EffectJournal are the only admitted real/state-changing effect authority.
- HCU, J-Space, world-model, workspace and model outputs are candidate/projection/measurement only and cannot mint canonical truth.

The current integration contract is `ENTITYOS_HCU_INTEGRATION_CONTRACT.json`. It supersedes historical Mini Entity product/workstream wording in older receipts and Git history without rewriting those historical identities.

## Current HCU path

```text
new data/event/prompt
-> Typed Entry Fabric
-> immutable causal event identity + concrete admission identity
-> canonical state/evidence
-> deterministic control plane
-> independently admitted EngineAdmission / capacity / capability bindings
-> HCU GRID10 / COGSIM10 / WM_TEST / NESTED_SIM / SCALEOUT computation
-> typed causal packet / Hyperposition / workspace
-> candidate decision or typed effect request
-> EffectGate + EffectJournal
```

Required invariants:

- replay-stable `event_sha256` is distinct from concrete admission identity;
- Entry capability or resource claims may narrow independently admitted authority but may never self-grant or broaden it;
- engine/provider/class/artifact authority comes from deterministic control-plane admission, never from an untrusted causal event;
- downstream inference receipts must echo the admitted event/admission/route/engine/artifact identities required by the current contract;
- one versioned canonical identity path must be selected before heterogeneous/cross-language hash identity is promoted;
- no second router, Entry authority, canonicalizer authority, state authority, identity service, recovery ledger or effect path is created to bypass a blocker.

## Retained donor lane

Draft PR #1263 is the retained HCU donor/integration lane for the richer Typed Entry + EngineAdmission + router + inference-receipt + GRID10 mechanisms. It is donor evidence, not a second product head, and must be rebased/fused into current EntityOS/HCU authority rather than duplicated.

## Files

- `ENTITYOS_HCU_INTEGRATION_CONTRACT.json` — current authority/integration fence for this compatibility subtree.
- `HCU_ARCHITECTURE.md` — current EntityOS/HCU architecture contract.
- `topology.kvm4.json` — historical/planning capacity profile only; numeric values are not runtime facts.
- `FREE_LLM_FEED_CONTRACT.json` — bounded FREE_ONLY candidate-feed contract where still compatible with current authority.
- `HCU_DATA_INDEX.json` — current compatibility-subtree data/package index.
- `capacity_guard_v1.py` — fail-closed capacity-admission donor primitive.
- `test_capacity_guard_v1.py` — deterministic capacity poison regressions.
- `receipts/` — bounded non-secret evidence receipts.

## Execution and evidence law

Current build/test/experiment/runtime credit comes only from `AUTHORIZED_ISOLATED_SANDBOX_ONLY`. VPS, self-hosted and production-host testing are forbidden under current control. A KVM/VPS profile is a deployment/planning target only until separately authorized; it cannot provide current acceptance credit.

Together API and paid fallback are forbidden. Final paid/model training requires explicit owner authorization. Source/component/historical PASS does not imply EntityOS/HCU runtime acceptance.

Current runtime credit remains zero until the exact current EntityOS/HCU path is actually executed and bound to exact source, model/checkpoint/tokenizer/runtime, capacity, causal/admission and effect identities.
