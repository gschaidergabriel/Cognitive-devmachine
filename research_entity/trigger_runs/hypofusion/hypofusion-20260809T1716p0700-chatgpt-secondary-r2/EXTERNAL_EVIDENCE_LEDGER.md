# Hypofusion r2 — External Evidence Ledger

Run: `hypofusion-20260809T1716p0700-chatgpt-secondary-r2`

Evidence is classified by mechanism, not by similarity of project vocabulary. Project-internal agreement is excluded from independent replication.

## Compiler / semantic identity

- **RFC 8785 — JSON Canonicalization Scheme** — `BETTER_MECHANISM_CANDIDATE | DIRECT_SUPPORT`. Canonical hashing requires invariant serialization; JCS constrains numbers to IEEE-754 doubles, forbids NaN/Infinity, serializes minus-zero as zero, and recommends string representation for higher-precision/long integers. Implication: ClayCode needs an explicit numeric semantic domain, but should reuse a standard canonicalization mechanism where its admitted domain matches rather than invent a bespoke formatter. Ref: RFC 8785, https://www.rfc-editor.org/rfc/rfc8785.html
- **CompCert semantic-preservation theorem / manual** — `DIRECT_SUPPORT`. Compiler correctness is a source-to-target observable-behavior relation, separate from provenance/hash continuity. Ref: https://compcert.org/man/manual001.html
- **Monniaux & Boulmé, The Trusted Computing Base of the CompCert Verified Compiler (2022)** — `THEORY_CRITIQUE | FAILURE_MODE`. Even a verified compiler has modeling/toolchain/TCB boundaries. Implication: provenance and proof/validation claims must retain scope. Ref: arXiv:2201.10280.
- **Willsey et al., egg: Fast and Extensible Equality Saturation, POPL 2021** — `IMPLEMENTATION_PRECEDENT`. Equality saturation is practical across several optimization domains, but it does not imply unbounded saturation is optimal. Ref: DOI 10.1145/3434304.

## Resource lifetime / FFI

- **WebAssembly Component Model / Wasmtime Resource own/borrow** — `IMPLEMENTATION_PRECEDENT | DIRECT_SUPPORT`. Opaque typed resource handles have explicit dynamic ownership/lifetime rules and runtime-mediated tables. This supports live resource identity distinct from semantic identity, while leaving generation tags as only one implementation choice. Ref: https://docs.wasmtime.dev/api/wasmtime/component/struct.Resource.html
- **POSIX/open descriptor allocation semantics** — `IMPLEMENTATION_PRECEDENT`. Small integer descriptors are reused from available descriptor space; retained identifiers therefore require lifetime discipline at higher layers. Ref: POSIX/open specifications.

## Replay / concurrency / idempotency

- **FoundationDB deterministic simulation and debugging guidance** — `IMPLEMENTATION_PRECEDENT | DIRECT_SUPPORT`. Deterministic whole-cluster simulation is paired with real/hardware fault testing; exact replay can depend on OS/build environment. Implication: environment fingerprint belongs in deterministic replay identity, and simulation alone has blind spots.
- **TigerBeetle VOPR + Vortex testing** — `IMPLEMENTATION_PRECEDENT`. Deterministic state-machine/fault simulation is complemented by non-deterministic outside-in fault injection. Supports the dual-lane H-TR-005 design class.
- **OpenTelemetry SpanContext specification** — `PARTIAL_ANALOGUE`. Trace/span causal identity is propagated separately from application truth. Supports transportable cross-node causal IDs but does not make tracing metadata authoritative state.
- **SQLite isolation / BEGIN IMMEDIATE documentation** — `IMPLEMENTATION_PRECEDENT`. SQLite serializes writers; `BEGIN IMMEDIATE` starts a write transaction before the read/check path. This independently supports moving idempotency conflict classification inside the serialized transaction boundary rather than relying on a pre-lock read. Ref: https://www.sqlite.org/isolation.html and https://www.sqlite.org/lang_transaction.html

## GWT / recurrence

