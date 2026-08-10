# HYPOFUSION Late Arrivals

Close-time worker refresh after Fusion2 found material new target-repository evidence.

## PR #157 — useful target-VPS mechanism evidence, implementation not selected

`GO: bind new effect starts to current self.root presence epoch` was closed as a duplicate after newer overlapping repair owners #160/#156 were identified, but it preserves a self-hosted target-VPS run (`31404574070`) with useful exact-candidate evidence:

- V17 presence-bound effect mechanism: PASS;
- stale holder A after B takeover fenced: PASS;
- successor could not adopt A reservation: PASS;
- pre-provider holder-change fence: PASS;
- confirmation+reservation+binding fault atomicity: PASS;
- historical V14 crash/replay/idempotency baseline: PASS;
- WP04 production effect-contract discriminator: PASS;
- SQLite integrity OK / FK violations 0;
- no external provider/network effect;
- focused gate about 0.18s, max RSS 25,824 KB.

The only red step was repository static integrity and was attributed to an independently moving telemetry-migrator invariant, not the V17 effect-fence mechanism.

Interpretation: this **strengthens the mechanism-level case for execution-epoch effect fencing**, while deliberately not promoting PR #157 as implementation authority. Current repair ownership remains on fresher overlapping lanes #160/#156.

## PR #163 — duplicate-work negative result

PR #163 was closed/superseded after fresh coordination found #156/#160 already owned the same gap. Useful retained alternative: carrying lease epoch inside the existing V14 reservation-event payload may be a simpler-baseline design if the selected sidecar/schema approaches prove over-complex.

Interpretation: add the event-payload design to the simpler-baseline set for `HF2-001`; do not maintain a third active effect-fence implementation.

## Effect on Fusion2

- `HF2-001-EXECUTION-EPOCH-SPINE`: strengthened.
- Selected implementation: unchanged; #160/#156 remain current repair candidates.
- Main/current Frank v0.1 acceptance: unchanged; no merge or end-to-end provider-effect acceptance was observed.
- Duplicate-work control: strengthened by closing #163/#157 implementation competition while retaining evidence/alternatives.
