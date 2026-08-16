# Clay Machine — Optical / Visual Signal I/O Workstream

Status: ACTIVE OWNER REQUIREMENT
Program: CLAYVERSE_CLAY_MACHINE_ONLY
Target integration: language -> type/effect system -> compiler/IR -> ClayVM -> Clay Environment -> Linux/device adapter -> visual medium

## Owner requirement

The Clay Machine must fundamentally be able to emit a Clay-native optical/visual signal from ClayCode. The signal must be machine-readable before any renderer sees it and must be mappable to different visual realizations without changing its Clay-visible meaning.

This is a core machine I/O capability, not an optional GUI, dashboard, theme, or visualization layer.

## Architectural invariant

The canonical boundary is:

`ClayCode intent -> typed VisualSignal value/effect -> canonical IR -> VM-visible output event/state -> Clay Environment sink contract -> adapter -> concrete visual medium`

A renderer is an adapter, never semantic authority.

Candidate concrete adapters may eventually include, without privilege or semantic preference:

- deterministic headless/event-log sink for tests;
- framebuffer/pixel surface;
- Wayland/X11/window renderer;
- terminal/ANSI visual projection where contract-compatible;
- LED / RGB / light-array output;
- monitor/display output;
- browser/canvas renderer;
- SVG/vector renderer;
- spatial/3D scene renderer;
- projector/light installation;
- external visualizer process;
- device/FFI bridge;
- future optical media not yet known.

The core Clay signal must not depend on any one of these.

## Research questions

1. What is the smallest useful canonical `VisualSignal` algebra?
2. Is the first canonical surface event-based, retained-state, scene-graph based, pixel based, vector based, or a typed composition of primitives?
3. Which properties belong in Clay semantics versus renderer policy: coordinate system, time, color, alpha, layers, transforms, text, images, geometry, animation, identity, lifetime?
4. Does visual emission require an effect such as `visual.emit`, a capability token, a typed sink parameter, or a VM output port?
5. How are deterministic replay and receipts defined for time-varying visual signals?
6. What are the resource limits: signal size, frame/event rate, retained state, object count, recursion, textures/assets?
7. How does failure behave when no adapter exists, an adapter is disconnected, a device is slow, or the signal is unsupported?
8. Which conversion rules are lossless, lossy-but-explicit, or forbidden?
9. How can the same Clay program be tested headlessly and later mapped to LEDs, 2D displays or 3D visualizers without host-specific branches becoming Clay semantics?
10. How should visual input and visual output remain distinct so a future perception/camera path does not contaminate output authority?

## Initial candidate semantics — NOT YET CANONICAL

Use a small typed signal envelope with explicit version, channel, time/sequence identity and payload kind. Candidate primitive families:

- `Clear`
- `Point`
- `Line`
- `Rect`
- `Circle`
- `Path`
- `Text`
- `ImageRef`
- `Transform`
- `Group`
- `FrameBoundary`
- `Light` / `ScalarChannel`

These names are research candidates only. No syntax or runtime authority is granted by this document.

A useful first falsifier is to compare three minimal representations:

A. immediate pixel/framebuffer commands;
B. retained scene/object graph;
C. renderer-neutral typed event stream with optional retained identity.

The discriminator should measure determinism, replayability, cross-adapter mapping, VM complexity, resource bounding and whether host behavior leaks into semantics.

## Acceptance ladder

### V0 — contract only
- explicit VisualSignal candidate schema;
- no host-renderer authority;
- deterministic canonical serialization;
- negative tests for unknown signal kinds and malformed values.

### V1 — headless end-to-end
- ClayCode source emits one admitted visual signal;
- canonical parser/type/effect/IR path accepts it;
- the single ClayVM executes it;
- Clay Environment receives it through a typed sink;
- deterministic headless sink records canonical output;
- exact expected receipt/hash can be reproduced.

### V2 — concrete visual adapter
- same canonical signal/receipt is mapped by at least one real adapter to visible output;
- changing the adapter does not change Clay-visible program semantics;
- unsupported/lossy mapping fails or degrades only according to an explicit adapter contract.

### V3 — temporal/interactive visual stream
- ordered multi-signal/frame behavior;
- explicit time/sequence semantics;
- bounded backpressure/resource behavior;
- replay test.

### V4 — heterogeneous visual media
- at least two materially different adapters, e.g. 2D pixels and LED/spatial output;
- one Clay program can target both through declared adapter contracts.

Whole Clay Machine completion is blocked below V2.

## `go` integration law

Every exact `go` refreshes this workstream and considers it in frontier selection. When actionable and high-information, `go` must perform research -> hypotheses/counterhypotheses -> cheapest falsifier -> build/repair -> deterministic test -> applicable Ubuntu/VPS/device test -> fusion -> durable delta for this path.

A `go` cycle may choose another higher-information blocker, but it may not silently drop visual-signal I/O from the active target. Deferral must remain explicit.

## Safety / authority

- Together is forbidden.
- No paid/final training without owner authorization.
- Renderer APIs, Linux graphics stacks, browser behavior, GPU behavior and device protocols are implementation evidence, not Clay language authority.
- Do not claim visible hardware output unless it was actually observed.
- Headless test PASS is not concrete-adapter PASS.
- Concrete-adapter PASS is not whole Clay Machine PASS.
