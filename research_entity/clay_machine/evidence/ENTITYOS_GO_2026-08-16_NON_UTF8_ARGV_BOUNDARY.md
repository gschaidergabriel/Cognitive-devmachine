# EntityOS go evidence — non-UTF8 argv boundary

Date: 2026-08-16
Worker role: temporary Clay research organ

## R0 observed evidence — first exact artifact

Product repo observed HEAD at first test: `d4fc929d33c69ecd61524d6f620d92b165aafbe7`
Exact workflow artifact: `EntityOS Canonical One-File VPS` run `31929090825`, artifact id `9258876082`
Exact tested executable SHA-256: `fade26ac184bc857fbb5e984d62d71347709ef8dc8ad72d54dec3fa6fd2e8f98`
Artifact size: `12820496` bytes

Deterministic checks observed:

- `EntityOS --self-test-json`: PASS; ClayCode -> ClayExecutableTypedIR/v1 -> ClayVMArtifact/v1 -> ClayVM -> ClayOS pipeline reported; VM arithmetic result 42; effect-gated VM process probe PASS; UnifiedDB grounding checks PASS.
- host process without `linux.process.spawn.v0`: denied as expected.
- host process with explicit `linux.process.spawn.v0`: `/usr/bin/printf` executed and returned expected output.
- artifact SHA-256 remained `fade26ac184bc857fbb5e984d62d71347709ef8dc8ad72d54dec3fa6fd2e8f98` after tests.
- naked first-launch in this sandbox reached the initial-grant GUI path but failed with `ENTITYOS_X11_DISPLAY_OPEN_FAILED` because no X11 display was available. This is local-environment evidence, not a claim about the accepted VPS.
- the embedded build receipt states `whole_machine_acceptance=false`.

## R0 refresh — current b32 artifact

During this go cycle the product main advanced to `b32ec5a5f577099f90d74a038b5e3aee4db0c43e` (`fix(entityos): probe X11 reachability before GUI boot`). The current-head `EntityOS Canonical One-File VPS` run `31929651652` completed successfully and produced artifact id `9258908699`.

The exact current-head artifact was downloaded and the executable tested locally:

- exact executable size: `12820848` bytes;
- exact executable SHA-256: `1a65554a6bc3a8c79c1eb033714c013e76a52d26877eb88c0349da4b72ff19e1`;
- embedded build receipt: two reproducibility builds, SHA-256 match true, `pyinstaller_onefile=true`, `whole_machine_acceptance=false`;
- `EntityOS --self-test-json`: PASS at build head `b32ec5a5f577099f90d74a038b5e3aee4db0c43e`;
- host process without `linux.process.spawn.v0`: denied fail-closed;
- host process with the capability: `/usr/bin/printf` executed and returned expected output;
- exact executable SHA-256 remained unchanged after tests.

A transient apparent hash discrepancy was resolved by source inspection: `artifact_sha256` in `EntityOSSelfTest/v1` is returned from the temporary canonical `build_file(...)["artifact_sha256"]` ClayVM artifact built by the self-test, not from the outer EntityOS executable. The executable identity is the separate build-receipt `sha256`, which matched the tested file exactly. No EntityOS binary identity mismatch is claimed.

Current b32 source inspection still shows the effectful TypedIR process probe carries an integer request identifier while the actual process `argv` is materialized in `HostProcessVMHost.requests` as a `VMProcessRequest`. Therefore a green process probe does not establish canonical Clay String/Bytes/argv semantics.

## Hypothesis

A canonical Clay process/data boundary needs explicit Clay String/Bytes (and later Buffer) values to traverse TypedIR and the single VM, with ownership/provenance and effect signatures bound before ClayOS host execution.

## Strongest counterhypothesis

The existing host substrate may already preserve arbitrary Unix argument bytes well enough that explicit Clay Bytes semantics are unnecessary for process interoperability.

## Exactly one bounded unusual experiment for this go cycle

Experiment: `NON_UTF8_ARGV_SURROGATEESCAPE_BOUNDARY`

Provenance: executed against the exact `d4fc929d33c69ecd61524d6f620d92b165aafbe7` artifact before product main advanced to b32. No claim is made that the intervention was rerun on b32.

Baseline:

- invoke the exact EntityOS binary via a bytes-valued Python subprocess argv;
- grant `linux.process.spawn.v0`;
- execute `/usr/bin/printf` with ASCII payload `ASCII`;
- observed rc=0 and stdout hex `4153434949`.

Intervention:

- same bounded command, but final argv byte payload is the invalid UTF-8 byte `0xff`;
- observed rc=0, stdout hex `ff`, stderr empty.

Rollback / persistence:

- no persistent state mutation was required by the experiment;
- only `/usr/bin/printf` was spawned;
- exact EntityOS executable was not modified.

## Collapse

Outcome: **RETAIN counterevidence / semantic constraint**.

The counterhypothesis is partly supported at the host-substrate level: Unix/Python can round-trip an opaque non-UTF8 byte through argv. That success is precisely why host behavior cannot be promoted to Clay language semantics. The current b32 process probe can pass while canonical Clay Bytes/String/argv remain absent from TypedIR/VM.

This is a negative anti-Goodhart result: host interoperability success is not evidence that the language/runtime owns the semantics.

## Next discriminating build/test action

Implement the smallest canonical value path that carries at least one Clay `String` or `Bytes` argv value through parser/type/effect checking -> `ClayExecutableTypedIR/v1` -> serialized `ClayVMArtifact/v1` -> single ClayVM -> ClayOS process boundary, without an out-of-band host request table supplying the argument payload.

Required first tests:

1. ASCII argv survives the canonical value path.
2. opaque/non-UTF8 bytes either survive as an explicit Clay `Bytes` value or are deterministically rejected by the declared `String` contract; no implicit host decoding decides semantics.
3. capability/effect denial remains fail-closed.
4. serialization/replay preserves value bytes, type, provenance, and effect binding.
5. exact one-file `EntityOS` is rebuilt and the exact rebuilt artifact repeats the tests on Ubuntu/VPS.

Promotion rule: do not mark CM-TERM/CM-DATA process-byte semantics PASS merely because the host adapter or Python runtime can transport the bytes.