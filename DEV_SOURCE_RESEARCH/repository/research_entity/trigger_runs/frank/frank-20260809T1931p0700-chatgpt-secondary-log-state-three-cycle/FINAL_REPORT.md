# FRANK Log/State Testing + Three-Cycle Research Fusion

Run: `frank-20260809T1931p0700-chatgpt-secondary-log-state-three-cycle`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Task class: substantial FRANK research/build request; **not** an exact reserved-trigger invocation  
Promotion: **NONE**  
Release effect: **NONE**  
Target Ubuntu executed: **NO**

## 1. Requested cycle

The owner requested an explicit sequence:

`FRANK testing + logs/states evaluation -> Fusion -> web research -> hypotheses -> renewed Fusion`, repeated for three cycles, followed by analysis, one concrete improvement, and durable return of all useful results into research.

This run therefore used current canonical/repository evidence first, distinguished the Research Entity worker from FRANK, compared the Research Entity H1 reference surface with the live-lineage `Dr.-Unterweger` FRANK repository, executed local discriminators, researched primary external sources, implemented one bounded improvement, re-read the remote repository, and compiled the results into run artifacts and knowledge micro-packets.

## 2. Canonical/state boot

Verified canonical identity before substantive work:

- Research Entity: RAE-8.8, revision 2.
- Canonical state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.
- Worker identity: `chatgpt-secondary`.
- FRANK is the separate research/build subject, not the worker identity.
- Current repository command/identity contracts supersede older Project Source wording where they differ.

Relevant current state assembled rather than reading the whole repository:

- FRANK research protocol and current fixed final architecture direction;
- current embodied-local + peer cognitive-fabric state contract;
- H-WP-02 state-ledger oracle/validation receipts;
- loop-dynamics reference controller;
- loop residual-quality experiment and quality gate;
- post-hoc recurrence trajectory readout;
- current `Dr.-Unterweger` trajectory adapter;
- recent hard-close/open blocker state.

## 3. Logs/states fusion before Cycle 1

### H-WP-02 state ledger

The current oracle-ledger evidence is substantially stronger than an early prototype:

- 9/9 local deterministic regression tests in the oracle-merge receipt;
- typed set canonicalization while preserving ordered sequence sensitivity;
- semantic-state identity separated from state-version/history identity;
- execution trace identity separated again;
- payload-bound idempotency;
- stale epoch fail-closed;
- atomic rollback after injected failure;
- deterministic replay and verification;
- exact snapshot restore and tamper rejection;
- same-request two-writer concurrency resolving to one commit plus one idempotent replay;
- 5,000 typed-set permutations and 5,000 ordered mutations exercised;
- 1,000-event replay with equal reconstruction.

Important limit: this is still local/synthetic mechanism evidence. The receipt explicitly says no target-Ubuntu execution and no live `frankv0.1` Golden Corpus differential.

### Loop/readout evidence

The H1 loop work has evolved through several distinct layers:

1. typed single-readout regime/controller reference;
2. synthetic experiments demonstrating why state-delta-only stopping confuses convergence with low-change unresolved stall;
3. residual-quality sensitivity experiments adding estimator identity/version, uncertainty and measurement age;
4. post-hoc short-trajectory readout to avoid classifying a dynamic regime from one scalar snapshot;
5. current FRANK repository adapter that fuses trajectory dynamics with residual-quality gating.

The quality experiment previously executed 100,000 property-fuzz cases with zero violations **inside its sampled valid input domain**. That distinction became important in this run.

## 4. Cycle 1 — Internal state/log fusion -> hypotheses -> discriminator

### Fusion 1 finding: cross-surface semantic drift

The newest `Dr.-Unterweger` adapter (`harness/loop_dynamics_probe.py`, commit `ef22a56990e8ebdfc3e7cab6292b74daf55d94d2`) already validates:

- finite/non-negative state delta and residual pressure;
- finite marginal utility;
- finite/non-negative residual uncertainty;
- non-negative measurement age;
- missing/stale/high-uncertainty residual metadata -> `ROUTE_READOUT_UNCERTAIN`;
- policy/threshold identity -> deterministic policy/receipt hash.

The Research Entity H1 `loop_dynamics_quality_gate.py` at blob `438ce0241e372c620c3d0b82924ca329f428d9d1` did **not** contain equivalent domain validation and did not bind policy identity into a receipt hash.

This produced a real reference-surface inconsistency: the FRANK lineage adapter was stricter than the H1 reusable quality component it referenced.

