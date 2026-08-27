# 666 Post-Level-0 Field Run — Proof-Carrying Adaptive State

- **Run:** `666-20260809T1521p0700-chatgpt-secondary-pcas`
- **Field:** `field-666-20260809T1521p0700-proof-carrying-adaptive-state-485652b7`
- **Actor:** `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
- **Canonical parent:** r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **Level-0 parent:** `666_LEVEL0_RELEASE_20260809T1519p0700` = PASS
- **Program milestone at spawn:** `BASE_CLAYCODE_RELEASE`
- **Seed:** `5212444565239029137`
- **Seed basis SHA-256:** `485652b7227cdd91f0192b058f51138aeced247ca3821ca7f3c7f138b2ac1db6`

## Selection

Seeded stochastic selection among high-value, non-duplicate candidates selected **Proof-Carrying Adaptive State** (formal methods × continual learning × provenance/rollback). The field is intentionally orthogonal to the just-completed Project-Frankenstein visual-lineage assimilation while still connecting to the new Unified Memory ↔ Retina owner directive.

## Research question

Can FRANK treat every autonomous learned-state change as a *candidate artifact* that must carry a small machine-checkable evidence/provenance/rollback certificate before the change becomes authoritative?

## Mechanism candidate: ASPC

**Adaptive State Promotion Certificate (ASPC)**

`candidate state -> shadow evaluation -> certificate construction -> deterministic verifier -> atomic promote | quarantine/reject -> last-known-good rollback`

Minimum certificate surface:

1. parent state/version;
2. candidate content hash;
3. promotion-policy version;
4. feature/schema compatibility identity;
5. training/evidence provenance and trust tier;
6. held-out/replay receipts;
7. retention/forgetting gate;
8. unknown/conflict gate where applicable;
9. resource-budget gate;
10. rollback pointer;
11. verifier result.

A certificate proves only that declared policy and evidence receipts passed. It **does not prove that a model label, memory prior or learned prediction is sensor truth**.

## External evidence used

- George C. Necula, *Proof-Carrying Code*, POPL 1997: producer-supplied safety evidence plus a comparatively small verifier motivates the architectural pattern.
- Torres-Arias et al., *in-toto*, USENIX Security 2019: provenance-bound verification across a multi-step artifact pipeline supports binding promotion to verifiable lineage.
- Rolnick et al., *Experience Replay for Continual Learning*, arXiv:1811.11682: replay is practical evidence for guarding prior capability/knowledge against forgetting.
- Fulton & Platzer, *Verifiably Safe Off-Model Reinforcement Learning*, arXiv:1902.05632: verification-preserving model updates demonstrate that formal update gates and learning can be combined, although the domain differs from FRANK.

These sources support components of the mechanism, not the untested claim that ASPC is optimal for FRANK.

## Hypotheses

### PCAS-H1 — conjunctive evidence beats one utility scalar for unsafe promotion

A proof-carrying promotion gate can reduce unsafe adaptive-state promotions when safety constraints span retention, open-set behavior, resource limits, provenance and compatibility.

**Falsifier:** on representative FRANK update streams, a simpler existing/scalar gate matches or beats unsafe-promotion rate at equal useful-promotion recall and lower complexity.

### PCAS-H2 — no new ClayCode primitive should be needed

ASPC should first be represented as ordinary typed canonical data plus deterministic verifier/effect logic in existing ClayCode semantics.

**Falsifier:** an executable adaptive-state case cannot preserve authority, rollback and certificate semantics through the existing IR/lowering without an escape hatch.

### PCAS-H3 — version-bound certificates enable replayable Unified Memory learning

Binding certificates to UnifiedDB/Unified Memory versions and evidence lineage may make online learning crash-replayable and auditable.

**Falsifier:** crash/replay cannot reconstruct the unique authoritative post-update state or leaves rollback ambiguous.

## Counterhypotheses

1. The gate may be too conservative and suppress useful plasticity.
2. A valid certificate can create false assurance because it verifies the encoded policy, not the truth/independence of the underlying data.
3. Existing candidate-vs-current shadow evaluation plus rollback may already be sufficient with less machinery.

## PCAS-E0 synthetic discriminator

A fixed-seed Monte Carlo test generated **100,000** candidate adaptive updates with latent task gain, retention delta, unknown-FPR delta, CPU cost and provenance/compatibility/rollback flags. Observed metrics contained noise.

Unsafe ground-truth condition in the simulation: retention delta `< -0.02`, unknown-FPR increase `> 0.01`, CPU cost `> 12 ms`, or missing provenance/compatibility/rollback.

| policy | accepted | unsafe among accepted | beneficial-safe recall |
|---|---:|---:|---:|
| weighted scalar | 51.883% | 41.141% | 84.693% |
| conservative certificate gate | 18.285% | 0.870% | 51.953% |

**Interpretation:** in this synthetic construction the conjunctive gate greatly reduced unsafe promotions, but it also rejected many more beneficial updates. Therefore the real target is the **safety/plasticity Pareto frontier**, not maximal rejection.

**Epistemic status:** synthetic mechanism stress test only. Distributions and thresholds were worker-chosen. This is not a FRANK performance result.

## Cross-branch implications

### ClayCode

Connects directly to `CC-WP-03-IR-TYPES`, `CC-WP-04-TYPE-EFFECT`, `CC-WP-06-COMPILER-LOWERING`, and `CC-WP-11-FUZZ-CONFORMANCE`. Implement ASPC first without language redesign; require an executable counterexample before semantic change.

### UnifiedDB / Unified Memory

Persist parent/candidate/promoted version identity, evidence lineage, verifier-policy version and rollback pointer transactionally. Explicitly test crash points between verification, state commit and index publication.

### Harness

Add replay/differential cases for accepted, rejected, stale-version, poisoned-label and crash-mid-promotion updates. H2 must reproduce the same verifier receipt semantics.

### FRANK / Retina

Apply first to the Unified Memory ↔ Retina online-learning loop. Certification must never let a memory prior acquire sensor authority; `memory_prior != sensor_truth` remains invariant.

## Next discriminating tests

- **PCAS-E1:** replay actual H1 adaptive visual/memory update candidates under scalar-vs-certificate policies at matched useful-promotion recall.
- **PCAS-E2:** crash at each promotion step; require one authoritative version and deterministic rollback.
- **PCAS-E3:** inject BRONZE pseudo-label poisoning and stale feature-backbone versions; verifier must reject autonomous truth promotion.
- **PCAS-E4:** measure certificate bytes, verifier latency and state-growth overhead on project hardware.
- **PCAS-E5:** ClayCode roundtrip/lowering differential test before considering any language semantic change.

## Synthesis

ASPC is worth carrying forward as a **research candidate**, not as canonical architecture. It offers a concrete way to unify provenance, replay, rollback and learning admission across Retina/Unified Memory, UnifiedDB, Harness and ClayCode. The immediate evidence also exposes the main danger: verification can trade too much plasticity for safety. The next useful experiment must therefore compare policies on the same real FRANK candidate-update stream and plot unsafe promotion against useful-promotion recall and overhead.

## Promotion decision

`OPEN_RESEARCH_CANDIDATE / ROUTED_TO_MESH`

No canonical architecture promotion is justified yet.
