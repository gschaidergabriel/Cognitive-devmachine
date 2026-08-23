# GO/ZERO FREE_ONLY swarm trigger contract — ClayVerse

Status: **CURRENT / FAIL-CLOSED UNTIL CLAYVERSE CONTROLLER ADMISSION**
Date: 2026-08-23
Current product authority: `research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md`
Current control: `4.1 + 4.2 + historical 4.3 + 4.4-clayverse-product-authority-addendum`
Macrocycle identity: `research_entity/continuity/GO_MACROCYCLE_IDENTITY_CONTRACT.md`

## Current admission state

Provider swarm execution for `go` / `zero` is **BLOCKED** until a controller is source-admitted that binds the current ClayVerse product/program authority before secret lookup or network I/O.

The historical base controller `tools/run_free_go_swarm.py` is **LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED** because its source currently:

- hard-codes the Mini Entity approximately-1B training directive as `OWNER_DIRECTIVE_PATH`;
- injects Mini Entity role/task language;
- expects the Mini Entity worker-protocol marker;
- therefore can recreate product-authority drift even when Bootstrap/PROGRAM_STATE/Control 4.4 select ClayVerse.

The previously named implementation `tools/run_go_zero_swarm.py` is not admitted by this contract unless the exact file exists and passes the current ClayVerse authority guard. A missing implementation is BLOCKED, never silently substituted with the legacy Mini Entity controller.

## Required ClayVerse controller contract

Before any provider key lookup or provider network call, the admitted controller MUST fail closed unless all of the following agree:

- `BOOTSTRAP_MINIMAL.active_program == CLAYVERSE_SINGLE_CONTAINER`;
- `BOOTSTRAP_MINIMAL.active_stage == CLAYVERSE_ARTIFACT`;
- `PROGRAM_STATE.program_id == clayverse-single-container`;
- current owner directive is `CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md`;
- effective control includes `4.4-clayverse-product-authority-addendum`;
- FREE_ONLY is active;
- Together is forbidden;
- VPS/self-hosted/production-host testing remains forbidden;
- exact runtime credit still requires admitted isolated execution;
- worker prompts preserve Clay as the persistent research entity and workers as temporary organs;
- worker prompts describe ClayVerse, not Mini Entity/Blogpost, as the current product;
- one shared `macrocycle_id` and one unusual-experiment lease law are preserved across children.

## Trigger law

Every explicit user `go` or `zero` remains eligible for maximum useful FREE_ONLY research/build concurrency **only when an admitted controller and admitted free credentials are actually available**.

If either is unavailable, record the blocker and continue all non-provider work possible in the current turn. Do not fabricate a running swarm and do not fall back to a stale product controller.

`go` and `zero` are parent triggers. Any future admitted API/model child receives child `go`, the current ClayVerse owner/product context, and the mandatory GRF/ClayCode worker protocol at the top of its prompt. A child never creates a new persistent Clay identity or a second user-triggered macrocycle.

## Provider safety law

When a ClayVerse controller is later admitted:

- FREE_ONLY must be verified before secret/key lookup and before network I/O;
- no paid fallback, quota purchase, subscription upgrade, or automatic billing escalation;
- HTTP 402 is hard stop;
- HTTP 429 is provider-wide cooldown/backoff, never key rotation to evade a shared limit;
- credentials remain environment/vault-only and never enter prompts, receipts, peer state, or source;
- absent quota metadata is UNKNOWN, not unlimited entitlement.

## Coordination law

Any admitted swarm uses one cross-process coordination state and atomically leases non-overlapping research lanes. Each lease binds at least macrocycle id, parent trigger, child trigger, provider/model/key fingerprint, lane/task, worker serial, expiry/heartbeat, and reserved output-token demand.

Before each call the child receives bounded peer state plus current repository/program/control/owner context. Model agreement remains candidate evidence only and never becomes canonical truth.

## Product boundary

Swarm is research/build orchestration only. Product runtime remains **one persistent central ClayVerse entity**. A swarm may not create a second durable identity, UnifiedDB alternative, truth authority, EffectGate bypass, recovery ledger, or consciousness daemon.

## Re-admission gate

Unblock provider swarm execution only after a ClayVerse controller exists and a deterministic source gate demonstrates at minimum:

1. current ClayVerse authority accepted;
2. Mini Entity product authority rejected;
3. Control 4.4 required;
4. FREE_ONLY weakening rejected before key lookup;
5. stale/missing macrocycle identity rejected;
6. worker prompt begins with current ClayVerse/GRF/ClayCode context;
7. no secret value appears in generated prompt/receipt state.

Passing this source gate still gives **ZERO provider/model/whole-product runtime credit** until actual admitted execution occurs.
