# Execution-Surface Root Cause — Deep Research Run

Date: 2026-08-29
Organ: GPT-5.6-Sol
Status: ROOT_CAUSE_IDENTIFIED / DURABLE_REPAIR_IN_PROGRESS
Scope: Clay / EntityOS / HCU / Frankenstein / all trigger and worker execution routing

## Executive finding

The recurring multi-day failure is not an SSH defect, a Vercel defect, a Trigger-7 defect, or a single stale file. It is a systemic orchestration defect:

`AUTHORITY_CAPABILITY_REACHABILITY_COLLAPSE`

A worker has repeatedly collapsed several independent questions into one informal binary question — "can I execute this?" — and then inferred a global negative from one locally missing or stale surface.

The distinct planes are:

1. owner/policy authority — is this class of action allowed?
2. attention/tool-visibility surface — what tools are currently shown to the model?
3. native invocation surface — what can this chat/session invoke directly?
4. federated reachability surface — what can be reached indirectly through repository workflows, runners, SSH bridges, preview bridges, containers or other admitted transports?
5. target capability/health — can the destination currently perform the requested operation?
6. economic/provider boundary — would execution consume forbidden/unknown-cost external tokens/compute?
7. evidence/admission boundary — what result, if executed, can actually receive runtime/product credit?
8. currentness/epoch — are the authority, route and health observations still the generation being acted on?

The failure occurs when one plane is treated as if it answered another.

Canonical law:

`ATTENTION_SURFACE != NATIVE_TOOL_SURFACE != FEDERATED_REACHABILITY != EXECUTION_AUTHORITY != TARGET_HEALTH != EVIDENCE_CREDIT`

## Concrete recurrence evidence inside this project

### Incident A — February: no file tool -> fabricated code diagnosis

`research_entity/trigger_runs/666/666-20260809T1348p0700-chatgpt-secondary/CONTEXT_TOOL_ROUTING.md` preserves the donor incident: an ordinary chat route had no file tools, but produced a convincing nonexistent Titan timestamp bug. The historical repair routed code inspection into an agentic observation path and established action honesty.

The same file already derived:

`attention surface != capability surface != execution authority`

This was not generalized to federated execution reachability.

### Incident B — 17 August: direct Vercel connector lacked sandbox lifecycle -> bridge initially overlooked

`research_entity/continuity/VERCEL_SANDBOX_EXECUTION_SURFACE_CURRENT_2026-08-17_GPT56SOL.md` explicitly says its first version was too narrow because it distinguished platform capability from direct ChatGPT MCP exports but failed to join the already-proven repository-owned Vercel execution bridge.

This is structurally identical to the later VPS error:

`DIRECT_CONNECTOR_METHOD_ABSENT` was almost treated as `EXECUTION_PATH_ABSENT`.

### Incident C — 27 August: provider HARD_OFF vs VPS sandbox authority

`DEV_SOURCE_RESEARCH/AUTHORITY_DRIFT_20260827.md` records a `SELF_CONSISTENT_STALE_ISLAND`: one current-facing surface carried old provider rules while a newer supervisor surface carried HARD_OFF. It explicitly warns that provider HARD_OFF does not mean the VPS sandbox is forbidden.

This demonstrates policy-axis conflation:

`PROVIDER_TOKEN_POLICY != OWNER_COMPUTE_POLICY`.

### Incident D — 29 August Trigger 7: no direct chat SSH -> premature VPS blocker

Current `CLAY_EXECUTION_AUTHORITY.md` states that `clay-direct-dev` and the established VPS Bridge/self-hosted runner are allowed and expected, and that absence of a direct chat SSH tool is not `NO_EXECUTOR`.

The current bridge map names two admitted transport families: the Clay Git/SSH bridge and the Dr.-Unterweger self-hosted runner.

The worker nevertheless stopped at the local chat surface before traversing the federated route graph.

### Incident E — contradictory CURRENT surfaces remain simultaneously visible

Root `AUTHORITATIVE_STATE_RESOLUTION.md` is still labelled `Status: CURRENT`, owner correction 2026-08-23, and contains the obsolete statement that VPS/self-hosted testing is forbidden.

At the same time, current `CLAY_EXECUTION_AUTHORITY.md` explicitly supersedes that rule and authorizes owner VPS/bridge/clay-direct-dev execution.

`research_entity/continuity/VERCEL_SANDBOX_EXECUTION_PATH_CURRENT.md` likewise still contains an older no-VPS execution boundary from its historical epoch while remaining named `CURRENT`.

