# DOOMSDAY Dynamic Forecast Protocol — Clay 0.1

**Status:** PROJECT_OWNER_FIXED_FORECAST_METHOD
**Target:** `Clay 0.1`
**Display name:** `DOOMSDAY` (internal joke)

## 0. Target definition

DOOMSDAY is the first successful end-to-end run on project-controlled hardware of:

`Clay-programmed FRANK architecture`
`+ one-module/binary distilled runtime`
`+ UnifiedDB`
`+ fully fine-tuned final Clay-native model`
`+ reproducible local/project-hardware boot`
`= Clay 0.1`

A Reference Harness, a Clay Harness, a binary without the final model, or a fine-tuned model without the integrated binary/UnifiedDB runtime is **not** DOOMSDAY.

## 1. No fixed DOOMSDAY date

The repository must never store one authoritative fixed DOOMSDAY date.

Every status calculation recomputes the forecast from current evidence.

Required underlying form is a critical-path table:

| Workstream | Current evidence/progress | Dependency | Capacity basis | Remaining effort | Acceleration/change | Forecast confidence |

The date/range is a conclusion of the table, not an input.

## 2. Required critical-path workstreams

At minimum every forecast evaluates:

1. `L0_ARCHIVE_ASSIMILATION`
2. `BASE_CLAYCODE_RELEASE`
3. `H1_REFERENCE_HARNESS`
4. `H2_CLAYCODE_HARNESS`
5. `H3_ONE_MODULE_BINARY_FRANK`
6. `UDB_UNIFIED_DATABASE`
7. `DATA_FINAL_TRAINING_CORPUS`
8. `OWNER_TRAINING_RELEASE_GATE`
9. `FINAL_MODEL_FINE_TUNE`
10. `MODEL_EXPORT_RUNTIME_PACKAGE`
11. `CLAY_0_1_FULL_INTEGRATION`
12. `PROJECT_HARDWARE_DEPLOYMENT`
13. `CLAY_0_1_ACCEPTANCE_RUN`

Rows may be split/merged when evidence shows the real work structure changed. New necessary rows must be added. Proven-obsolete rows are retired with a receipt rather than silently deleted.

Canonical row model:

`research_entity/forecast/DOOMSDAY_FORECAST_MODEL.json`

## 3. Dynamic evidence inputs

The forecast reads current state from:

- `research_entity/rooms/PROGRAM_STATE.json`;
- exact stage workspaces/release manifests;
- `research_entity/archive_assimilation/666_WORKSPACE.json`;
- `research_entity/rooms/PROGRAM_THROUGHPUT.json`;
- `research_entity/rooms/CAPACITY_STATE.json`;
- Harness/ClayCode/UnifiedDB workspaces and test receipts;
- training-data workspace when created;
- actual fine-tuning job receipts after owner authorization;
- actual model export/inference benchmarks;
- actual project-hardware validation receipts;
- `research_entity/forecast/DOOMSDAY_EVENTS.jsonl` for verified shocks/accelerators/blockers;
- `research_entity/global/EXTERNAL_RESEARCH_TOOL_REGISTRY.json`;
- every `research_entity/global/*_RESEARCH_CAPABILITY.json` extension;
- `research_entity/forecast/DOOMSDAY_CAPABILITY_RULES.json`.

## 4. Remaining-effort derivation

For each row derive a low/high remaining-effort estimate.

Priority order:

1. measured same-row throughput from completed work/receipts;
2. measured analogous project throughput;
3. current-stage calibrated ETA;
4. explicit engineering prior from `DOOMSDAY_FORECAST_MODEL.json`.

Never prefer an old prior over a newer measured rate.

A row's remaining effort may be changed by a verified event or a verified capability benchmark. Unverified claims never change the date.

## 5. APIs / tools are dynamic forecast inputs

Every forecast automatically scans the external tool registry plus all capability-extension files.

This is deliberately future-proof: a newly added API/tool does not require manual hardcoding into the forecast engine merely to appear in the capability table.

Each capability is classified as one of:

- `ACTIVE_CALIBRATED` — runtime verified and has a verified DOOMSDAY impact benchmark;
- `ACTIVE_UNCALIBRATED` — runtime verified and relevant, but no trustworthy time multiplier yet;
- `POTENTIAL_UNVERIFIED` — relevant but not runtime verified;
- `NO_DIRECT_PATH_IMPACT` — currently no plausible critical-path relationship.

### Availability is not acceleration

A new API counts immediately in the table, but does **not** automatically move DOOMSDAY earlier.

A capability changes ETA only when:

1. its runtime status is verified;
2. the affected DOOMSDAY row(s) are explicit;
3. a benchmark/receipt is attached;
4. the multiplier is mechanically valid;
5. the effect is not double-counted with equivalent providers.

Default same-row provider rule:

> Choose the strongest single verified capability multiplier. Do not blindly multiply several API accelerators together.

A combined multiplier is allowed only if a later joint benchmark explicitly measures the combined stack.

This prevents provider proliferation from creating fictional exponential speedups.

### Existing Together capability

Together AI is registered as a relevant future model-training/inference capability. It counts in the capability table immediately, but remains forecast-neutral until runtime/training behavior is actually verified and benchmarked. Paid/final training remains blocked until explicit owner authorization.

## 6. Verified jumps / new technology

The model explicitly supports discontinuous progress.

