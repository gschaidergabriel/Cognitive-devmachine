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

Required output is a table plus derived range:

| Workstream | Current evidence/progress | Dependency | Capacity basis | Remaining effort | Acceleration/change | Forecast confidence |

The date/range is a conclusion of the table, not an input.

## 2. Required critical-path workstreams

At minimum every forecast evaluates these rows:

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

Rows may be split/merged when evidence shows the work structure changed. New necessary rows must be added. Proven-obsolete rows must be retired with a receipt rather than silently deleted.

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
- `research_entity/forecast/DOOMSDAY_EVENTS.jsonl` for verified shocks/accelerators/blockers.

## 4. Remaining-effort derivation

For each row, derive a low/high remaining-effort estimate.

Priority order:

1. **measured same-row throughput** from completed work/receipts;
2. **measured analogous project throughput**;
3. **current-stage calibrated ETA**;
4. **explicit engineering prior** from `DOOMSDAY_FORECAST_MODEL.json`.

Never prefer an old prior over a newer measured rate.

For a row with a progress fraction `p` and prior/calibrated effort band `[L,H]`:

`remaining_low = L * (1-p) * capacity_factor * verified_change_factor`

`remaining_high = H * (1-p) * capacity_factor * verified_change_factor * uncertainty_factor`

When direct measured remaining effort exists, it replaces this formula.

## 5. Verified jumps / new technology

The model explicitly supports discontinuous progress.

Examples:

- a new compiler eliminates a lowering stage;
- a better model needs much less fine-tuning;
- a Clay primitive collapses multiple architecture modules cleanly;
- a new inference/runtime engine makes the binary deployment trivial;
- a stronger external training system accelerates model tuning;
- a discovered bug reveals that an apparently complete row needs major rework.

A jump changes the forecast only when recorded as a `DOOMSDAY_EVENT` with:

- event id/date;
- affected rows;
- type: `ACCELERATOR | ELIMINATION | BLOCKER | REWORK | CAPACITY_CHANGE | NEW_DEPENDENCY`;
- evidence/receipt refs;
- old assumption;
- new assumption;
- multiplier or eliminated work;
- confidence;
- reversibility/expiry if applicable.

Examples:

`verified compiler shortcut -> H3 factor 0.55`

`new model natively understands Clay eval suite -> FINAL_MODEL_FINE_TUNE factor 0.45`

`UnifiedDB migration reveals semantic mismatch -> UDB factor 1.6`

No hype-based multiplier is allowed.

## 6. Capacity model

Capacity is time-dependent.

Read `CAPACITY_STATE.json` on every forecast.

Rules:

- only `available_now` resources count as current execution capacity;
- expected future resources may constrain an **earliest possible future date**, but do not count as current throughput until verified ACTIVE;
- temporarily unavailable AI workers do not contribute current parallel throughput;
- future capacity events may be shown as forecast assumptions with reduced confidence;
- effective parallelism comes from actually completed independent work, never raw worker count.

The current owner work cadence defaults to `10 active collaboration hours/day` unless `PROGRAM_THROUGHPUT.json` changes it.

## 7. Dependency / critical-path model

Do not blindly sum every row.

Each row declares dependencies and whether work may overlap.

Compute earliest finish using a precedence graph:

`row_start = max(forecast_epoch, finish(dependencies), required_capacity_available_date)`

`row_finish = row_start + remaining_duration`

Independent preparatory work may overlap.

The DOOMSDAY range is the earliest/latest forecast finish of `CLAY_0_1_ACCEPTANCE_RUN` through this dependency graph.

This means parallel research can shorten the calendar without pretending it reduces the intrinsic work of a row.

## 8. Owner training gate

The current program intentionally stops after training-data freeze and waits for explicit owner authorization before paid/final training.

For date forecasting only, `OWNER_TRAINING_RELEASE_GATE` has two modes:

- if authorization exists: actual authorization timestamp;
- if not: forecast is **conditional on immediate authorization when DATA is ready** and must say so.

Unknown human waiting time must never be silently guessed into the date.

## 9. Fine-tuning method neutrality

Clay 0.1 requires the final validated fully fine-tuned model, but the forecast does not permanently hardcode LoRA as the only method.

The active training plan may become:

- LoRA/QLoRA;
- adapter + merge;
- staged fine-tuning;
- full-parameter fine-tuning;
- distillation plus tuning;
- a newer method that appears later.

The chosen method must pass the frozen Clay 0.1 eval contract. A new method may accelerate DOOMSDAY if validated.

## 10. Dynamic DOOMSDAY progress percentage

The DOOMSDAY bar is not a simple count of stages.

It is recomputed from the **current forecast effort table**:

`forecast_progress = 1 - remaining_expected_work / current_total_expected_work_scope`

Where completed work is retained as historical effort and eliminated future work reduces the denominator only with a verified elimination event.

Because scope knowledge can change, this percentage is allowed to move backward when a new necessary dependency is discovered. That is a feature, not a bug.

Always label it as a forecast/project completion measure, while `NEXT LEVEL` remains the stricter gate progress.

## 11. Forecast outputs

Every substantive project status may show the compact result:

`DOOMSDAY / Clay 0.1`
`Progress: [........] N%`
`Forecast: YYYY-MM-DD – YYYY-MM-DD`
`P50/center: YYYY-MM-DD`
`Confidence: LOW/MEDIUM/HIGH`
`Conditional: <e.g. owner authorizes final training immediately when corpus gate passes>`

Exact `q12` should be able to expand this into the underlying table on request or when a major change moved the date materially.

## 12. Recalculation triggers

Recompute whenever any of these changes:

- stage/work-package progress;
- completed archive obligations;
- measured throughput;
- worker availability;
- hardware availability;
- model/training benchmark;
- architecture change;
- new dependency;
- accelerator/blocker event;
- owner authorization;
- failed acceptance test;
- new external technology selected for use.

In practice the status resolver recalculates every time it is run, so no manual refresh is required.

## 13. Epistemic rule

DOOMSDAY is a forecast, not a promise.

The point of the model is to become **more accurate as the project learns**, including when learning produces sudden jumps.