### Cycle 1 hypotheses

**H-FRANK-LOOP-011**  
Invalid/non-finite telemetry must be rejected before recurrence classification; relying on producer validity is insufficient at this boundary.

Counterhypothesis: upstream validation makes duplicated boundary checks redundant.

**H-FRANK-TRACE-012**  
Controller policy/threshold identity must be decision-receipt-visible for deterministic replay and audit.

Counterhypothesis: immutable executable identity is sufficient, making explicit policy identity redundant.

### Executed pre-fix discriminator

Using the exact current v0.1 quality-gate semantics in a local reproduction:

- `residual_uncertainty = -1.0` -> `HALT_CANDIDATE_CONVERGED`;
- `measurement_age_cycles = -3` -> `HALT_CANDIDATE_CONVERGED`;
- `residual_uncertainty = NaN` -> `HALT_CANDIDATE_CONVERGED`;
- `residual_pressure = -0.1` -> `HALT_CANDIDATE_CONVERGED`;
- `residual_pressure = NaN` -> `CONTINUE`.

The old `_hash_readout()` used Python `json.dumps` defaults, so NaN was emitted into the hash input rather than rejected.

A second discriminator showed policy invisibility:

- same valid readout;
- two different convergence thresholds that still produced the same categorical decision;
- complete old receipt objects were identical;
- changing the threshold far enough to change the decision still left `readout_sha256` identical, because no policy identity was represented.

### Cycle 1 fusion outcome

H-FRANK-LOOP-011 is supported at component level by a reproducible defect, not merely architecture preference.

H-FRANK-TRACE-012 is supported as a replay/provenance constraint, though the best long-term representation (explicit policy hash vs executable content hash + deployment identity) remains falsifiable.

## 5. Cycle 2 — Primary standards/provenance research -> renewed fusion

Primary sources researched:

1. RFC 8259, *The JavaScript Object Notation (JSON) Data Interchange Format*  
   https://www.rfc-editor.org/rfc/rfc8259.html

   Relevant constraint: Infinity and NaN are not permitted by the JSON number grammar.

2. Python `json` library documentation  
   https://docs.python.org/3/library/json.html

   Relevant implementation fact: Python defaults to `allow_nan=True`, allowing NaN/Infinity serialization even though this is outside the JSON specification; `allow_nan=False` rejects them.

3. RFC 8785, *JSON Canonicalization Scheme (JCS)*  
   https://www.rfc-editor.org/rfc/rfc8785.html

   Relevant design support: cryptographic operations over JSON require invariant representation to be reliably repeatable. This run does **not** claim the new FRANK serializer is a full JCS implementation; JCS is evidence for explicit deterministic canonicalization discipline.

4. OpenTelemetry Trace API / Logs data model  
   https://opentelemetry.io/docs/specs/otel/trace/api/  
   https://opentelemetry.io/docs/specs/otel/logs/data-model/

   Relevant design support: trace/span identity and causal context are represented separately from operation attributes/log bodies, and trace context can connect logs to causal execution structure.

5. W3C PROV-O  
   https://www.w3.org/TR/prov-o/

   Relevant design support: Entity, Activity and Agent/provenance relationships are distinct, supporting FRANK's separation between state evidence, transformation/activity and actor/origin.

### Cycle 2 revised hypotheses

**H-FRANK-STATE-014**  
When H-WP-02 is fused into the ordinary H1 spine, recurrence receipts should test direct binding to `state_version_hash` / `trace_root_hash` (or equivalent immutable state/causal identities), not only a scalar `state_epoch` and a local readout hash.

Counterhypothesis: external ledger reconstruction from `state_epoch` + readout/policy hashes is always unambiguous, so direct lineage binding adds only payload cost.

### Cycle 2 fusion outcome

The correct improvement is not merely “reject NaN.” The stronger boundary is:

`validated readout identity + explicit policy identity + deterministic decision receipt + preserved external state/trace lineage + no effect authority`.

Only the first three were implemented in this run because they can be changed and tested locally without inventing a premature H-WP-02 integration schema. Direct state-ledger trace-root binding remains an OPEN integration hypothesis.

## 6. Cycle 3 — Recurrence/halting research -> renewed fusion

Primary research reviewed:

1. Alex Graves, *Adaptive Computation Time for Recurrent Neural Networks*, arXiv:1603.08983.  
   Adaptive recurrent computation can learn variable numbers of processing steps; benefits are task-dependent rather than universal.