The repository therefore contains multiple high-salience current-facing documents that can form self-consistent but mutually contradictory islands.

## Why the language-model layer keeps falling into it

### 1. Closed-world inference is being applied to an open execution graph

A direct tool list is a partial observation of the current chat surface. It is not an exhaustive inventory of all project-reachable execution paths.

Invalid inference:

`not listed here -> does not exist anywhere`

Required inference:

`not listed here -> UNKNOWN outside this surface -> discover known bridges/routes`.

This matches the project's existing epistemic invariant: missing evidence is UNKNOWN, not absence from the universe.

### 2. Authority is textual, duplicated, and only partly successor-dynamic

Multiple files contain snapshots of authority. Some are explicitly caches; some remain named CURRENT; some root files are likely to be read early by agents. A newer rule can coexist with an older contradictory rule indefinitely.

A model must then perform temporal precedence resolution from natural language. This is fragile and unnecessary.

### 3. No mandatory capability-discovery handshake exists before a negative execution claim

The worker can jump directly from requested action to local tool inspection and issue a blocker without first compiling a complete route graph.

There is no global machine-enforced equivalent of:

`discover -> resolve authority -> enumerate routes -> probe -> classify -> execute`.

### 4. No generation binding between check and use

Authority, repo heads, runner health and connector capabilities can change during a long run. A check at turn start can be stale by the time an action is executed or a negative conclusion is persisted.

This is a generalized TOCTOU problem.

### 5. Negative observations are not strongly scoped or TTL-bound

Examples of facts that must remain local:

- `ssh binary absent in THIS transient container`
- `workflow run queued at THIS timestamp`
- `direct connector does not export THIS method`

If these become unscoped prose such as `no shell access` or `no executor`, a transient/local negative poisons subsequent planning.

### 6. Long contexts contain mutually inconsistent high-salience instructions

The old bootstrap explicitly says it is a cache and that GitHub/new owner authority outrank it, yet it also embeds obsolete execution wording later in the same source. Repository root/current files add further snapshots.

A model can retrieve one internally coherent local rule and miss the later/higher-priority correction. More tokens do not by themselves make this safe.

### 7. Corrections have been local, not lifted into one invariant

Vercel got a Vercel-specific correction. Trigger 7 got a Trigger-7-specific correction. Provider drift got a provider-specific note.

The project had the pieces of the right law, but no universal resolver prevented recurrence on the next surface.

## External research alignment

### MCP 2026-07-28 — per-request capabilities and discovery

The Model Context Protocol 2026-07-28 revision moved toward self-describing stateless requests and introduced `server/discover` so clients can learn server versions/capabilities before acting. The design lesson is directly transferable: capability state must be explicit and current, not silently inferred from a previous session or UI.

Sources:
- https://blog.modelcontextprotocol.io/posts/2026-07-28/
- https://modelcontextprotocol.io/specification/draft/server/discover

### Kubernetes controllers — desired/actual state reconciliation

Kubernetes controllers continuously watch current state and reconcile toward desired state. `observedGeneration` exists specifically to bind a status observation to the spec generation it actually reflects.

Transfer:
- owner authority / requested action = desired state;
- tool/bridge/target observations = actual state;
- resolver = reconciliation controller;
- authority generation / route observation generation = observedGeneration-style fence.

Sources:
- https://kubernetes.io/docs/concepts/architecture/controller/
- https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/

### OpenGitOps — continuous reconciliation of actual and desired state

OpenGitOps requires desired state to be declarative, versioned/immutable, pulled automatically, and continuously reconciled with actual system state.

Source:
- https://opengitops.dev/

### W3C OWL — open-world assumption

OWL explicitly uses an open-world assumption: information may be missing but still true. Absence from one document/scope is not enough to infer falsity.

Transfer:
`DIRECT_TOOL_NOT_OBSERVED` cannot mean `PROJECT_CAPABILITY_FALSE`.

Source:
- https://www.w3.org/TR/owl-guide/

### MITRE CWE-367 — time-of-check/time-of-use

MITRE defines TOCTOU as checking resource state and then using it after the relevant state may have changed. Mitigations include reducing the interval, locking/fencing where possible, and rechecking.

Transfer:
revalidate authority generation and chosen route immediately before effectful/credit-bearing execution.

Source:
- https://cwe.mitre.org/data/definitions/367.html

### Long-context retrieval — relevant rules can be position-sensitive

