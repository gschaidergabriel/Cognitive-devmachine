# CM-I/O shared frontier — canonical Bytes transport across OP_HOSTCALL

Date: 2026-08-17
Program: CLAYVERSE_CLAY_MACHINE_ONLY / CLAY_MACHINE
Product boundary: one executable `EntityOS`
Trigger context: `go`
Affected workstreams: CM-NET, CM-DATA, CM-VIS, CM-AUDIO; adjacent CM-TERM
Execution classification: SOURCE-INSPECTION / TEST-OBLIGATION DELTA ONLY. No Vercel Sandbox execution occurred for this work item and no new unusual experiment is consumed.

## Observed anchors

Current product `main@6012d2cf4125e65d3a0c2df8d3b37119ae4f7b47` already contains a canonical CLAYVM/2 value surface with `Bytes` function parameters/returns and fail-closed owned-Bytes admission. `ExecutableIR` lowering also admits `Int`/`Bytes` function locals/parameters.

However, the canonical host boundary is still narrower:

- `ClayHost._calls` is typed as `Callable[[list[int]], int]`;
- `ClayHost.invoke` takes `list[int]` and returns `int`;
- the runtime `OP_HOSTCALL` path rejects any host argument whose concrete type is not `int` with `TYPE_TRAP`;
- the current `HOSTCALL_SIGNATURES` table exposes only the Int request-id process contract on product main.

Therefore `Bytes` can cross Clay functions inside CLAYVM/2 but cannot cross the canonical VM -> host capability boundary. This blocks a shared prerequisite for real CM-NET byte I/O, external CM-DATA ingress/egress, visual/video payload transport and audio payload transport.

Open PR #744 explores a narrow String process-path hostcall and explicitly leaves general Bytes/streaming open. This work item must not duplicate that PR's String/process semantics.

## Leading mechanisms

### A. Typed scalar ClayValue hostcall transport

Widen only the generic VM hostcall transport from `Int -> Int` to an admitted `ClayValue` argument/result surface, while keeping each hostcall's exact parameter/return types in the canonical `ExecutableIR` signature table. The host adapter must validate the exact contract and fail closed.

Advantages:
- smallest reuse of existing CLAYVM/2 `Bytes` value semantics;
- no new network/media semantics minted in the VM;
- enables a deterministic Bytes echo/no-op host adapter as a transport-only discriminator;
- keeps capability identity separate from payload value.

Risk:
- owned `bytes` implies copies for some adapters and is not yet the final zero-copy/high-bandwidth Buffer design.

### B. First-class Buffer/lease resource

Introduce a typed Buffer/BufferHandle resource with explicit owner, lifetime, lease/epoch and mutability semantics before any host boundary carries large payloads.

Advantages:
- structurally aligned with low-copy CM-DATA/VIS/AUDIO goals.

Risk:
- substantially larger semantic expansion; current VM has no admitted first-class resource/handle type and this could stall basic canonical byte transport.

### C. Integer handle registry

Keep `OP_HOSTCALL` Int-only and pass integer IDs referring to out-of-VM byte buffers/requests.

This is acceptable only if the handle is itself promoted to an explicit typed Clay resource with declared ownership/lifetime/provenance semantics. A hidden backend dictionary keyed by arbitrary Int would move Bytes semantics outside Clay and is therefore rejected as the default solution.

## Strongest counterhypothesis

A direct owned-Bytes hostcall may become a performance dead end because high-bandwidth network/media paths need streaming, backpressure and low-copy buffer lifetime control. If a scalar Bytes transport causes unavoidable repeated copying or cannot express cancellation/partial I/O, it must remain a bounded bootstrap substrate rather than the final streaming contract.

## Cheapest discriminator — ordinary deterministic gate

Before attaching real network/device semantics, add a transport-only exact-signature hostcall candidate using already-owned immutable `Bytes`:

`test.bytes.echo.v0::(Bytes)->Bytes`

Required observations in an authorized isolated Vercel Sandbox:
1. source/type/effect/ExecutableIR signature identity is explicit;
2. CLAYVM/2 preserves the exact byte payload including NUL and non-UTF-8 bytes;
3. capability denial fails closed;
4. wrong argument type and wrong return type fail closed at the hostcall contract boundary;
5. legacy Int hostcalls remain unchanged;
6. no adapter/parser assigns semantics to the payload bytes;
7. deterministic exact-byte roundtrip and receipt identity are recorded;
8. unusual experiment count = 0 for this ordinary transport discriminator.

Do **not** call this CM-NET/CM-VIS/CM-AUDIO PASS. It proves only the shared canonical Bytes crossing needed by those workstreams.

## Promotion path after transport proof

- CM-NET: define explicit address/connection/timeout/cancellation/partial-I/O semantics at TypedIR before attaching DNS/socket/TLS adapters.
- CM-DATA: fuse the transport with the admitted ownership/epoch/stability rules and measure copies/allocations/latency/backpressure.
- CM-VIS: carry typed visual envelopes plus Bytes/Buffer payload without mandatory decode.
- CM-AUDIO: carry typed audio envelopes plus Bytes/Buffer payload without mandatory decode.

Streaming/resource semantics should then choose between owned Bytes chunks and a first-class Buffer/lease design using measured copy/latency evidence, not assumption.

## Coordination / outcome

No new product branch is opened by this work item because PR #787 currently owns the product-nearest exact-EntityOS lane and PR #744 owns overlapping generic hostcall/String work. Fuse the generic value-transport portion with the preferred refreshed hostcall implementation rather than maintaining parallel VM semantics.

Outcome: RETAIN as cross-capability canonical transport blocker and zero-experiment deterministic test obligation. Whole EntityOS acceptance remains open.
