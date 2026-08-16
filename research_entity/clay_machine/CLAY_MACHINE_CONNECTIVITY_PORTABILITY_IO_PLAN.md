# Clay Machine — Connectivity, Portability and Low-Latency I/O Plan

Status: OWNER-FIXED TARGET WORKSTREAM
Date: 2026-08-16
Program: CLAYVERSE_CLAY_MACHINE_ONLY

## Purpose

This plan makes connectivity, zero-install portability, direct Linux execution and low-latency data/media transport first-class Clay Machine obligations. They are not optional integrations and they are not deferred UI polish.

The target is a Clay Machine that can be copied onto a compatible Linux PC as a self-contained directory and run immediately, connect to networks and the Internet through Clay-visible typed effects, execute real host processes/terminal sessions through a direct explicit Linux boundary, transform ordinary incoming data into Clay-native typed representations with minimal avoidable latency, and pass visual/media streams through the appropriate Clay I/O modules without forcing expensive semantic conversion of every byte/frame/sample.

## Fixed capability workstreams

### CM-NET — General network / Internet connectivity

The architecture must permit general-purpose connectivity rather than a special-case web client. The progressively admitted surface should cover, where justified by tests: DNS/name resolution, TCP, UDP, TLS, HTTP(S), WebSocket/streaming and later additional protocols/services through explicit adapters.

Requirements:
- network access is expressed as explicit ClayCode effects/capabilities;
- connection, address, timeout, cancellation, partial I/O, EOF and failure semantics are Clay-visible;
- host libraries/kernel calls implement the contract but do not define Clay language semantics;
- raw byte streams remain available so future protocols do not require redesigning the VM;
- receipts/observability bind requested effect to actual network outcome;
- security/capability policy can restrict consequential destinations/actions without turning the machine into an artificial air-gap.

Baseline PASS: a real Clay program resolves/connects/sends/receives through the canonical VM/environment path and the result is reproducible with failure-path tests.

### CM-PORT — Zero-install, copy-and-run Clay Machine

Normal use must not require a package-manager install, system-wide registration, root access or a setup wizard. The distributable form is a self-contained Clay Environment directory containing the launcher/runtime, ClayVM, required libraries/artifacts, configuration and local state layout.

Requirements:
- copy/extract directory onto a compatible Linux PC;
- launch directly from that directory;
- no mandatory system package installation for the supported reference build;
- no hidden dependency on repository checkout or developer tooling;
- relative/path-independent resource discovery inside the environment;
- writable state defaults to a declared local/state location unless the user explicitly selects external storage;
- moving/renaming the directory must be tested;
- host ABI/kernel/hardware requirements are declared rather than disguised as installation steps.

Baseline PASS: fresh compatible Linux machine/container/VM, copy artifact directory, run one command, execute a real Clay program, restart, move the directory, run again, and verify artifact/state provenance.

### CM-TERM — Direct Linux terminal/process execution

ClayCode must be able to execute real commands and interactive terminal programs. The canonical path must not depend on a hidden Python harness or an implicit shell that invents semantics.

Requirements:
- direct process spawn maps as closely as practical to Linux process primitives (for example execve-style argv/env/cwd plus pipes/PTY);
- shell interpretation occurs only when ClayCode explicitly requests a shell effect;
- Clay-visible stdin/stdout/stderr, exit status, signals, environment, working directory, cancellation and PTY/session semantics;
- byte-preserving streaming I/O;
- typed/effectful capability boundary and receipts for consequential host effects;
- deterministic tests use harmless commands plus negative/failure cases.

Baseline PASS: ClayCode launches a real Linux executable without an implicit shell, exchanges streaming I/O, observes exit/failure semantics, and separately proves an explicit PTY/shell path.

### CM-DATA — Low-latency Clay data plane

Ordinary data entering the Clay Machine should be transformed into Clay-native typed/structured representations as close to ingress as practical, while retaining source bytes and provenance when lossless recovery matters.