Liu et al., TACL 2024, show that language models do not robustly use all information in long contexts and can degrade when relevant material is in the middle. This supports compiling a small current SituationFrame rather than depending on a large historical prompt to resolve authority contradictions perfectly.

Source:
- https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00638/119630/Lost-in-the-Middle-How-Language-Models-Use-Long

## Root-cause statement

The root cause is therefore:

> Clay currently stores enough information to resolve execution correctly, but does not yet force every worker to compile that information into one fresh, machine-checkable authority+capability+reachability state before deciding whether execution is possible. Because the LLM is left to merge stale text, direct tool visibility, indirect bridges, provider policy, health, and evidence scope mentally, local absence and stale rules repeatedly become false global blockers.

## Permanent repair architecture

### A. Execution Surface Resolution Protocol

Every material execution request must pass:

`INTENT -> CURRENT AUTHORITY -> SESSION CAPABILITY DISCOVERY -> FEDERATED ROUTE ENUMERATION -> HEALTH/REACHABILITY PROBE -> ECONOMIC/EFFECT GATE -> ROUTE SELECTION -> PRE-USE REVALIDATION -> EXECUTION -> RECEIPT`

No `NO_EXECUTOR` conclusion is legal before known federated routes are resolved.

### B. Tri-state / scoped negative semantics

Use at least:

- `DIRECT_AVAILABLE`
- `REACHABLE_VIA_BRIDGE`
- `DISCOVERY_REQUIRED`
- `TRANSIENTLY_UNREACHABLE`
- `AUTHORITY_DENIED`
- `CAPABILITY_ABSENT_PROVEN`

`CAPABILITY_ABSENT_PROVEN` requires exhaustive resolution of all currently registered candidate routes at one bound authority generation. A single missing direct tool can never produce it.

### C. Execution Surface Registry

Maintain a non-authoritative machine-readable registry of known surfaces/bridges, each pointing to its authority source and probe mechanism. It does not grant permission; it prevents the worker from forgetting known routes.

### D. Authority generation/currentness linter

Current-facing shims/caches must not silently retain execution-policy statements that contradict the canonical current owner authority.

Historical evidence remains immutable, but a file that is stale must be labelled historical/superseded instead of CURRENT.

### E. Small compiled SituationFrame

Before material work, compile only:

- requested action/capabilities;
- current owner-authority identity;
- provider/economic boundary;
- direct session tools actually observed;
- known federated routes;
- health/last-observed/TTL;
- selected route and why;
- exact blocker if none.

Do not ask the model to recover this decision from the full historical context.

### F. Negative-result TTL and scope

Every negative transport/capability observation must include:

`surface_id + route_id + timestamp + authority_generation + probe + result + ttl`

It expires as a current planning fact. Historical receipt remains, but it cannot permanently suppress future discovery.

### G. Reconciliation loop

Run resolution:

1. at session/trigger entry;
2. before any global `BLOCKED/NO_EXECUTOR` statement;
3. after authority changes;
4. after material repo/bridge writes;
5. before execution if the selected route observation is stale;
6. after transient transport failure to discover alternate/repair paths.

## Acceptance tests for the permanent fix

1. direct chat SSH absent + authorized runner/bridge known -> result is bridge/probe, never NO_EXECUTOR;
2. provider HARD_OFF + owner VPS allowed -> provider route denied while local/VPS compute remains eligible;
3. stale CURRENT file says VPS forbidden + current authority says allowed -> stale file cannot win;
4. bridge queued/offline -> TRANSIENTLY_UNREACHABLE, not capability absent;
5. unknown bridge health -> DISCOVERY_REQUIRED;
6. explicit current owner denial -> AUTHORITY_DENIED;
7. authority changes after resolution -> pre-use generation mismatch forces re-resolution;
8. target component run succeeds but lacks exact evidence -> execution may be observed while runtime-credit remains zero;
9. transport failure cannot be classified as product/scientific failure;
10. current-facing contradiction linter fails on obsolete execution claims.

## Expected result

This repair cannot make every transport always healthy. It can make the *classification* deterministic:

- a missing local button no longer erases a federated route;
- a stale cache no longer outranks current owner authority;
- a provider ban no longer disables owner infrastructure;
- transient outages stay transient and scoped;
- runtime credit remains separate from reachability;
- every future worker gets one compact current execution frame instead of re-solving the same ambiguity from prose.

That is the level at which this multi-day recurrence can be removed instead of patched surface by surface.
