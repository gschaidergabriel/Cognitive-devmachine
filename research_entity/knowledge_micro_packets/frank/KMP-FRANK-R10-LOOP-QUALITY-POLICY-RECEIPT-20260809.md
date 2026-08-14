<!-- RAE_META
{"packet_id":"KMP-FRANK-R10-LOOP-QUALITY-POLICY-RECEIPT-20260809","title":"KMP-FRANK-R10-LOOP-QUALITY-POLICY-RECEIPT-20260809","domains":["frank"],"epistemic_class":"REPOSITORY_CODE_AUDIT_PLUS_LOCAL_COMPONENT_VALIDATION_PLUS_PRIMARY_STANDARD_SUPPORT","claim_status_hint":"CURRENT","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/frank/frank-20260809T1931p0700-chatgpt-secondary-log-state-three-cycle/EXECUTION_RECEIPT.json","gschaidergabriel/Dr.-Unterweger@ef22a56990e8ebdfc3e7cab6292b74daf55d94d2"]}
RAE_META -->

# KMP-FRANK-R10-LOOP-QUALITY-POLICY-RECEIPT-20260809

packet_id: `KMP-FRANK-R10-LOOP-QUALITY-POLICY-RECEIPT-20260809`
domains: `frank, harness, loop_dynamics, state_ledger, observability, recovery, security`
epistemic_class: `REPOSITORY_CODE_AUDIT_PLUS_LOCAL_COMPONENT_VALIDATION_PLUS_PRIMARY_STANDARD_SUPPORT`
status_hint: `CURRENT`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
canonical_parent: `r2:04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
run_id: `frank-20260809T1931p0700-chatgpt-secondary-log-state-three-cycle`

## Atomic claim

A FRANK recurrence-quality boundary must not treat numerically invalid telemetry as valid evidence and must make the controller policy/threshold identity reconstructible from the decision receipt.

The pre-fix H1 reference `loop_dynamics_quality_gate.py` violated both parts: negative/NaN quality or residual values could reach recurrence decisions, including `HALT_CANDIDATE_CONVERGED`, and the receipt carried only a readout hash, not a policy or receipt hash. The current FRANK repository trajectory adapter already rejected invalid numerical quality values and bound policy identity, revealing a cross-surface semantic mismatch rather than a missing concept in the target architecture.

H1 quality-gate v0.2 now rejects invalid numeric domains before classification, uses strict JSON-compatible hash input (`allow_nan=false`), domain-separates hashes, and binds readout plus policy into a deterministic receipt hash. External-effect authority remains `NONE`.

## Evidence refs

- pre-fix H1 component blob: `438ce0241e372c620c3d0b82924ca329f428d9d1`
- post-fix H1 component blob: `ac3767fb72f87da10ab625a7721486c9d5b400a9`
- component commit: `312c532db49d570c4866b9015dc72d63d568291d`
- tests commit: `c8c2f7919f30b2060bc6f658bc3cd49269881703`
- execution receipt: `research_entity/trigger_runs/frank/frank-20260809T1931p0700-chatgpt-secondary-log-state-three-cycle/EXECUTION_RECEIPT.json`
- current FRANK repo trajectory adapter commit: `gschaidergabriel/Dr.-Unterweger@ef22a56990e8ebdfc3e7cab6292b74daf55d94d2`
- RFC 8259: JSON does not permit NaN or Infinity numeric values.
- Python `json` documentation: default `allow_nan=True` emits NaN/Infinity even though that is outside the JSON specification; `allow_nan=False` rejects them.
- RFC 8785: cryptographic hashing/signing over JSON benefits from invariant canonical representations. The v0.2 implementation uses strict deterministic local serialization and domain separation; it does **not** claim full RFC 8785/JCS conformance.

## Validation

Local component execution after the change:
- 13/13 unit regressions PASS;
- 100,000-case fixed-seed property fuzz;
- 29,808 deliberately invalid telemetry cases rejected;
- 0 deliberately invalid cases accepted into recurrence decision logic.

Evidence class remains local/container component validation, not target-Ubuntu or whole-H1 acceptance.

## Counterhypothesis

Upstream producers may eventually make duplicated validation at this boundary redundant, and a single immutable controller version could make an explicit policy hash unnecessary.

The present evidence weighs against relying on that counterhypothesis because the two current surfaces had already drifted: the FRANK trajectory adapter was strict while the H1 quality gate was not. Boundary-local fail-closed validation and policy identity therefore currently reduce silent semantic drift.

## Falsifier / next test

Run the committed v0.2 gate inside the ordinary-code H1 spine on target Ubuntu with captured/frozen FRANK state histories. If a simpler upstream-only validation plus immutable versioning achieves identical invalid-input rejection, replay discrimination, recovery and latency with lower complexity, the duplicated boundary validation/policy hash may be reduced.

## Promotion boundary

This packet records a component-level implementation/validation result. It does not promote H1, FRANK v0.1, recurrence thresholds, emergence claims or target-host readiness.
