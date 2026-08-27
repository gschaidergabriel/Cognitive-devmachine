# FRANK C9 — Negative Results and Rejected Shortcuts

Run: `20260809T0130p0700-chatgpt-secondary-r5`

These results remain explicit because they constrain the architecture even where no candidate is promoted.

## 1. `No destructive primitive` is not a sufficient safety boundary

CC13 already produced a stronger counterexample: a constructive-only program can create a harmful replacement and activate it. C9's new 500,000-case mechanism fuzz reaches the same conclusion from a different constructed state-transition family.

A gate that checked only `no_direct_destructive` admitted **227,517 oracle-unsafe commits**. Therefore the strong claim

`remove destructive syntax -> safe system`

is rejected.

The surviving narrower claim is:

`removing direct destructive protected-state constructors can reduce one effect path, but only complete runtime mediation and authority/effect controls can test containment.`

## 2. Static capability possession is not enough

The constructed gate `no destructive primitive + capability valid` still admitted **144,780 oracle-unsafe commits** because the capability could be applied against stale basis/source state, invalid selection, revoked authority, unknown closure or missing recovery conditions.

A capability answers *what class of effect may be attempted*. It does not by itself establish that *this exact effect is currently admissible*.

## 3. Every tested release-time dimension was load-bearing in the constructed family

Removing any one predicate from the full C9 oracle admitted unsafe commits:

- direct-destructive exclusion: 20,076;
- no model-minted permit: 11,991;
- valid capability: 50,596;
- known-valid closure: 31,330;
- current source epoch: 25,933;
- valid selection: 22,911;
- current revocation state: 14,556;
- recovery witness: 10,890.

This does **not** prove those eight predicates are a complete real-world safety basis. It only disproves, within this generated family, the tested shortcuts that omit one of them.

## 4. Zero C9 property-test mismatches are not a formal safety proof

The complete C9 gate had zero unsafe accepts because it was evaluated against an oracle defined from the same declared safety predicates. That is useful as a property/interface test, not as evidence that:

- the compiler cannot mis-lower an effect;
- child processes cannot escape;
- the OS/filesystem/database obeys the abstract recovery model;
- side channels are closed;
- all dangerous effects are represented by the tested predicates.

The real falsifier is end-to-end adversarial execution.

## 5. Provenance does not imply safe memory use

ClayGraph G2a and current external memory-security work both reject the shortcut that authentic/provenanced memory is automatically cognitively safe. A record can be stale, context-invalid, combined with another record into a harmful instruction, selected through manipulated structure or amplified by a bad salience learner.

C9 therefore keeps ingestion integrity, use-time admissibility, selection integrity and effect authority separate.

## 6. More activation is not always better cognition

G2a's constructed mixed workload showed exact-task harm under always-on blending and a severe frequent-topic attractor under naive scalar utility learning. C9 therefore rejects:

`persistent activation should always influence every query`.

CASAR routing and exact bypass/fallback remain necessary OPEN mechanisms.

## 7. Required context is not a forced workspace winner

C9 rejects a simplistic interpretation in which every effect-critical item is permanently pinned into the prompt or forced to win GWT competition. That would collapse candidate availability, selection and internal uptake into one mechanism and could itself consume context/attention budget.

Required-context closure means *availability obligation plus explicit overflow handling*, not epistemic or attentional dominance.

## 8. Logical unification is not physical monolith evidence

UnifiedDB U2 measured trade-offs rather than a universal winner. Same-process logical composition nearly matched its SQLite monolith in one cache-hot read proxy; the monolith was cheaper on its write proxy; service-like JSON boundaries cost more; replay/outbox added safety with write overhead.

C9 therefore rejects both:

- `one logical database => one physical DB/process`, and
- `decoupled sidecars/services are always better`.

Real FRANK traces decide PlacementVectors.

## 9. Android semantic success is not full FRANK/Qwen evidence

Android R1 demonstrated a functioning GitHub Actions -> Firebase -> virtual ARM lane and selected deterministic semantic checks. It did **not** establish:

- full FRANK memory fit;
- Qwen-class 4B package/load success;
- inference latency;
- sustained thermal behavior;
- battery cost;
- Linux-general performance.

No such claim is made in C9.

## 10. C9 does not establish emergence or consciousness

Typed admission, nested workspace receipts, recurrence and safe-effect constraints are architecture/measurement mechanisms. They do not establish phenomenal consciousness. Salience attractors are an explicit alternative explanation for recurrence-like persistence and must be controlled before emergence interpretation.

## 11. Registered provider gap in this run

The RAE provider router records E2B and other research providers, but this ChatGPT connector surface does not expose direct execution of that repository-side bridge. This run therefore used GitHub, native web and a local Python mechanism test. The absence of a fresh E2B run is recorded rather than silently treated as provider verification.

## 12. Strong promotion remains blocked

C9 remains OPEN because the following decisive evidence is missing:

- exact owner-selected Clay-adapted Qwen-class 4B causal experiments;
- real cross-language child-effect escape/utility matrix;
- target FRANK trace placement/recovery benchmark;
- persistent crash/restart/rebuild with real engines;
- Android Qwen package/load/inference/resource measurements;
- ancestry-distinct full-stack replication.