Requirements:
- canonical envelopes for bytes, text, structured records, streams, timestamps, provenance and schema/version identity;
- incremental/streaming transformation rather than whole-buffer conversion when possible;
- avoid repeated parse/serialize/copy cycles;
- zero-copy/shared-buffer/memory-view techniques may be used where safe and measurable;
- transformation is explicit and versioned; unknown formats fail closed or remain typed opaque bytes rather than being guessed;
- latency, throughput, allocation/copy count and backpressure are measurable.

Performance law: do not claim literal zero latency. Optimize for minimal avoidable added latency, bounded jitter and near-zero-copy paths where feasible, and report measured overhead.

Baseline PASS: representative byte/text/structured streams enter through one canonical ingress path, become Clay-native values/streams, cross the VM/runtime path and are consumed with measured latency/copy/allocation data.

### CM-VIS — Visual/image/video signal plane

The already-fixed first-class optical/visual output obligation extends to ingress/passthrough for image and video. Visual payloads may remain encoded/raw buffers plus Clay metadata/timestamps until a visual operation actually requires decoding or semantic transformation.

Requirements:
- typed visual signal/envelope identity;
- image/video buffer and stream passthrough;
- timestamps/frame ordering/backpressure/drop policy are explicit;
- renderer/codec/device adapters do not mint Clay semantics;
- headless deterministic sink plus concrete visual adapter;
- low-copy buffer transport where supported;
- optional visual analysis is separate from transport.

Baseline PASS: ClayCode/ClayVM passes an image and a short video/frame stream through the canonical visual path to a deterministic sink and at least one real visual adapter, preserving declared metadata and measured transport behavior.

### CM-AUDIO — Audio stream boundary

Audio is a separate media stream boundary rather than being forced through the visual representation. Encoded/raw audio must still be transportable through the Clay Machine with Clay-visible metadata, timing and stream semantics.

Requirements:
- encoded/raw audio buffers and streams;
- sample/packet timing, format identity, channel/rate metadata when known;
- passthrough without mandatory decode or semantic interpretation;
- explicit adapters for playback/capture when admitted later;
- low-copy streaming and backpressure measurements.

Baseline PASS: an audio payload/stream can traverse the canonical Clay path losslessly at the transport layer with deterministic sink verification.

## Unified architecture rule

All these workstreams must converge on one Clay-native I/O/effect architecture rather than separate hidden subsystems:

`ClayCode -> typed/effect IR -> ClayVM -> Clay Environment capability/adaptor boundary -> Linux/network/device/renderer -> observed outcome -> receipt/re-entry`

For inbound data:

`Linux/network/device/media source -> explicit adapter -> typed Clay ingress envelope or typed opaque bytes -> ClayVM/runtime -> ClayCode consumer`

No adapter gains semantic authority from a name, protocol, library or device. Raw transport and typed semantic transformation are separate layers so high-bandwidth data can pass through quickly without requiring every byte/frame/sample to be reinterpreted.

## Exact `go` obligation

Every exact `go` cycle must load this plan during frontier refresh until all baseline gates are promoted. Each cycle must:
1. preserve current status/blockers for CM-NET, CM-PORT, CM-TERM, CM-DATA, CM-VIS and CM-AUDIO;
2. include these workstreams in hypothesis/counterhypothesis and reprioritization;
3. produce at least one concrete research, falsification, code, deterministic-test or measured-runtime delta in this capability family whenever an unblocked high-information step exists;
4. never allow documentation-only progress to count as implementation PASS;
5. continue obeying the global exactly-one bounded unusual-experiment law for the overall `go` macro-cycle.

The workstreams can be developed incrementally, but none may be silently dropped from the Clay Machine completion target.

## Whole-machine completion impact

Whole Clay Machine PASS is impossible until the canonical path has demonstrated, with reproducible evidence:
- copy-and-run zero-install operation on a fresh compatible Linux environment;
- real general network/Internet connectivity through explicit Clay effects;
- direct real Linux process/terminal execution with no implicit hidden shell/harness semantics;
- measured low-latency ordinary-data ingress/Clay transformation;
- visual/image/video passthrough through the canonical visual signal path;
- audio transport through its declared media boundary;
- failure, cancellation, recovery, provenance and observability appropriate to the exercised paths.

These are minimum architectural possibility gates, not a claim that every protocol, codec, device or renderer must be implemented before the first Clay Machine release.