2. Andrea Banino et al., *PonderNet: Learning to Ponder*, arXiv:2107.05407.  
   Learns adaptive computation depth with an explicit performance/compute tradeoff.

3. Harsh Kohli et al., *Loop, Think, & Generalize: Implicit Reasoning in Recurrent-Depth Transformers*, arXiv:2604.07822.  
   In controlled from-scratch compositional tasks, recurrent depth improves systematic/depth extrapolation, while excessive recurrence produces overthinking. Transfer to FRANK's pretrained/local 4B setting is not established by this paper.

4. Costin-Andrei Oncescu et al., *The Recurrent Transformer: Greater Effective Depth and Efficient Decoding*, arXiv:2604.21215.  
   In tested 150M/300M regimes, recurrence can trade effective depth against width/KV-cache characteristics. This is architecture evidence, not validation of FRANK's stop controller.

### Cycle 3 hypotheses

**H-FRANK-LOOP-013**  
Typed, quality-gated adaptive recurrence will beat tuned fixed-depth and state-delta-only stopping on real/frozen FRANK episodes under matched outcome/latency/compute/recovery costs.

Counterhypothesis: a simpler fixed-budget/event-driven baseline matches or wins after fair tuning.

**H-FRANK-QCAL-015**  
Residual-quality and convergence thresholds should eventually be calibrated/versioned per estimator and possibly per loop family rather than assumed globally correct.

Counterhypothesis: one global threshold set remains adequately calibrated across FRANK loops and estimator versions.

### Cycle 3 fusion outcome

External recurrence literature supports keeping adaptive depth as a serious candidate and directly reinforces an anti-overthinking requirement. It does **not** validate FRANK's current threshold values. Therefore this run makes no threshold promotion and no claim that recurrent depth is intrinsically superior.

The highest-information next experiment remains a matched Golden Trace benchmark across:

- fixed depth;
- delta-only;
- residual-aware dual signal;
- typed quality-gated adaptive recurrence.

Measure false convergence, missed productive recurrence, overthinking/divergence, routing/escalation, task outcome, latency, compute/tokens, memory, recovery and effect-gateway non-authority.

## 7. Concrete improvement implemented

### H1 Quality Gate v0.2

Updated:

`research_entity/harness/reference/loop_dynamics_quality_gate.py`

Commit:

`312c532db49d570c4866b9015dc72d63d568291d`

New component blob:

`ac3767fb72f87da10ab625a7721486c9d5b400a9`

Changes:

1. validate `loop_id` and integer domains;
2. reject negative state epochs, low-delta streaks and measurement ages;
3. reject NaN/Infinity/non-numeric bool-like telemetry;
4. reject negative state delta/residual pressure;
5. constrain oscillation indicator and residual uncertainty to `[0,1]`;
6. validate controller thresholds and logical stalled/converged ordering;
7. hash strict JSON input with `allow_nan=False`;
8. domain-separate readout, policy and receipt hashes;
9. add explicit `controller_policy_id`;
10. add `policy_sha256` and `receipt_sha256`;
11. preserve `authority=NONE`, `effect_eligible=false`, `effect_gate_required=true`.

Updated tests:

`research_entity/harness/reference/test_loop_dynamics_quality_gate.py`

Commit:

`c8c2f7919f30b2060bc6f658bc3cd49269881703`

New tests blob:

`f2317a60a14d58e3bac5110ed389707f06e41047`

### Local post-fix validation

- 13/13 unit tests PASS;
- deterministic receipt test PASS;
- invalid telemetry rejection tests PASS;
- invalid policy tests PASS;
- policy/threshold receipt-identity tests PASS;
- authority guard remains PASS.

Property fuzz, fixed seed `202608091931`:

- 100,000 cases total;
- 29,808 deliberately invalid cases rejected;
- **0 invalid cases accepted**;
- accepted-decision counts:
  - `ROUTE_READOUT_UNCERTAIN`: 46,907
  - `CONTINUE`: 19,814
  - `HALT_CANDIDATE_CONVERGED`: 1,894
  - `HALT_MARGINAL`: 1,338
  - `ESCALATE_STALLED`: 239

This fuzz validates the new input-domain boundary under generated cases. It is not a live FRANK behavioral benchmark.

GitHub was re-read after writes and both expected blobs were present. The combined commit-status surface returned no statuses for the tests commit, so no CI success is claimed.

## 8. Final three-cycle fusion

### Confirmed / materially strengthened

1. **The old H1 quality gate had a real invalid-telemetry acceptance defect.**  
   This was reproduced and fixed.

