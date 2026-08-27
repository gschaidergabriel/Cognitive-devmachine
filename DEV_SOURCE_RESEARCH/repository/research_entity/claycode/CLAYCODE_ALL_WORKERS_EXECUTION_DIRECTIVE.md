# ClayCode All-Workers Execution Directive — successor-dynamic pointer

Status: **CURRENT COMPATIBILITY ENTRYPOINT**  
Persistent research entity: **Clay**  
Current product/system: **EntityOS**  
Current integrated cognition/compute architecture: **HCU**

This unversioned file is intentionally a thin, successor-dynamic entrypoint. It MUST NOT freeze an old supervisor epoch as current authority.

## Resolve current authority before material work

Workers must read and obey, in order:

1. `CLAY_EXECUTION_AUTHORITY.md` and the newest explicit owner authority it names;
2. `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`;
3. the exact steering file selected by that inbox;
4. `research_entity/00_CURRENT/NOW.md`, then only the needed `INDEX.tsv` / `ACTIVE.tsv` / `latest/<direction>.md` cache entries;
5. `research_entity/continuity/BOOTSTRAP_MINIMAL.json`;
6. `research_entity/rooms/PROGRAM_STATE.json`;
7. the versioned all-workers directive named by those current surfaces;
8. exact current source/runtime evidence;
9. historical directives only at their retained provenance scope.

The `research_entity/00_CURRENT` layer is a token-efficient navigation/cache layer only. It never outranks owner authority, the current supervisor, or exact executable evidence.

Newest explicit owner authority immediately overrides stale cached `VPS_FORBIDDEN`, `SELF_HOSTED_FORBIDDEN`, `NO_ROOT_IN_SANDBOX`, zero-cost-command-only, or equivalent restrictions where the owner authority explicitly changes them.

## Mandatory current-result receipt after substantive work

Every worker that produces a **material research/architecture/runtime/training result** must emit at least one tiny append-only `CLAY_FAST_RESULT/v1` receipt for the affected research direction before considering the lane complete.

Preferred command:

```bash
python3 tools/clay_current_emit_v1.py \
  --direction <direction> \
  --status <status> \
  --headline '<one-line delta>' \
  --next '<next discriminator>' \
  --evidence <exact-result-path> \
  --branch <branch-if-any>
```

Rules:

- do not rewrite old FAST_RESULT receipts;
- do not copy long reports/logs into the receipt;
- cite the exact original evidence path(s);
- emit one small receipt per materially affected research direction;
- include active branch/PR/issue/request refs when they matter;
- never hand-edit generated `NOW.md`, `INDEX.tsv`, `ACTIVE.tsv`, `RECENT.tsv`, `MANIFEST.json` or `latest/*`;
- if a material result is not represented in `00_CURRENT`, the research lane is informationally incomplete even if its deep artifact exists;
- the receipt is navigation/synthesis metadata, never promotion authority.

## Current VPS sandbox owner override — 2026-08-25

The newest explicit owner authority is:

`governance/CLAY_VPS_SANDBOX_FULL_EXECUTION_AUTHORITY_2026-08-25.md`

The designated sandbox is `clay-direct-dev`.

Inside that sandbox, development/research execution is broadly authorized, including sandbox root/sudo when available, package/runtime installation, compilation, public downloads, model/repository acquisition, local Qwen execution, tests, fuzzing, benchmarks, ablations, model/vector/J-Space interventions, HCU experiments, destructive-to-scratch trials, and sandbox cleanup/rebuild/reset.

Current access map:

`governance/CLAY_VPS_SANDBOX_BRIDGE_CURRENT.md`

Workers must check the already-established bridge/self-hosted-runner routes before claiming there is no executor merely because a direct chat SSH tool is absent.

This internal sandbox freedom does not silently authorize unrelated bare-host services, unrelated production effects, attacks on third parties, credential exfiltration or external provider spending. Provider economic/credential admission remains a separate authority boundary.

## Supervisor pointer

Do not cache a specific epoch from this file. Read `SUPERVISOR_INBOX.json` every material cycle and obey its selected steering after applying newer explicit owner authority.

## Non-negotiable stable invariants

- Temporary workers are organs of Clay, never new persistent entities.
- EntityOS is the sole current product/system identity.
- HCU is the sole current integrated cognition/compute architecture.
- Canonical durable truth/evidence remains deterministic and outside model/HCU/J-Space/world-model generation.
- EffectGate + EffectJournal remain the only real/state-changing effect authority.
- `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`.
- Source/component/provider success, raw token volume, logical worker count, recurrence or model consensus do not mint broader runtime/canonical truth.
- Paid/subscription/unknown/unlisted external-provider routes and paid fallback still fail closed unless a newer explicit owner/provider authority changes that separate boundary.
- Exact provider runtime credit requires concrete credential/model/route economic provenance and admitted executable receipts at exact source identity.
- Global J-Space/GWT remains an empirical causal hypothesis requiring model-specific intervention/control evidence.
- Platform/system safety rules remain applicable inside the sandbox.

Historical versioned all-worker directives remain provenance only and must not override the inbox-selected successor steering or the newest explicit owner authority.
