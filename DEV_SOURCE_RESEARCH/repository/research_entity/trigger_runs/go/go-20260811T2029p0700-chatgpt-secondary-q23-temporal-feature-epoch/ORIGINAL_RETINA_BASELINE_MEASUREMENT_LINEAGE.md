# Original Retina baseline — measurement lineage and regeneration boundary

Run: `go-20260811T2029p0700-chatgpt-secondary-q23-temporal-feature-epoch`
Work package: `F-V01-06-DIGITAL-RETINA-MVC`
No second GO out-of-box experiment is introduced here.

## Why this delta exists

After exact source/E2E recovery, historical Retina measurements must not be collapsed into one synthetic scalar. The surviving artifacts correspond to different code/config/evaluation points and carry materially different latency/coverage numbers.

## Recoverable source ancestry

Original standalone source anchor:

`gschaidergabriel/digital-retina@819dcac12253b7de45795239b44482627ade624f`

The standalone README states the service was extracted from `gschaidergabriel/agentforge` `engine/vision/`.

The private `gschaidergabriel/agentforge` repository is also reachable. `engine/vision/retina.py` contains the complete Digital Retina v8 classifier architecture, CIFAR-10 loader, augmentation/training loop, evaluation loop and `torch.save` persistence path used to create a `retina_v8.pt`-class artifact.

## Exact-weight versus reconstructed-weight boundary

The v8 training source fixes the LSH projection with NumPy `RandomState(42)` but does **not** set a global Torch seed for network initialization, data permutation, random crop/flip or cutout.

Therefore:

- a newly trained weight from recovered source can become a valid `RECONSTRUCTED_SURROGATE` baseline candidate;
- it must **not** be labeled the exact historical `retina_v8.pt`;
- exact historical weight recovery remains preferable and preserves the `NO_ORIGINAL_BASELINE -> NO_REPLACEMENT_CLAIM` gate;
- any reconstructed surrogate requires its own seed/runtime/dependency/hardware metadata and repeated-run distribution.

## Historical result artifacts now physically recovered

Drive `digital-retina-e2e/coverage/` retains, among other artifacts:

- `p12_FINAL.json` — hard-set final snapshot;
- `freshset_coverage.json` — 32-image fresh-set snapshot;
- iterative hard-set result snapshots;
- final/honest reports;
- cached baselines.

Locally hashed copies recovered during this GO cycle:

- `p12_FINAL.json`: SHA-256 `6dc0ef16e1756834be04502cf501ae25a0778f37ee846fdec32bb0e69aff31b0`;
- `freshset_coverage.json`: SHA-256 `2858648db19c818e091ab119f58190a87338bcf04441e8c7a985f496c86cbe23`.

These hashes bind the exact recovered JSON bytes for future lineage work.

## Hard-set snapshot facts

`p12_FINAL.json` contains 12 result rows and 279 baseline phrases. Stored summary fields report:

- strict coverage: 87.81362007168458%;
- CLIP-lenient coverage at threshold 0.20: 94.6236559139785%;
- strict covered phrases: 245 / 279;
- lenient covered phrases: 264 / 279.

The same raw rows contain per-image `retina_elapsed_ms` and `wall_retina_s`.

Computed from the 12 stored rows without modifying them:

- `retina_elapsed_ms`: p50 24809.896 ms; p90 35118.603 ms; p95 36055.599 ms; p99 36822.817 ms; min 19782.799 ms; max 37014.621 ms; mean 26807.194 ms;
- `wall_retina_s`: p50 24.872 s; p90 35.136 s; p95 36.071 s; p99 36.837 s; min 19.797 s; max 37.028 s; mean 26.830 s.

These numbers are **artifact-local** and must not be generalized to another pipeline configuration or host.

## Fresh-set snapshot facts

`freshset_coverage.json` contains 32 result rows and 681 baseline phrases. Stored summary fields report:

- strict coverage: 72.2466960352423%;
- CLIP-lenient coverage at threshold 0.20: 92.51101321585904%;
- strict covered phrases: 492 / 681;
- lenient covered phrases: 630 / 681.

The 32 rows contain `wall_retina_s` but not the same internal elapsed field as the hard-set file.

Computed from those stored wall times:

- p50 26.689 s;
- p90 29.679 s;
- p95 31.613 s;
- p99 35.071 s;
- min 4.054 s;
- max 35.669 s;
- mean 25.866 s.

## Conflict discipline

Historical source/docs also contain materially lower latency anchors, including approximately 900 ms p50 in the standalone README/core comments and approximately 5 s lean / approximately 18 s deep in later May-27 reporting. These must remain **separate evidence points**, because the raw hard/fresh result files above show roughly 25-27 s central wall times.

Do not average these numbers. Before using any historical latency as an Original Baseline row, bind:

- exact source commit;
- environment flags, especially caption/deep settings;
- live endpoint version;
- fixture/result file hash;
- model/weight hashes where recoverable;
- warm/cold state;
- host/runtime metadata.

The final May-27 paper commit also reports a 44-image / 960-phrase aggregate of 93.1% lenient and 75.1% strict. That aggregate is preserved as a documented historical result, but it should not be recomputed by simply adding arbitrary later/earlier JSON snapshots unless their run lineage matches the paper's exact input set.

## Security boundary on eval recovery

The recovered historical hard-set driver contains embedded fallback credentials. Those values were not copied here or used. Before any replay, use a sanitized driver with secret injection and frozen cached baselines; do not contact external oracle providers unless a new experiment explicitly requires and authorizes that dependency.

## Next discriminating work

1. Recover exact historical custom weights if possible.
2. If exact `retina_v8.pt` remains missing, run multiple seeded reconstructed-surrogate trainings from `agentforge/engine/vision/retina.py`; characterize variance rather than selecting one best seed.
3. Determine whether the GoL library and DINO artifacts have deterministic export/build paths and classify exact versus reconstructed independently.
4. Pair every recovered result JSON to the nearest verifiable source/config/runtime receipt before admitting it as a baseline row.
5. Re-run the exact original/surrogate on accepted target hardware with frozen local fixtures and no external credential fallback.
