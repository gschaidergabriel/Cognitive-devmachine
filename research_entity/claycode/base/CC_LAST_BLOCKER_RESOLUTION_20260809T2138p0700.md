# ClayCode — last blocker resolution · 2026-08-09 21:38 +07:00

Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Target: `ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM`  
Authority invariant: `model output != execution authority`

## Result

The remaining ClayCode work has been reduced to receipt-producing execution on the selected Ubuntu target plus one exact-main strict V9 parser receipt. No current executable counterexample justifies additional ClayCode semantic widening. `open_p0=0` and `open_p1=0` in the current compiler manifest.

Current promotion blockers remain exactly:

1. `WP02_STRICT_V9_RECEIPT_NOT_PRESENT`
2. `ANDREAS_TARGET_RECEIPTS_NOT_PRESENT`
3. `FULL_FRANK_TARGET_RECEIPT_NOT_PRESENT`
4. `WP14_AUDIT_NOT_PASS`

These four are intentionally fail-closed. They must not be satisfied by hosted/proxy/sandbox evidence.

## Software/gate defects closed in this run

### 1. WP02 grammar identity could drift between V7 and V9

The canonical Andreas collector had still been capable of producing WP02 strict/frontend evidence from the V7 typed-function grammar while the current formal WP02 contract and production declarative defaults require V9.

Repairs:

- `tools/claycode_base_andreas_target_runner_v2.py`
  - WP02 strict/full-corpus is explicitly V9.
  - strict receipt is now `STRICT_LALR_D_V9_TARGET_RECEIPT.json`.
  - strict and frontend receipts must embed the exact repository V9 SHA-256.
  - WP03 typed-function evidence remains a separately versioned executable slice rather than being mislabeled as WP02 evidence.
- `tools/claycode_andreas_ubuntu_acceptance_assembler.py`
  - independently recomputes the V9 SHA-256;
  - requires collector, strict receipt, frontend receipt and production canonicalizer to agree on V9 identity before WP02 can pass.
- `tools/claycode_andreas_ubuntu_target_gate.py`
  - legacy/manual diagnostic path now follows the same V9 WP02 split and cannot emit misleading V7-as-WP02 evidence.
- `research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json`
  - V9 grammar identity is now a hard contractual requirement, not just an implementation convention.

This closes the path where a physically real Ubuntu run could still satisfy the wrong parser contract.

### 2. Physical autoprobe did not retrigger on gate dependencies

`.github/workflows/claycode-andreas-target-autoprobe.yml` had regressed to triggering on its own YAML only. Gate/compiler/grammar/finalizer changes could therefore land without requeuing the target closure.

Repair commit: `e943d27ab88902fef565198cd3f9532fbeb58ce4`.

The workflow now reacts to the runner/bootstrap, host identity, target collector, V9 parser/canonicalizer/IR/compiler, desktop gate, real app suite, Full-FRANK finalizer, strict acceptance assembler, receipt contract, WP14 audit and promotion dependencies.

### 3. Hosted strict evidence was version-mislabeled

The BASE frontend CI previously used V6 naming while the invoked validators had moved to V9 defaults. That could have archived green V9 behavior under a V6 receipt identity.

Repair:

- exact V9 grammar is passed explicitly to frontend/canonicalizer/IR;
- environment records path + SHA-256;
- machine-readable receipts are checked against the exact V9 SHA;
- receipt names now say V9;
- pull-request observability was added for independent probing.

### 4. Hosted Actions failure was separated from language evidence

The observable strict-V9 probe run `31318205382` failed before any executable step. The initial job `93256814556` had zero steps/artifacts and no log blob. An explicit GitHub Actions job rerun was accepted and created job `93258442470`; it reproduced the same pre-step failure with zero steps and a missing log blob.

Therefore this is replicated hosted Actions transport/startup negative evidence, not a V9 parser/canonicalizer/typed-IR/ClayCode semantic failure.

Preserved events:

- `research_entity/rooms/rooms/center/events/20260809T212450p0700_claycode_hosted_strict_v9_transport_negative.json`
- `research_entity/rooms/rooms/center/events/20260809T213600p0700_claycode_hosted_strict_v9_second_prestep_failure.json`

### 5. V7 executable surface vs V9 parser repair now has a concrete unification candidate

`research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V10_OPERATOR_FN_DOTTED.lark` combines V7 typed `fn`/exact operator support with V9's contextual dotted-prefix repair.

Sandbox discriminator receipt:

`research_entity/claycode/base/receipts/CC_WP02_V10_UNIFIED_FRONTEND_SANDBOX_20260809T2110p0700.json`

Observed contextual LALR regressions: `8/8` pass. V10 remains non-promoted; it cannot replace V9 from sandbox evidence alone.

### 6. `frank_runtime.clay` root surface is no longer a false release blocker

`frank_reference/claycode/frank_runtime.clay` is currently a provenance-bound semantic root contract, not a selected APP10/WP13 production executable. Generic structured ClayCode already covers the execution constructs needed by the selected Full-FRANK programs. The remaining root-contract sugar is tracked as coverage research.

Current rule: if that root file or a byte-identical descendant becomes a selected production executable, the surface gap automatically reactivates as a gate-relevant counterexample. Until then it must not widen BASE merely to make a non-selected contract source parse.

Reference: `research_entity/claycode/base/FRANK_ROOT_SURFACE_CLASSIFICATION_V1.json`.

## Remaining evidence boundary

At the end of this run the following physical receipts are still absent from `main`:

- `research_entity/claycode/target/ANDREAS_SELF_HOSTED_AUTOPROBE.json`
- `research_entity/claycode/target_receipts/ANDREAS_BASE14_CLOSURE_RUN.json`
- `research_entity/claycode/target_receipts/ANDREAS_UBUNTU_FULL_FRANK_H2_HANDOFF.json`

They cannot be manufactured from a hosted runner, proxy suite, ChatGPT sandbox or model assertion. The physical closure remains wired through:

```bash
python3 tools/claycode_run_andreas_target_acceptance.py
```

The target chain must still prove exact V9 WP02 identity, real 10-application execution, real mapped Ubuntu desktop behavior, Full-FRANK production handoff, zero semantic escape hatches and WP14 strict audit before promotion.

## Current conclusion

Software-side blocker search found and repaired multiple real gate/orchestration defects. The remaining release blockers are now evidence-production blockers on the real selected host, not unresolved language-design blockers. Do not mark ClayCode BASE PASS until the required physical receipts exist and the strict auditor promotes all fourteen work packages.
