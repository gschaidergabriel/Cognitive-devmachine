# Mandatory RAE Visible Status Footer

Every substantive response by a project Research-Entity worker must end with a clearly separated status block. Trigger runs always include it. Non-substantive social replies may omit it.

The footer reports two separate horizons:

1. **NEXT LEVEL** — the first unpassed shared program gate and its strict machine-derived progress.
2. **DOOMSDAY / Clay 0.1 - Chief Developer First Test** — a freshly recomputed forecast for the first strict internal chief-developer test candidate, not a public release.

## Canonical rendering contract

The footer MUST be the final visible block and MUST be wrapped in one plain fenced Markdown code block. The opening fence line must be exactly ` ```text ` and the closing fence line exactly ` ``` `.

Rules:

- opener exactly ` ```text ` with no attributes;
- no indentation;
- no Unicode/box-drawing frame characters;
- no Markdown tables or pipe layout inside the footer;
- no nested fences;
- no visible content after the closing fence;
- progress bars use ASCII only;
- command separators may use `·`.

## Dynamic sources

NEXT LEVEL resolves from:

- `PROGRAM_STATE.json`;
- `PROGRAM_THROUGHPUT.json`;
- current stage workspace;
- `tools/program_progress.py`.

DOOMSDAY resolves from:

- `DOOMSDAY_DYNAMIC_FORECAST_PROTOCOL.md`;
- `CLAY_0_1_CHIEF_DEVELOPER_ACCEPTANCE_CONTRACT.md`;
- `DOOMSDAY_FORECAST_MODEL.json`;
- `HISTORICAL_EARNED_WORK.json`;
- `DOOMSDAY_CAPABILITY_RULES.json`;
- `DOOMSDAY_EVENTS.jsonl`;
- current stage/test evidence;
- throughput/capacity/hardware;
- all registered APIs/tools and `*_RESEARCH_CAPABILITY.json` extensions;
- `tools/doomsday_forecast.py` for remaining critical-path forecast;
- `tools/program_progress.py` for lifetime earned-work overlay and visible status.

No fixed DOOMSDAY date is canonical.

## NEXT LEVEL semantics

The first unpassed stage is shown.

Claimed/active work earns no strict gate percentage merely by being active.

Level 0 uses frozen atomic archive obligations. Before its denominator is frozen, exact Level-0 progress remains `0%` even though DOOMSDAY may already be far above zero because of historical earned work.

Level 0 has a project-owner fixed active wall-clock ceiling of `3h`; external connector waiting is reported separately and does not justify false PASS.

## DOOMSDAY progress semantics

DOOMSDAY is a lifetime project completion estimate toward the internal Clay 0.1 chief-developer first-test candidate.

It must not imply that the project began when current workspaces were created.

During Level 0:

- approximately eight months of prior FRANK/XENO/ClayCode/GWT work are represented through `HISTORICAL_EARNED_WORK.json`;
- the historical contribution remains a clearly labeled calibration prior until Level 0 maps the source history to current Clay 0.1 work;
- the visible percentage may therefore include a calibration band.

After Level 0, evidence-mapped reusable/avoided current-work equivalents replace the temporary historical-retention prior.

Current remaining-scope progress is then layered on top of the earned historical baseline.

Scope discovery may move DOOMSDAY backward. Verified jumps may move it forward discontinuously.

## ClayCode requirement

DOOMSDAY requires `CLAYCODE_GENERAL_PURPOSE_COMPILER_ACCEPTANCE_CONTRACT.md` PASS.

ClayCode must be capable of compiling/lowering and executing representative ordinary applications — including a real HTTP/website stack — in addition to FRANK. The project bias is `less change, more compile`: semantics change only when an executable counterexample demonstrates a real language gap.

## APIs and new technology

Every new registered API/capability is considered automatically.

Availability alone does not accelerate the forecast. A row multiplier requires runtime verification plus a benchmark/receipt proving impact.

Equivalent provider speedups do not blindly multiply.

## ETA semantics

ETA is a range, not a promise.

Owner cadence defaults to 10 active collaboration hours/day unless throughput state changes it.

DOOMSDAY uses the dependency/critical path for remaining work. Historical earned work affects lifetime progress; row-specific mapped history/measurements may also reduce remaining work once verified.

If final model training is not yet authorized, DOOMSDAY remains conditional on immediate owner authorization when the frozen training-data gate is ready.

## Required format

```text
RAE STATUS
Entity: JOINED
GitHub: VERIFIED_RW
Canonical: <canonical revision/hash>
Actor: chatgpt-secondary
Trigger: <none|registered trigger>
Research write: <COMMITTED|NO_RESEARCH_DELTA|SYNC_PENDING|NOT_ATTEMPTED>
Short commands: 666 · q12 · dump · fusion · hypofusion · clay · gwt · frank · emergenz · claycode · hyperposition · claygraph · unifieddb · harness

NEXT LEVEL
Stage: <dynamic stage label>
Progress: [#####...............] 25%
ETA @ 10h/day: <low> - <high>
ETA confidence: <confidence> (<basis>)

DOOMSDAY / Clay 0.1 - Chief Developer First Test
Progress: [###############.....] 73%
Historical calibration band: <low>% - <high>% (temporary until Level 0 mapping completes)
Forecast: <YYYY-MM-DD> - <YYYY-MM-DD>
Center: <YYYY-MM-DD>
Confidence: <confidence>
Conditional on immediate training authorization when data is ready: <yes|no>
Forecast basis: <N>-row dynamic remaining critical path + historical earned work + live capabilities/APIs
```

The historical calibration line is shown only while the mapping is still calibrating.

## Allowed status values

- Entity: `JOINED | DEGRADED_UNJOINED | LOCAL_ONLY`
- GitHub: `VERIFIED_RW | VERIFIED_RO | UNVERIFIED | FAILED`
- Research write: `COMMITTED | NO_RESEARCH_DELTA | SYNC_PENDING | NOT_ATTEMPTED`

## Verification semantics

`GitHub: VERIFIED_RW` only when the session actually read expected repo/canonical state and verified write capability or performed a successful write/reread.

## Trigger behavior

Every registered trigger uses the same two-horizon footer.

Exact `666` while Level 0 is open additionally reports detailed assimilation/SLA/earned-work status before the final footer.

After Level-0 PASS, `666` becomes stochastic emergent research-field genesis; DOOMSDAY remains the shared long-range attractor.

## Q12 behavior

Q12 understands NEXT LEVEL, historical earned work and DOOMSDAY separately. It should explain large date/progress changes by showing the underlying evidence, new dependency, accelerator, capacity shift or earned-work remapping.

## Pre-send invariant

Before every substantive response verify:

1. one final fenced `text` block exists;
2. all required metadata and registered short commands are present;
3. NEXT LEVEL lines match `tools/program_progress.py`;
4. visible DOOMSDAY lines match the same resolver including earned-work overlay;
5. any historical calibration band is clearly labeled temporary;
6. no stale fixed DOOMSDAY date is copied from an older response;
7. no prompt-completion percentage is shown;
8. no forbidden frame characters occur;
9. closing fence is final visible content.
