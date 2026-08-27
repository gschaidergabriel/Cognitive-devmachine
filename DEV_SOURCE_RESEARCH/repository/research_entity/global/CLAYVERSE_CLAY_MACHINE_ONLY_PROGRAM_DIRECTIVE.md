# CLAYVERSE / CLAY MACHINE ONLY — OWNER PROGRAM DIRECTIVE

## Authority

This directive supersedes all older active-program framing that selects Frank v0.1, self.root, UCM2-only, H1/H2/H3, or a Harness as the current product/program.

**ClayVerse is the only active top-level directive.** The active engineering program is the **Clay Machine**.

Legacy Frank/self.root/UCM2/Harness files, tests, receipts and modules remain valuable **bounded implementation and regression evidence** only when their measured semantics are relevant. They do not select current work and they do not define completion.

## Mission

Build a minimal, empirically testable Clay Machine whose core is:

1. **ClayCode** as a real programming language with explicit semantics;
2. a **ClayCode compiler/toolchain** with parser, IR, type/effect analysis, lowering and executable output;
3. a **virtual Clay Machine (Clay VM)** that executes Clay programs under defined instruction, memory, failure and resource semantics;
4. a **Clay Environment** — a self-contained directory/runtime containing the VM, libraries, state, tools and program artifacts;
5. **deep Linux interoperability** through explicit typed/effectful boundaries for files, processes, networking, devices/FFI and host services;
6. a **minimal ClayOS** personality/services layer implemented on top of the Clay VM/environment, sufficient to boot its defined scope, execute Clay programs, maintain state and interact with Linux;
7. a **first-class optical/visual signal path** in which ClayCode can emit and receive typed Clay-native visual signals/streams independent of any particular display technology, with explicit adapters to pixels, images, video, LEDs, displays, windows, projections, spatial/3D visualizers, renderers, devices or future optical media;
8. **general network and Internet connectivity** as a first-class Clay capability, progressively admitting real DNS/socket/TLS/web/streaming protocols through explicit typed effects rather than a special-case web wrapper;
9. **zero-install copy-and-run portability** for the supported Linux reference target: placing/copying the self-contained Clay Environment directory onto a compatible PC must be sufficient for normal launch, without a package-manager install, system-wide registration, root setup or hidden developer checkout;
10. **direct real Linux terminal/process execution** from ClayCode through explicit process/PTY effects, with no hidden Python harness or implicit shell defining semantics; shell interpretation exists only when ClayCode explicitly requests it;
11. a **low-latency Clay data plane** that transforms ordinary incoming bytes/text/structured streams into versioned Clay-native representations near ingress, retains provenance/raw bytes where required, supports incremental streaming and minimizes avoidable copies/serialization;
12. **media passthrough** in which image/video use the visual signal plane and audio uses a separate typed audio stream boundary, preserving payloads/timestamps/metadata and avoiding mandatory decode or semantic reinterpretation merely to transport the stream.

The fixed implementation/research plan for items 7-12 is `research_entity/clay_machine/CLAY_MACHINE_CONNECTIVITY_PORTABILITY_IO_PLAN.md`.

The objective is not a metaphorical OS or a renamed Python harness. ClayCode must progressively become an independently specified language, the VM must have observable executable semantics, and host behavior must not silently define Clay semantics.

The visual signal path is not a GUI feature and not presentation metadata. It is a fundamental Clay Machine I/O capability. Clay-visible meaning must exist before host rendering: adapters may transform a typed Clay visual signal into a concrete representation, but the adapter, renderer, display server, GPU API or device must not silently mint Clay semantics. The same Clay visual signal should be capable of targeting different renderers when their declared contracts support it.

Connectivity, portability, terminal execution and data/media transport are likewise core-machine properties rather than optional applications. "Direct terminal" means the canonical Clay process path maps as closely as practical to Linux process primitives (argv/env/cwd, pipes, PTY, signals, exit status) and does not insert an implicit shell. "Zero-install" means a self-contained supported build is copy-and-run; host kernel/ABI/hardware requirements must be declared rather than disguised as installation. "Low-latency" means minimal measured avoidable overhead, bounded buffering/backpressure and zero-/low-copy techniques where safe; literal zero latency must never be claimed without measurement.

## Research law

All research/build/test workers operate inside GRF as a reasoning scaffold:

`observed reality -> generated alternatives -> counter-realities -> discriminating tests -> intervention -> measured outcome -> collapse/fusion -> re-entry`.

GRF does not create authority. Imagination expands the search space; repository/runtime evidence contracts truth.

Each material result becomes one of: code delta, test obligation, architecture candidate, work item, counterhypothesis, negative result, or explicit NO_CHANGE.

## Language and VM authority

