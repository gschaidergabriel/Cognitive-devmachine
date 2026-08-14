# GO WP02 measurement-hardening delta

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay research worker; NOT Frank.  
Canonical parent: `RAE-8.8 / r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffähig auf Andreas PC` under the registered Ubuntu target contract.

## Durable delta

Commit `27e061460db0aa4c477e1d014d15554970f09a3c` updates `tools/claycode_wp02_strict_local_closure_v2.py` without changing V17 grammar or ClayCode semantics.

The closure runner now records, per executed WP02 component:

- monotonic wall duration in nanoseconds/milliseconds using `time.perf_counter_ns()`;
- child user/system CPU deltas from `resource.getrusage(RUSAGE_CHILDREN)`;
- minor/major page-fault deltas;
- block input/output deltas;
- voluntary/involuntary context-switch deltas;
- cumulative terminated-child max-RSS value with explicit scope labelling;
- timeout budget and timeout state;
- stdout/stderr SHA-256 plus bounded tails;
- host kernel/machine/logical-CPU/total-memory metadata in addition to Python/OS/package/repository identity.

Timeouts are now fail-observable instead of escaping before a component row can be materialized.

Primary implementation basis used for this observability change: current Python documentation for `time.perf_counter_ns()` and `resource.getrusage(RUSAGE_CHILDREN)`. No language semantics are inferred from these APIs.

## Evidence status

- GitHub write: VERIFIED; commit `27e061460db0aa4c477e1d014d15554970f09a3c` exists on current main history.
- Selected WP02 grammar remains contract-selected V17.
- The hardened file is already in the path filter of `.github/workflows/claycode-vps-wp02-probe.yml`, so the push is eligible for the existing read-only self-hosted Hostinger execution lane.
- The canonical remote receipt `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json` remained absent (404) on repeated post-change reads in this invocation. This is `MISSING_EVIDENCE`, not a parser failure and not a PASS.
- No physical Andreas target execution is claimed.
- No BASE/WP02/WP06 release promotion is claimed.

## Hypothesis / counterhypothesis

H1: adding process-level timing/resource/timeout telemetry will make the next V17 strict receipt materially more interpretable without changing pass/fail semantics.

Counterhypothesis: the new measurement wrapper introduces a runtime/portability regression in the Ubuntu closure path. The existing self-hosted workflow is the cheapest discriminator; any nonzero/timeout/precondition regression must remain a negative receipt and be repaired before relying on the telemetry.

## OOB accounting

This measurement hardening is NOT a second out-of-the-box experiment. The mandatory bounded OOB slot for the current `go` research cycle is already recorded in `research_entity/reports/20260810T0020p0700_CHATGPT_GO_CLAYCODE_WP02_V17_RECURSIVE_FUSION.md` as the contextual-vs-basic V17 lexer shadow. The separately committed metamorphic trivia probe is a concurrent branch artifact and is not re-counted here.

## Architecture / work consequence

Architecture delta: `NO_CHANGE` to ClayCode semantics and V17 grammar.

Test/observability delta: `SUPPORTED_IMPLEMENTATION_DELTA_PENDING_REMOTE_EXECUTION`.

Next executable frontier remains fail-closed and ordered:

1. consume a persisted read-only Hostinger V17 WP02 strict/OOB receipt bound to exact tested commit and selected grammar SHA;
2. only if clean, replay the latest WP06 deep-expression/call-chain/checked-numeric/string-object/native-C hardening against exact V17/current-main bytes;
3. only after that, execute the registered physical Andreas Ubuntu BASE14 path, ten real applications, five-path FULL_FRANK handoff, recovery/authority checks and independent WP14;
4. preserve all negative results and never use remote VPS evidence as physical-target acceptance.

No paid/final training action was authorized or attempted.