2. **FRANK live-lineage and H1 reference semantics had drifted.**  
   `Dr.-Unterweger` already rejected invalid quality telemetry and policy-bound receipts; H1 did not. v0.2 aligns that boundary more closely.

3. **Policy identity belongs in replay evidence.**  
   The old receipt could hide threshold changes when categorical output stayed unchanged. v0.2 makes policy changes receipt-visible.

4. **The state ledger's richer identity model is relevant to loop observability.**  
   H-WP-02 already distinguishes semantic state, state version/history and trace root. The loop boundary should be tested against those identities during the future spine fusion rather than inventing a second lineage model.

5. **Adaptive recurrence remains the stronger research candidate, not a settled theorem.**  
   Internal synthetic discriminators plus external adaptive/recurrent research justify continued investment, but real FRANK Golden Traces must decide against simpler baselines.

### Preserved negative evidence / limits

- No target-Ubuntu execution occurred.
- No live `frankv0.1` Golden Corpus was available/executed in this worker surface.
- No Qwen-class 4B recurrence benchmark occurred.
- No full state-ledger -> loop -> GWT -> effect-gateway Golden Trace ran end to end.
- No H1 release gate advanced.
- Current hard thresholds remain uncalibrated engineering defaults.
- RFC 8785 was used as design evidence for canonical hashing discipline; the v0.2 serializer is not claimed to implement the full JCS specification.
- Adaptive-computation/recurrent-depth papers do not directly prove FRANK's architecture or threshold choices.

## 9. Durable research return

Created:

- `EXECUTION_RECEIPT.json` — exact defect, implementation commits/blobs, tests/fuzz and remaining falsifiers;
- `HYPOTHESIS_MATRIX.json` — H-FRANK-LOOP-011 through H-FRANK-QCAL-015 with counterhypotheses and falsifiers;
- `KMP-FRANK-R10-LOOP-QUALITY-POLICY-RECEIPT-20260809.md` — component-level confirmed boundary knowledge;
- `KMP-FRANK-R10-ADAPTIVE-RECURRENCE-HALTING-20260809.md` — open adaptive-recurrence hypothesis with primary research and competing baselines;
- this `FINAL_REPORT.md`.

Affected research domains receiving explicit feedback through these artifacts:

- `frank`: component semantics and next Golden Trace discriminator;
- `harness`: v0.2 quality-gate implementation + tests;
- `loop_dynamics`: invalid-domain and policy-identity invariants;
- `state_ledger`: future state-version/trace-root binding hypothesis;
- `gwt`: recurrence decision remains proposal/control evidence, not effect authority;
- `observability/recovery`: receipt replay and causal lineage requirements;
- `security/authority`: no new effect authority introduced;
- `performance/model_runtime`: adaptive recurrence must beat tuned simpler baselines under matched compute/latency;
- `emergence`: recurrence remains a mechanism/readout candidate, not phenomenal-consciousness evidence and not sufficient emergence evidence by itself.

## 10. Highest-information next work

1. Execute v0.2 quality gate/tests on target Ubuntu.
2. Fuse H-WP-02 oracle state identity into the ordinary H1 loop trajectory path without creating duplicate state truth.
3. Build frozen/live-derived Golden Trace episodes with explicit estimator ID/version, uncertainty, freshness, state-version and trace ancestry.
4. Run four-controller matched benchmark: fixed-depth vs delta-only vs residual-aware vs typed quality-gated adaptive recurrence.
5. Calibrate quality/convergence thresholds by estimator/version/loop family only if the traces support stratification.
6. Add stale/out-of-order/duplicate/cross-instance state-message cases from the current embodied-local + peer cognitive-fabric contract.
7. Keep every recurrence outcome proposal-only until the independent effect gateway establishes actual external authority/effect receipts.

## 11. Bottom line

The three-cycle run produced a nontrivial executable result rather than another architecture note: it found a concrete H1 boundary bug by comparing FRANK's current adapter against Research Entity reference state, reproduced unsafe invalid-input behavior, used primary standards/provenance research to refine the fix, used adaptive/recurrent research to preserve the larger hypothesis rather than overpromote it, hardened the quality gate, passed local regressions/fuzz, re-read the committed code, and returned both confirmed and open knowledge into persistent research artifacts.

The next scientific bottleneck is no longer this specific invalid-input defect. It is **real/frozen H1 trajectory evidence and target-Ubuntu execution**, especially the fused state-ledger/loop/GWT path and fair controller baselines.
