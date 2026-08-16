# GO 2026-08-16 — raw Linux pathname bytes vs strict Clay String

Status: **SUPPORTED NARROW COUNTER-REALITY / ARCHITECTURE EVIDENCE**  
Program: `CLAYVERSE_CLAY_MACHINE_ONLY`  
Stage: `CLAY_MACHINE`  
Authority/effects: none  
Execution boundary: isolated local ChatGPT sandbox only  
New unusual experiments in this GO macro-cycle: **exactly 1**

## Observed anchors

- Product main observed before the experiment: `7eb7fc63d38c910c2bdb9c80ec32908e0b0866fe`.
- Active String-path candidate: PR #744, exact candidate head `81f1b99c70af56d9459d81190a1244484748d32f`.
- PR #744 deliberately defines only `linux.process.spawn.path.v1::(String)->Int`; it does not claim general argv/Bytes/path-byte totality.
- Current `ClayVM/1` String constants use strict UTF-8 encoding/decoding.
- Current canonical host-process boundary accepts `Sequence[str]`, rejects NUL, requires an absolute executable pathname, and uses `shell=False`.
- Parallel PR #741 separately explores typed `Bytes` through `CLAYVM/2`; it must remain semantically distinct from String/argv work until canonically composed.

## Generated reality / hypothesis

A strict UTF-8 Clay `String` may be sufficient as the sole canonical representation for Linux executable paths.

### Strongest counter-reality

Linux/POSIX pathnames are byte sequences rather than guaranteed Unicode strings. A legal pathname can contain a non-UTF-8 byte while excluding only NUL and `/` within a filename component. Therefore a strict UTF-8 String-only path contract cannot represent the entire Linux pathname space losslessly.

## Primary-source basis

- POSIX Base Definitions, Filename: a filename is a sequence of bytes; NUL and `/` are excluded from filename bytes: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap03.html
- POSIX.1-2024 rationale/definitions retain the byte-sequence model for filenames/pathnames: https://pubs.opengroup.org/onlinepubs/9799919799/xrat/V4_xbd_chap01.html
- Python `os` filesystem encoding guidance documents `surrogateescape` for undecodable filesystem bytes and round-tripping them back to bytes: https://docs.python.org/3/library/os.html#file-names-command-line-arguments-and-environment-variables

## Exactly one bounded unusual experiment

`RAW_LINUX_PATH_BYTE_NOT_REPRESENTABLE_AS_STRICT_CLAY_STRING`

Disposable sandbox procedure:

1. Create a normal executable filename and verify direct execution.
2. Create a second executable whose filename contains raw byte `0xff`.
3. Execute the raw-byte pathname directly with `shell=False`.
4. Decode the pathname through the host filesystem codec (`os.fsdecode`) and test strict UTF-8 re-encoding.
5. Remove the disposable directory.

Measured result:

```json
{
  "baseline_utf8_path_exec_rc": 0,
  "experiment": "RAW_LINUX_PATH_BYTE_NOT_REPRESENTABLE_AS_STRICT_CLAY_STRING",
  "fsdecoded_contains_surrogate": true,
  "new_unusual_experiment_count": 1,
  "raw_invalid_utf8_bytes_path_exec_rc": 0,
  "result": "STRING_PATH_NOT_TOTAL_FOR_LINUX_PATHSPACE",
  "strict_utf8_reencode": "REJECT:UnicodeEncodeError"
}
```

Rollback: complete deletion of the disposable temporary directory. No repository, VPS, provider, production, canonical state, Harness, or effect authority was touched.

## GRF collapse

- `strict UTF-8 String is a total representation of Linux pathname space` -> **REJECT**.
- `PR #744 is invalid because it uses String` -> **REJECT**. The PR is explicitly a narrow path-only String candidate and makes no total-pathspace claim.
- `String and Bytes should be collapsed into one undifferentiated scalar before semantics are fixed` -> **REJECT / DEFER**.
- `retain PR #744 as a bounded UTF-8/textual pathname surface while preserving an owned Bytes/PathBytes route for lossless filesystem identity if full Linux pathspace is required` -> **RETAIN as architecture candidate**.
- `full Linux interop requires raw PathBytes` -> **DEFER** pending explicit product policy: either (a) full POSIX pathname byte coverage or (b) a deliberately narrower UTF-8-only EntityOS pathname contract.

## Affected gates

- CM-DATA: canonical Bytes/Buffer ownership and lifetime.
- CM-TERM: String/argv/process semantics and typed Linux interoperability.
- ClayVM value contract: type-distinct String vs Bytes transport.
- EntityOS one-file release boundary: filesystem/process interoperability must not silently claim broader pathname support than the admitted semantic contract.

## Next discriminator

After the current sandbox-only workflow-trigger isolation repair is complete, run **ordinary** (zero-new-unusual-experiment) exact-head sandbox regressions that prove:

1. PR #744 accepts only its declared String signature and all host handlers retain exact fail-closed argument typing;
2. Bytes remain type-distinct and cannot be accidentally accepted by String hostcalls;
3. the chosen pathname policy is explicit: UTF-8-only restriction with deterministic rejection, or a separate owned lossless `PathBytes` boundary;
4. the same reviewed bytes rebuild and self-test the exact one-file `EntityOS` candidate in an allowed isolated sandbox.

## Non-claims

No PR #744 promotion. No PR #741 promotion. No whole Clay Machine acceptance. No current EntityOS artifact verification. No VPS/self-hosted evidence is admitted. No final/model training authorization. No external effect authority.
