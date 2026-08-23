# GO/ZERO FREE_ONLY swarm trigger contract

Status: CURRENT OWNER TRIGGER/ORCHESTRATION CONTRACT
Date: 2026-08-23
Implementation: `tools/run_go_zero_swarm.py`
Base provider controller: `tools/run_free_go_swarm.py`
GRF/ClayCode worker protocol: `research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md`
Macrocycle identity: `research_entity/continuity/GO_MACROCYCLE_IDENTITY_CONTRACT.md`

## Trigger law

Every explicit user `go` or `zero` is eligible to start the maximum useful FREE_ONLY research/build swarm during that work cycle whenever an execution surface carrying admitted free provider credentials is actually available.

`go` and `zero` are parent triggers. Every API/model child spawned by the swarm receives a child `go` task plus the mandatory GRF/ClayCode protocol at the top of its prompt.

A child `go` is NOT a new user-triggered macrocycle. The parent orchestration boundary mints or receives one `macrocycle_id` and propagates the exact same value to every child. Child workers do not invent another macrocycle id and do not independently consume the one-unusual-experiment slot.

## Maximum-use law

Within current FREE_ONLY authority, use as much admitted free provider capacity as possible while preserving provider rules and coordination:

- use all admitted Groq, Mistral and NVIDIA/Nemotron keys actually exposed to the runtime;
- start up to the configured concurrency cap per provider and adapt from live outcomes;
- successful calls may keep/ramp concurrency high;
- HTTP 429 causes provider-wide cooldown/backoff and reduced concurrency; do not rotate keys to evade an organization/provider rate limit;
- HTTP 402 is a hard stop for that key/provider path for the current run;
- auth/entitlement failure is not runtime evidence and disables the affected key/path;
- never create paid capacity, paid fallback, quota purchases or subscription upgrades under FREE_ONLY;
- secrets remain environment/vault-only and never enter receipts, peer state, prompts or source control.

## Token and request observation

Before every spawn attempt the coordinator observes the shared rolling provider telemetry from completed calls:

- total tokens and request count over the previous 60 seconds;
- total tokens and request count over the previous 24 hours;
- provider response rate-limit headers when returned;
- provider-wide cooldown state;
- active reserved output-token demand.

Optional explicit caps may be supplied by environment variables:

- `CLAY_GROQ_TPM_BUDGET`, `CLAY_GROQ_TPD_BUDGET`, `CLAY_GROQ_RPM_BUDGET`, `CLAY_GROQ_RPD_BUDGET`;
- equivalent `CLAY_MISTRAL_*` and `CLAY_NVIDIA_*` variables.

An absent configured cap is UNKNOWN, not unlimited entitlement. In that case live provider responses remain authoritative and 429 must cool down rather than trigger quota-evasion behavior.

## Worker collision avoidance

Workers share one cross-process coordination state. Before a model call the controller atomically leases one research lane. A lane cannot be owned by two live workers at once.

Each lease contains at least:

- `macrocycle_id`;
- parent trigger (`go` or `zero`);
- child trigger (`go`);
- provider/model/key fingerprint;
- lane and task;
- worker serial;
- start/expiry/heartbeat;
- reserved output-token count.

Leases use a host file lock and atomic state replacement. Heartbeats extend live leases; expired leases are pruned.

Before every call, the child prompt receives:

- current active peer leases;
- a bounded window of recent completed worker results;
- rolling token/request observations;
- current repository/program/supervisor/owner context;
- its own lane lease and shared macrocycle identity.

Workers MUST inspect peer work and avoid duplicating it. If another worker already covers a hypothesis, the child should attack it, discriminate it, independently replicate it, or work a non-overlapping subproblem inside its leased lane.

## Evidence law

Peer/model output is candidate evidence only. Agreement among many workers does not become canonical truth. Measured/runtime claims still require admissible receipts and exact identity.

The swarm is research/build orchestration only. It does not create multiple durable Mini Entities and cannot bypass MiniUnifiedDB, truth, secret, effect, generation, budget or execution authority.

## Runtime availability law

The trigger contract does not claim that every chat/runtime exposes the provider vault. If the current execution surface lacks admitted FREE_ONLY credentials, record the exact blocker and continue the local/non-provider part of the `go`/`zero` work. Do not fabricate a running swarm.
