# ClayCode Trigger Run — Deterministic APP-02 HTTP Lowering

Run: `claycode_20260809T1607p0700_chatgpt_http_app02`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (`IN_PROGRESS`)  
Promotion: **none**

## Executive result

This run strengthens the BASE-stage compile-first direction without adding a new ClayCode core semantic primitive.

The bounded APP-02 experiment lowered a canonical ClayCode HTTP-service representation through `cc-http-lowerer-v2` into a real local HTTP server. Three adversarial/positive cases all behaved as expected:

- no host listener handle -> denied;
- forged file-descriptor number -> denied;
- valid host-created listener -> real HTTP service, deterministic routes/assets/404 behavior and 32 concurrent requests completed.

Repeated lowering produced the same generated-code SHA-256. The run therefore supports, within this bounded experiment, the hypothesis that existing G9 records/rules/effect-reference semantics plus a typed host resource adapter are sufficient for HTTP-service realization without an HTTP-specific ClayCode core primitive.

The strongest negative result is equally important: the earlier v1 design embedded a per-run capability-token hash into generated code and thereby changed generated-program identity across executions. Capability instances therefore belong in runtime resource/authority state or deployment receipts, not silently inside deterministic compiler-output identity.

This is **not APP-02 PASS** and not `GENERAL_PURPOSE_GATE: PASS`. The current generated target is ordinary Python and is not a production capability sandbox. A guest with unrestricted host APIs/imports could recover ambient authority outside the tested narrow path. Production acceptance still requires an opaque typed host-resource/FFI boundary plus OS/runtime enforcement and differential tests.

## Canonical and program grounding

Immediately before final write, canonical state was re-read and remained:

- entity version RAE-8.8;
- revision 2;
- state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.

The active stage remains `BASE_CLAYCODE_RELEASE`. Its governing law remains `preserve semantics -> freeze -> compile/lower -> execute -> test -> change language only when an executable counterexample forces it`.

No canonical revision, ClayCode authority, BASE gate, application-pass list or current G9 source was changed by this run.

## Internal executable evidence

Primary receipt:

`experiments/http_app02_v2/EXECUTABLE_RESEARCH_RECEIPT.json`

Observed:

- compiler fragment: `cc-http-lowerer-v2`;
- backend: local container / Python 3.13.5 / loopback-only network;
- deterministic generated target identity within repeated run;
- missing handle denied with exit 77;
- forged handle denied with exit 77;
- valid inherited listener served `/`, an asset, and deterministic 404 behavior;
- 32 concurrent HTTP requests completed with expected monotonic state counts;
- no capability-instance secret was compiled into generated code.

Preserved negative receipt:

`experiments/http_app02_v1/EXECUTABLE_RESEARCH_RECEIPT.json`

Its failure mode — capability-token material contaminating generated-code identity — is retained as `N-CC-HTTP-20260809-01`.

## Concurrent ClayCode evidence assimilated

A concurrent whole-current-G9 surface-closure run measured all 86 top-level current G9 V3 chunks:

- checked-in grammar proxy: 61/86 pass, 25/86 fail;
- strict normalization candidate N: 86/86 parse closure;
- no new cognitive/runtime semantic primitive was required for that parser closure;
- N is not selected because S and D remain live relation-surface alternatives pending matched full-corpus typed-IR comparison.

A separate semantic-publication experiment reported 12/12 fixed cases plus 20,000 mutation rounds with zero violations for the typed epoch-publication barrier and found no need for new syntax. These concurrent workers share project ancestry and are not treated as independent replication.

Combined implication: the immediate BASE problem is increasingly an implementation/surface/type/runtime closure problem rather than evidence for another round of semantic-core invention.

## Cross-branch synthesis

### FRANK

The fixed effect-authority boundary survives this run: model/source text may express intent and reference resource identity, but execution authority remains external and host/runtime controlled. The HTTP experiment adds an executable example of this separation; it does not prove the final backend.

### ClayGraph

Activation, salience, graph selection and derived relations remain relevance/topology state, not network-effect authority. HTTP lowering must therefore consume explicit typed resource authority rather than infer it from graph accessibility.

### UnifiedDB

Capability/resource instance state, freshness, execution receipts and semantic identity belong in explicit state/receipt planes. The v1 identity failure is a concrete example of why runtime authority instances must not be conflated with compiler semantic identity.

### GWT / Hyperposition / Emergenz