Examples:

- a new compiler eliminates a lowering stage;
- a better model needs much less fine-tuning;
- a Clay primitive collapses multiple architecture modules cleanly;
- a new inference/runtime engine makes binary deployment simpler;
- a stronger external training system accelerates model tuning;
- a discovered bug reveals that apparently complete work needs rework.

A non-capability jump changes the forecast only through a verified `DOOMSDAY_EVENT` containing:

- event id/date;
- affected rows;
- type `ACCELERATOR | ELIMINATION | BLOCKER | REWORK | CAPACITY_CHANGE | NEW_DEPENDENCY`;
- evidence/receipt refs;
- old assumption;
- new assumption;
- multiplier or eliminated work;
- confidence.

Examples:

`verified compiler shortcut -> H3 factor 0.55`

`new model natively understands Clay eval suite -> FINAL_MODEL_FINE_TUNE factor 0.45`

`UnifiedDB semantic mismatch -> UDB factor 1.6`

No hype-based multiplier is allowed.

## 7. Capacity model

Capacity is time-dependent and is read from `CAPACITY_STATE.json` every time.

Rules:

- only `available_now` resources count as current execution capacity;
- future hardware does not count as active before verification;
- dated expected hardware may constrain the conservative/high forecast bound as a fallback;
- temporarily unavailable AI workers do not contribute current parallel throughput;
- effective parallelism comes from completed independent work, never raw worker count;
- the owner cadence defaults to 10 active collaboration hours/day unless throughput state changes it.

The hardware parser uses dates attached to hardware entries rather than confusing unrelated events such as an AI-worker quota reset with the expected GPU-server date.

## 8. Dependency / critical-path model

Do not blindly sum every row.

Each row declares dependencies. Compute earliest finish through the precedence graph:

`row_start = max(forecast_epoch, finish(dependencies), required_capacity_available_date)`

`row_finish = row_start + remaining_duration`

Independent preparatory work may overlap. Dependency cycles are invalid and make the forecast fail closed.

The DOOMSDAY range is the low/high finish of `CLAY_0_1_ACCEPTANCE_RUN`.

## 9. Owner training gate

The current program intentionally stops after training-data freeze and waits for explicit owner authorization before final/paid training.

For forecasting only:

- if authorization exists, use the actual authorization state/time;
- if not, the forecast is explicitly conditional on immediate authorization when DATA becomes ready.

Unknown human waiting time is never guessed.

## 10. Fine-tuning method neutrality

Clay 0.1 requires the final validated fully fine-tuned model, but the forecast does not hardcode LoRA as the only future method.

The selected method may become LoRA/QLoRA, merged adapter, staged tuning, full-parameter tuning, distillation plus tuning, or a future method. A newer method may accelerate DOOMSDAY when its actual benchmark demonstrates the impact.

## 11. Dynamic DOOMSDAY progress percentage

The DOOMSDAY bar is an effort-weighted dynamic project forecast, not a simple stage count:

`progress = completed_expected_effort / current_expected_scope`

Verified eliminations reduce future scope. New required dependencies can increase scope and therefore move the percentage backward. That is scientifically correct behavior.

NEXT LEVEL remains the stricter local gate progress and is displayed separately.

## 12. Forecast outputs

Compact status output:

`DOOMSDAY / Clay 0.1`
`Progress: [........] N%`
`Forecast: YYYY-MM-DD - YYYY-MM-DD`
`Center: YYYY-MM-DD`
`Confidence: ...`
`Conditional on immediate training authorization when data is ready: yes|no`
`Forecast basis: N-row dynamic critical path + live capabilities/APIs`

Q12 can expand the same resolver result into the full workstream/capability table when useful.

## 13. Mandatory regression tests

Forecast changes must be tested against scenarios including at least:

- normal baseline;
- partial stage progress;
- verified accelerator;
- unverified accelerator rejection;
- verified blocker/rework;
- new API discovered automatically;
- runtime-verified but uncalibrated API does not alter ETA;
- unverified API cannot alter ETA even with a fake impact object;
- calibrated API shortens the correct workstream;
- multiple APIs do not blindly multiply;
- capability-extension status overrides stale registry metadata;
- future hardware date is parsed from the hardware entry rather than an unrelated capacity date;
- owner authorization conditional toggles correctly;
- completed future workspace advances progress;
- verified elimination shortens scope;
- measured throughput outranks prior;
- irrelevant API has no path effect;
- new dependency can increase ETA / lower progress;
- dependency cycle fails closed;
- malformed forecast event does not silently affect the date.

Canonical test tool:

`tools/test_doomsday_forecast.py`

A future forecast-engine change is not accepted solely because it produces a date. It must preserve these invariants or explicitly update the contract with evidence.

## 14. Recalculation triggers

Recompute whenever any of these changes:

- stage/work-package progress;
- completed archive obligations;
- measured throughput;
- worker availability;
- hardware availability;
- API/tool registry or capability file;
- provider runtime verification;
- model/training benchmark;
- architecture change;
- new dependency;
- accelerator/blocker event;
- owner authorization;
- failed acceptance test;
- newly selected external technology.

The status resolver recalculates every time it runs; no manual refresh is required.

## 15. Epistemic rule

DOOMSDAY is a forecast, not a promise.

Its purpose is to become more accurate as the project learns — including when learning produces sudden jumps forward or backward.