- **Gurnee et al., Verbalizable Representations Form a Global Workspace in Language Models (2026)** — `PARTIAL_ANALOGUE | MECHANISTIC_PRECEDENT`. J-space representations are reported as verbalizable, controllable, reusable and causally load-bearing under interventions. This supports testing a model-internal privileged workspace separately from FRANK's system-level workspace. It is not evidence of phenomenal consciousness. Ref: arXiv:2607.15495 and Anthropic research release.
- **Yang et al., STARS: Stabilizing Recurrent Dynamics for Test-Time Scalable Latent Reasoning (2026)** — `COUNTEREVIDENCE | BETTER_MECHANISM_CANDIDATE`. Looped LMs can peak and then collapse as recurrence depth increases; stability constraints mitigate this. Implication: adaptive continuation/overcoupling tripwires are more defensible than a monotonic 'more loops is better' claim. Ref: arXiv:2605.26733.

## Higher-order structure

- **Llabrés et al., Reducibility of higher-order to pairwise interactions, Physical Review Research 8, 023250 (2026)** — `COUNTEREVIDENCE`. A general class of hypergraph social-impact models is exactly reducible to weighted pairwise networks while preserving microscopic transition probabilities. This directly falsifies any universal claim that explicit hyperedges are always semantically necessary. DOI 10.1103/wy1x-3px8.
- **Peixoto et al., Graphs are maximally expressive for higher-order interactions (2026)** — `THEORY_CRITIQUE`. Argues graph parametrizations can encode multivariate interactions and challenges claims of intrinsic hypergraph expressivity. Ref: arXiv:2602.16937. This is a preprint and receives lower weight than the peer-reviewed exact-reduction result.

## UnifiedDB / incremental state

- **McSherry et al., Differential Dataflow, CIDR 2013** — `IMPLEMENTATION_PRECEDENT`. Differential computation can reuse work under changing inputs, including nested iteration. It supports incremental maintenance as a strong candidate mechanism, not a universal cost win.
- **Murray et al., Timely Dataflow / CACM 2016** — `IMPLEMENTATION_PRECEDENT`. General-purpose systems can mix incremental low-latency and batch/high-throughput modes. This supports H-CR-028's adaptive incremental-to-batch crossover rather than always-incremental doctrine.
- **Gupta, Mumick & Subrahmanian, Maintaining Views Incrementally, SIGMOD 1993** — `IMPLEMENTATION_PRECEDENT`. Classical incremental-view-maintenance support for updates/aggregation/recursion establishes the mechanism class independently of Clay.

## Retina / adaptive visual learning

- **Wei et al., Online Prototype Learning for Online Continual Learning, ICCV 2023** — `PARTIAL_ANALOGUE`. Online prototypes can support continual adaptation while addressing class confusion/shortcut learning. This supports prototype-based adaptation as a plausible family, not Clay's provenance/rollback design specifically.
- **Open-set prototype-recognition literature** — `PARTIAL_ANALOGUE | FAILURE_MODE`. Unknown rejection requires explicit open-set handling/calibration; closed-set confidence alone is insufficient. This supports keeping known/unknown/conflict distinct, but target-stream evidence remains required.

## Emergence

- **Partial Entropy and Information Decompositions under interventions (PEID, 2026 preprint)** — `PARTIAL_ANALOGUE`. Provides intervention-grounded decomposition of multivariate causal influence and synergy. Useful measurement candidate only; no promotion from one estimator/scalar. Ref: 2026 PEID preprint.
- **Dewhurst, causal-emergence critique (2021)** — `THEORY_CRITIQUE`. Effective-information improvement can support an epistemically useful coarse-graining without proving a stronger ontic causal-emergence claim. Implication: retain prospective intervention, lesion/rescue, multiscale and cross-implementation controls.

## Security / effect authority

- **seL4 capability model** — `IMPLEMENTATION_PRECEDENT`. Unforgeable capabilities bind object references and rights at the kernel boundary; supports external authority roots rather than model text as authority.
- **WASI capability model** — `IMPLEMENTATION_PRECEDENT`. Components start without ambient I/O authority and receive capabilities from the host; capability attenuation is possible. Supports WASI as a useful confinement backend, not proof that cross-step information flow is solved.

## Anti-echo conclusion

The fresh external evidence most strongly supports design *separations*: semantic identity vs provenance vs runtime lifetime; deterministic replay vs outside-in faulting; system workspace vs model-internal workspace; higher-order representation vs necessity of native hyperedges; per-operation authority vs composition-sensitive flow. None of these sources independently verifies FRANK or Clay as a complete architecture.