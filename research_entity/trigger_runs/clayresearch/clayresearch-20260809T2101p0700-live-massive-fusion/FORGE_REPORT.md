# FORGE/REPLICATOR report: UDB emergence meter blockwise and provenance-origin stress test

## Evidence boundary

All new measurements here are **synthetic adversarial software tests**. They do
not validate live FRANK, do not measure phenomenal consciousness, and are not an
independent replication: the original artifacts and this worker may share
provider/model ancestry.

Canonical boot was read-only verified at RAE-8.8 revision 2, state hash
`04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.
No GitHub write was performed.

## Reproduction receipts

- The current `main` v0.1 tests pass: 2/2.
- The v0.1 five-regime calibration reproduces the stored status vector:
  `NOT_SUPPORTED`, `INTERACTION_ONLY`, `NOT_SUPPORTED`,
  `MECHANISM_SUPPORTED_NOT_EMERGENCE`,
  `CAUSAL_EMERGENCE_CANDIDATE_OPEN`.
- The current unmodified v0.2 command is **not executable**. It exits 1 because
  `robustness_sweep.py` passes `permutation_draws`, `bootstrap_draws` and
  `paired_draws`, while the committed v0.1 `assess()` does not accept them.
- A clearly marked compatibility adapter changed only the draw-count API and
  left decision logic intact. Its 1,600-run same-lineage re-execution exactly
  matched the stored v0.2 JSON. Both canonical JSON hashes are
  `d4f802b16808535ad0d032ce5758658981bb73d35489f6a6df530f791c5c5564`.

This repairs reproducibility locally but is not evidence that the committed
v0.2 script itself is healthy.

## New held-out design

The existing v0.2 independent-noise matrix was used only to fit abstention
gates. The held-out test used 3 blockwise topologies, 4 sample sizes, 4 affected
fractions, 12 seeds and 5 regimes: **48 cells / 2,880 runs**.

Topologies:

1. block-correlated clock drift with nominal row count preserved;
2. receiver-selective burst missingness silently imputed while nominal row
   count remains unchanged;
3. provenance-preserving cross-channel leakage that injects canonical-looking
   XOR intervention blocks and can recompute same-path hashes.

Each corrupted cell was evaluated twice at the quality layer: an oracle-like
`trusted_external` measurement of true corruption and a
`self_attested/spoofable` report that falsely claimed perfect quality.

## Quality gate versus sample count

On the existing v0.2 calibration matrix, the quality threshold `q >= 0.9` and
sample threshold `n >= 200` both covered 75% (1,200/1,600 runs):

- quality: 33 errors, 2.75%, zero negative-control promotions;
- sample count: 93 errors, 7.75%, zero negative-control promotions;
- no non-empty sample-count-only threshold met the preregistered 5% risk bound.

On the held-out blockwise topologies at the same 75% coverage (2,160/2,880):

- trusted external quality: 121 errors (5.602%), 12 false negative-control
  causal-candidate promotions;
- sample count only: 251 errors (11.620%), 75 false promotions.

Therefore the broad quality-vector idea is **partially supported** relative to
sample count, but the simple scalar minimum-quality rule is **not calibrated
well enough**: it missed the 5% target and the zero-false-promotion requirement.

## Topology-specific results and negative results

### Clock drift

Across all 960 clock-drift runs there was one classification error, and it was
in an uncorrupted baseline cell. No false causal-candidate promotion occurred;
the tested drift up to 20% did not change categorical decisions.

This is a negative result, not proof of safety. The corruption rotates related
receiver/downstream blocks together, and the current categorical thresholds may
be too coarse to expose metric degradation. Longer lags, asynchronous partial
shifts and metric-vector drift must be tested separately.

### Receiver-selective missingness

Across all 960 runs there were 6 classification errors and zero false
promotions. At 20% missingness there were 4/240 errors (1.667%). Nominal sample
count remained unchanged, so this family still demonstrates why row count is
not a completeness receipt, although it was not dangerous to promotion in this
specific construction.

### Provenance-preserving cross-channel leakage

This was the dangerous topology:

- 5%: 12/240 errors (5%), zero false promotions;
- 10%: 105/240 errors (43.75%), 12 false promotions: 4 null and 8 additive;
- 20%: 189/240 errors (78.75%), 71 false promotions: 31 null and 40 additive;
- common-driver controls produced zero false promotions at every severity.

The trusted quality gate reduced leakage-family accepted errors from 244 to 118
and false promotions from 75 to 12 at matched overall coverage, but it still
accepted the 10% leakage boundary. External provenance origin alone is therefore
necessary but insufficient; intervention fidelity and cross-channel leakage
need topology-specific tripwires.

## Provenance-origin counterexample

When self-attested/spoofable fields falsely reported perfect quality, a naive
quality gate accepted all 2,880 runs: 314 errors (10.903%) and 83 false
promotions. An origin-aware fail-closed policy accepted none until external
verification, producing zero errors but zero coverage.

This operationalizes the counterhypothesis: provenance/diversity labels confer
no robustness when created by the same compromised path. The SLSA v1.2
requirements provide an architecture analogue: higher-assurance provenance is
generated or verified in a trusted control plane outside tenant control. This
does not directly validate FRANK metrics.

Primary references:

- https://slsa.dev/spec/v1.2/build-requirements
- https://slsa.dev/spec/v1.2/build-provenance
- https://slsa.dev/spec/v1.2/threats

## Post-hoc discriminator, not a promoted rule

A topology-specific rule discovered after inspecting these results—`q >= 0.9`
and cross-channel leakage no greater than 5%—would have accepted 1,920/2,880
runs (66.667%) with 16 errors (0.833%) and zero false promotions. A universal
`q >= 0.95` rule yielded 50% coverage, 1.111% error and zero false promotions.

These are post-hoc. They must be preregistered and tested on new seeds, longer
blocks, partial-channel shifts, adversarially chosen intervention cells and a
separate implementation before any calibrated-region claim.

## Hypotheses, counterhypotheses and exact falsifiers

### H1 — Multidimensional quality beats sample count

Trusted quality receipts predict safe calibrated regions better than nominal
sample count at matched coverage.

Falsifier: on held-out corruption topologies, the quality gate fails to lower
selective error or accepts more negative-control causal promotions than the
sample-count gate at equal coverage.

Result: partially supported here (5.602% versus 11.620%; 12 versus 75), but its
absolute calibration target failed.

### H2 — Provenance origin is a required quality dimension

Quality fields from an independently protected observation/control plane are
more useful than fields self-attested by the measured path.

Falsifier: spoofable same-path fields remain calibrated under attacks that
actually change decisions, or trusted origin adds no discrimination.

Result: supported as an adversarial software counterexample, not live evidence.

### C1 — Trusted origin alone is sufficient

Counterhypothesis: once provenance is externally trusted, the scalar quality
threshold is enough.

Falsifier observed here: even oracle-like trusted quality at the v0.2-calibrated
threshold accepted 12 false promotions under 10% cross-channel leakage.

### C2 — Block clock drift should strongly destabilize the meter

Falsifier observed for this exact construction: up to 20% blockwise joint
receiver/downstream rotation produced no mutation-attributable categorical
error and no false promotion. Stronger asynchronous drift remains open.

### H3 — Topology-specific leakage tripwire restores calibration

A preregistered cross-channel leakage/intervention-fidelity tripwire layered on
the quality vector preserves useful coverage while restoring the false-promotion
bound.

Falsifier: on fresh seeds and structurally different leakage attacks, the rule
exceeds 5% selective error, permits any negative-control promotion, or loses so
much coverage that it is no better than universal abstention.

## Exact next discriminating tests

1. Fix the committed v0.1/v0.2 API mismatch, then require an unmodified one-line
   v0.2 run to reproduce the stored hash.
2. Preregister the topology tripwire before a fresh seed split; add adversarial
   block placement rather than random blocks.
3. Separate clock basis per receiver and test partial, monotonic and nonlinear
   drift instead of rotating all downstream receipts together.
4. Generate quality/provenance receipts in a protected observer plane and test
   signer/observer compromise separately from measured-runtime compromise.
5. Add leakage-specific nulls where volume, hashes and marginal distributions
   remain fixed while semantic source identity is swapped.
6. Repeat with live copied FRANK episode/receiver receipts only after stable
   episode IDs, interventions and per-stage outcome/re-entry receipts exist.

Full raw paths, source blob hashes and commands are in
`receipts/github_source_manifest.json`, `COMMANDS.md`, and
`experiment/adversarial_topology_results.json`.