- Unknown syntax/semantics fail closed; do not inherit Python, Linux, C, shell, library or model behavior by name.
- Host intrinsics/FFI require explicit Clay signatures, effects and capability boundaries.
- Parser success is not type/effect success; type/effect success is not compiler success; compiler success is not VM/runtime acceptance.
- A VM instruction or runtime service is canonical only at the exact scope tested and versioned.
- No generic, member, builtin or standard-library semantics may be minted from corpus frequency or model agreement.
- Self-hosting is a later bootstrap property, not a prerequisite for the first useful Clay Machine.
- Optical/visual output semantics must be typed and explicit. A renderer or host API may implement a Clay-visible contract, but framebuffer, DOM, Wayland/X11, GPU, LED, projection, scene-graph or device behavior never becomes language authority merely because an adapter uses it.
- Network protocols, Linux process behavior, shell syntax, codecs and media libraries are host/protocol behavior, not Clay language authority. Clay contracts must expose the admitted semantics and failures explicitly.
- Raw/opaque byte transport is a valid typed state when semantic interpretation is unavailable or unnecessary; models/adapters must not guess a format to make progress.

## Linux relationship

Linux is the host substrate for the current reference implementation. ClayOS is not required to replace the Linux kernel. The Clay Machine may use Linux for process isolation, filesystems, networking, devices and scheduling while exposing Clay-native typed semantics above explicit interop boundaries.

A host adapter can be replaced only when the same Clay-visible contract, failures and recovery behavior remain measured. This replacement law also applies to visual/optical, network, process, terminal and media adapters.

The supported portable Clay Environment should launch from its own directory and directly invoke admitted Linux primitives through its explicit runtime boundary. A shell, Python interpreter, package manager, daemon or system installer must not be a hidden mandatory semantic dependency unless a particular declared build explicitly requires and tests it.

## Safety / authority

- Together API/service is forbidden.
- NVIDIA and genuinely free APIs/tools may be used where useful and permitted, but their output is evidence/candidate material, never semantic or effect authority.
- Never expose secrets.
- No final paid/model training without explicit owner authorization.
- Never claim a test, VPS run, build, effect, receipt, commit or completion that was not actually executed/observed.
- General connectivity does not erase capability/security boundaries: consequential network/process/device effects still require the explicit authority model selected for the Clay Machine.

## `go`

Exact `go` runs a maximum-useful Clay Machine macro-cycle:

`refresh shared state -> choose highest-information Clay Machine blocker -> hypotheses/counterhypotheses -> external primary evidence when material -> cheapest falsifier -> build/repair -> deterministic test -> Ubuntu/VPS test when available/applicable -> exactly one bounded unusual experiment -> fusion -> durable receipt/work delta -> reprioritize`.

Every exact `go` must load and keep live the fixed workstreams in `CLAY_MACHINE_CONNECTIVITY_PORTABILITY_IO_PLAN.md`: general Internet/network connectivity, zero-install copy-and-run portability, direct Linux terminal/process execution, low-latency Clay data transformation, visual/image/video transport and audio transport. Until their baseline gates are promoted, each `go` refresh must explicitly preserve their status/blockers and include them in frontier selection. Whenever an unblocked high-information step exists in this capability family, the macro-cycle must produce at least one concrete research, falsification, implementation, deterministic-test or measured-runtime delta there; documentation-only progress never counts as implementation PASS.

The optical/visual signal path remains a first-class workstream across language semantics, type/effect contracts, VM instructions/runtime, Clay Environment adapters, Linux/device interoperability, ClayOS services, deterministic headless rendering tests and concrete visual output. Media ingress/passthrough must be developed with the same separation between transport and semantic interpretation.

Do not ask the owner what to do when the frontier is inferable. Avoid duplicate work, preserve negative results and stop only when the next useful step is blocked, unsafe, owner-gated or lower-value repetition.

## Completion

Whole Clay Machine PASS requires reproducible evidence that the canonical language/compiler/runtime can execute real Clay programs in the Clay VM; operate inside the Clay Environment; cross Linux boundaries through explicit typed/effectful contracts; run the defined minimal ClayOS scope with observability/recovery appropriate to the exercised paths; emit/receive the canonical typed visual signal through both a deterministic sink and at least one concrete adapter; connect to a real network/Internet endpoint through the canonical Clay path; execute a real Linux process directly without an implicit hidden shell/harness; run as a copied self-contained environment on a fresh compatible Linux target without a mandatory install step; transform representative ordinary ingress data into Clay-native typed streams with measured overhead; pass image/video through the visual plane; and pass audio through its declared media boundary.

These are architectural capability gates, not a requirement that every protocol, codec, display or device exist before the first release.

Component PASS, synthetic success, a green legacy Frank workflow, a rendered image produced outside the canonical Clay path, a curl/subprocess result produced outside the canonical Clay effect path, or a coherent generated architecture never implies whole-machine completion.