Service concurrency is not emergence evidence. Selection/broadcast/use/effect/outcome/re-entry and semantic/active/physical topology identities remain separate. Nothing in this run changes an emergence claim.

### Harness

H2 remains blocked on BASE. The useful handoff from this run is a testable backend boundary: identical Clay semantic IR must lower through explicit resource imports/handles while preserving deterministic receipts and denying absent/forged authority.

## External research and second-backend candidate

Current primary-source WebAssembly evidence makes the Component Model/WIT + WASI 0.3 path a high-information second backend candidate, not a selected architecture.

Useful independent mechanisms:

- WIT models typed component imports/exports and abstract resource handles with ownership/borrowing semantics;
- WASI 0.3, released in June 2026, makes asynchronous functions, futures and streams first-class Component Model concepts;
- this provides a plausible way to test HTTP, resource lifetime, cancellation and concurrency semantics without adding HTTP-specific ClayCode core syntax.

Counterweight: WebAssembly validation or a component boundary is not itself proof of safe authority confinement. Runtime implementation vulnerabilities remain possible, so any Wasmtime/WASI backend used as a security boundary must be version-pinned, adversarially tested and covered by host-grant/effect receipts.

## Goodman anti-echo result

The run-local `FRANK_CLAYCODE_GOODMAN_REVIEW.json` records:

1. host/runtime ownership of effect authority: `SUPPORTED`;
2. no ambient OS authority / host-minted resources: `REFINED` — opaque typed resources + OS/runtime enforcement are required; raw FD passing in unrestricted Python is only a prototype;
3. conventional backend encoding under Clay semantic authority: `REFINED` — bounded HTTP lowering works, but streaming, cancellation, structured errors, resource lifetimes and second-backend equivalence remain falsifiers.

FRANK/ClayCode shared ancestry was collapsed and was not counted as replication.

## Hypotheses carried forward

- `H-CC-HTTP-20260809-01` — run-local support: bounded HTTP can be realized through typed host adaptation without HTTP-specific core syntax.
- `H-CC-HTTP-20260809-02` — run-local refined support: bind/serve authority can remain host-owned and generated program identity need not contain capability secrets.
- `H-CC-HTTP-20260809-03` — open external support: Component Model/WASI-style typed resources are a strong candidate backend boundary.
- `H-CC-HTTP-20260809-04` — open: the next high-information step is matched differential lowering of one frozen canonical HTTP IR to two backends, not language redesign.

## Negative results / blockers

- `N-CC-HTTP-20260809-01`: per-run capability-token embedding breaks deterministic generated-code identity.
- `N-CC-HTTP-20260809-02`: inherited FD into unrestricted Python is not proof of a production capability sandbox.
- `N-CC-PREFLIGHT-20260809-01`: current mandatory interconnect-preflight governance is stale after `clay -> clayresearch`; registry and hard-coded preflight priority sets differ. Strong promotion therefore remains fail-closed.

The last blocker is governance/tooling drift, not a scientific reason to discard the HTTP result. It prevents claiming a strong protocol completion/promotion until the preflight validator is synchronized.

## Highest-information next experiment

Freeze one canonical HTTP/concurrent-service IR and lower the exact same semantic object to two backends:

1. current native/Linux host-handle reference path;
2. a Component Model/WASI 0.3 resource/import path where network authority is only available through explicit host imports.

Require:

- identical source semantic hash;
- explicit backend/contract hashes;
- positive route/state behavior;
- missing/forged-resource denial;
- structured error equivalence;
- resource lifetime/close behavior;
- async cancellation and concurrent requests;
- deterministic or explicitly scoped nondeterminism receipts;
- no ambient filesystem/network authority outside granted imports;
- performance/cost shadow;
- mutation/fuzz tests;
- cross-backend expected-vs-observed semantic differential.

If this matched test succeeds, it would materially advance `CC-WP-06`, `CC-WP-07`, `CC-WP-09`, `CC-WP-10` and `CC-WP-11`. If it exposes an unrepresentable semantic distinction, that becomes the executable counterexample required before changing ClayCode semantics.

## Run completion boundary

Required run artifacts now include canonical/run grounding, interconnect manifest, tool execution manifest, Goodman review, hypotheses, preserved negative results, executable receipts and this final report.

Strong promotion remains intentionally blocked by the current `clay` -> `clayresearch` preflight governance drift. No attempt was made to bypass that check and no canonical promotion is claimed.
