# ClayCode Trigger Run — Epoch-Coherent Loop Runtime Delta

Run: `claycode-20260809T1648p0700-loop-runtime`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` — IN_PROGRESS  
Promotion: **NONE**  
Gate advancement: **NONE**

## Result

The new FRANK loop-of-loops hypothesis does not currently justify a FRANK-specific ClayCode loop organ or syntax family. A concurrent ClayCode run independently reached the stronger generic-control result with a parser/canonical-IR/lowering/interpreter proxy: 2,000 randomized nested-loop differential cases, 0 mismatches and 4/4 negative cases rejected.

This run adds a separate executable compiler/runtime discriminator:

1. **Scheduling semantics must be explicit.** For a coupled loop family declared semantically unordered/set-like at one epoch, every member must read an equivalent prior-epoch snapshot (or another formally equivalent deterministic barrier). All tested loop-spec permutations produced equivalent state under snapshot lowering. An in-place-read mutation produced schedule-order dependence.
2. **Budget exhaustion is not convergence.** The test exhausted all loop budgets and reached `state_delta=0.0` while residual pressure/error remained `0.5690308937228293`. The correct typed result was `STALLED -> ESCALATE`, not successful `HALT`.
3. **Authority remains external.** Forged capability names/readout values were rejected; only a valid capability could commit the representative effect.
4. **No core semantic redesign is warranted.** These findings belong primarily in generic structured-control, scheduler/lowering, halt-reason and receipt contracts.

## Internal grounding

Current G9 already has `Delta`, epochs, capability-bearing effects, GraphDelta, GWT delivery/use/effect/reentry distinctions, search budgets and a top-level `cycle(...)`. ClayGraph already has graph/source epochs, cycle IDs, activation events, hyperrelations and separate projection/selection/receiver receipts. UnifiedDB already has cycle-aware answer capsules, capability sources, pressures, coalitions and stack receipts. Therefore the new evidence favors compiler/runtime realization over a second loop-state model.

The current BASE acceptance law remains `less change, more compile`: semantic changes require an executable counterexample showing existing semantics cannot express/lower the needed behavior.

## External triangulation

Primary recurrent-depth research supports adaptive recurrence as a computation-allocation mechanism but also reports overthinking/stability failure at excessive recurrence. Mechanistic/fixed-point work supports measuring recurrent dynamics without implying that all useful systems converge to one fixed point. Independent HRM ablation evidence further warns against attributing gains to a proposed hierarchy when an outer refinement loop can explain most of the observed effect.

This evidence supports explicit budgets, continuation/exit reasons and dynamics observability. It does not establish FRANK equivalence to a looped Transformer and does not justify neuro-inspired syntax.

## Executable experiment

Experiment: `EXP-CC-LOOP-RUNTIME-20260809-01`  
Candidate: `CC-G9-loop-runtime-library-v0.2`  
Lowering target: local Python host-runtime probe  
Evidence class: local executable mechanism proxy, not live FRANK runtime evidence.

Observed:
- snapshot permutation equivalence: PASS;
- in-place mutation schedule dependence: DETECTED;
- seeded fuzz cases: 250 PASS for budget/halt invariants;
- productive bounded cycle discriminator: PASS;
- divergence/rollback discriminator: PASS (rollback at probe step 5);
- forged authority: REJECTED;
- valid effect capability: EXECUTED;
- terminal fixed-proxy state: `STALLED`;
- terminal delta: `0.0`;
- residual pressure/error: `0.5690308937228293`;
- exhausted-budget action: `ESCALATE`.

The exact executed-driver hash and generated-code hash are recorded in `EXECUTABLE_RESEARCH_RECEIPT.json`. A compact reproduction is checked into `experiments/CC_LOOP_RUNTIME_LAB_V02.py` and is explicitly marked as not hash-identical to the full executed driver.

## Hypotheses / negative results

- `H-CC-LOOP-001`: generic structured recurrence is sufficient for current tested FRANK requirements — OPEN_SUPPORTED_NOT_PROMOTED.
- `H-CC-LOOP-002`: unordered/set-like coupled loops require deterministic epoch/order semantics — OPEN_SUPPORTED_NOT_PROMOTED.
- `H-CC-LOOP-003`: budget exhaustion must be distinct from semantic completion — OPEN_SUPPORTED_NOT_PROMOTED.
- `H-CC-LOOP-004`: adaptive budgets outperform fixed budgets on selected FRANK loops — OPEN_UNTESTED_ON_FRANK.

Negative results:
- in-place set-like lowering can create accidental schedule-order semantics;
- zero delta after exhausted budget can still be a stalled high-residual state;
- no executable evidence currently requires a FRANK-specific loop primitive.

## Goodman anti-echo result

FRANK/ClayCode branch restatements of the loop-of-loops hypothesis were collapsed into one ancestry family. Current executable discriminators and independent external sources were used as separate evidence. The result is a refinement, not circular promotion:

`FRANK loop-of-loops -> generic structured recurrence + explicit scheduling class + typed halt reasons + receipts`

not

`FRANK loop-of-loops -> new FRANK-specific ClayCode organ`.

The repo-local Goodman validator could not be executed because the local execution sandbox had no repository checkout/network access. Official validator PASS is not claimed.

## Cross-branch feedback

- FRANK/Harness: H1 should compare snapshot/set-like, explicit sequential and event-driven/asynchronous lowering on frozen traces and preserve budget-exhausted/high-residual as STALLED/ESCALATE.
- ClayGraph: no schema promotion; scheduling class/order is provenance/semantic contract, never accidental graph iteration order.
- UnifiedDB: persist epoch, scheduling contract, budget exit reason and replay receipt in the existing logical plane; no physical merge implication.
- GWT: continuation/halt is not broadcast/use/effect/reentry authority.
- Hyperposition: no change; preserved alternatives must survive loop routing.
- Emergenz: recurrence/stability/order determinism are observability/control axes, not emergence proof.
- ClayCode: implement production generic structured control plus explicit snapshot/set-like vs ordered/sequential/asynchronous scheduling semantics and translation validation.

## Required artifacts

Written for this run:
- `INTERCONNECT_MANIFEST.json`;
- `TOOL_EXECUTION_MANIFEST.json`;
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`;
- `EXECUTABLE_RESEARCH_RECEIPT.json`;
- `HYPOTHESES.json` including negative results;
- `BRANCH_FEEDBACK_MANIFEST.json`;
- `experiments/CC_LOOP_RUNTIME_LAB_V02.py` compact reproduction;
- `FINAL_REPORT.md`;
- micro-packet `KMP-CLAYCODE-EPOCH-SNAPSHOT-LOOP-SCHEDULING-20260809.md`.

## Completion boundary

Completed: current GitHub boot, trigger routing, current FRANK/ClayCode/ClayGraph/UnifiedDB/GWT grounding, independent external triangulation, executable scheduler/budget/authority discriminator, Goodman review, hypotheses/negative results, mesh feedback and durable GitHub write-back.

Not completed and not claimed: authoritative repo-local interconnect-preflight PASS, repo-local Goodman-validator PASS, E2B evidence, production G9 compiler change, H1 live FRANK replay, Qwen-4B test, any BASE work-package PASS, BASE gate PASS or canonical scientific promotion.

## Highest-information next implementation step

Implement the smallest production generic structured-control/scheduling layer required by BASE:
- typed branch + bounded loop/control op;
- loop-carried values;
- explicit scheduling class (`SNAPSHOT_SET`, `SEQUENTIAL_ORDERED`, `ASYNC_EVENT` or validated equivalents);
- explicit exit/halt reason including `BUDGET_EXHAUSTED`, `CONVERGED`, `STALLED`, `DIVERGED`, `CANCELLED`, `ERROR`;
- effectful-body permit revalidation;
- independent interpreter/oracle translation validation;
- then frozen H1/H2 differential replay.
