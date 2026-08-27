# GO research delta — PYTHONPATH can reintroduce CWD shadowing under `-P`

**Date:** 2026-08-14T14:14+07:00  
**Organ:** temporary Clay worker / GPT-5.6 Sol  
**Program:** `FRANK_V0_1`  
**State:** CANDIDATE / LOCAL_REPRODUCED; accepted-VPS productive-path confirmation still OPEN

## R0 anchors

- Current accepted-VPS replication receipt: `gschaidergabriel/Dr.-Unterweger/runtime/vps_integrity/clay_import_path/runs/31778957750.json` (commit head observed `12eb0dd1301793298710e643da8f035a7454ba3d`).
- In that bounded replication, `actual_script_current_controls` resolves the shadow module from `SCRIPT_DIR_SHADOW` in 20/20 repetitions with `safe_path=false`.
- The paired `actual_script_python_safe_path` arm resolves from `EPHEMERAL_DEPS` in 20/20 with `safe_path=true`.
- This receipt is a replication/probe on the accepted VPS, not evidence that the exact productive Frank launcher is already hardened.
- CPython documentation states that `-P` stops the interpreter from prepending the potentially unsafe script/CWD entry; `PYTHONPATH` separately augments the module search path. `-E` ignores `PYTHON*` variables and `-I` implies `-E`, `-P`, and `-s`.

Primary references:
- https://docs.python.org/3.14/using/cmdline.html
- https://docs.python.org/3.14/library/sys.html

## Generated reality / hypothesis

`-P` is necessary for the observed script-directory-shadow failure, but it is not a sufficient import-integrity boundary if an inherited or attacker-influenced `PYTHONPATH` can explicitly reintroduce CWD (for example `.` or an empty path element).

## Strongest counter-reality

`-P` suppresses CWD strongly enough that explicit/empty `PYTHONPATH` elements cannot put CWD ahead of trusted dependencies.

## Exactly one bounded unusual experiment

Local disposable three-arm experiment, Python `3.13.5`, using a CWD shadow module (`CWD_SHADOW`) and a trusted dependency module (`TRUSTED_DEPS`). All arms invoked `python3 -P`; temp files were deleted after measurement.

| Arm | PYTHONPATH | `safe_path` | Loaded marker | Outcome |
|---|---|---:|---|---|
| baseline | `<trusted_deps>` | true | `TRUSTED_DEPS` | control PASS |
| dot contamination | `.:<trusted_deps>` | true | `CWD_SHADOW` | hypothesis supported |
| empty-segment contamination | `:<trusted_deps>` | true | `CWD_SHADOW` | hypothesis supported |

Observed local `sys.path` in both contaminated arms contained the experiment CWD before the trusted dependency path while `sys.flags.safe_path == true`.

## Collapse

**Outcome: RETAIN.** The counter-reality was falsified in the local runtime. `safe_path=true` is not by itself evidence that CWD is absent from `sys.path`; provenance of all search-path contributors matters.

## FRANK_V0_1 implications

Affected invariants/components: F-V01-02 ClayCode runtime boundary, F-V01-09 effect authority (trusted code execution boundary), F-V01-13 security/recovery/observability.

Candidate hardening directions, to be discriminated rather than assumed:

1. Productive launcher uses isolated mode (`-I`) where compatible, or otherwise `-P` plus explicit sanitization/allowlisting of `PYTHONPATH` and other startup path contributors.
2. Runtime startup receipt records `sys.flags.safe_path`, effective `sys.path`, relevant environment-policy decision, interpreter identity, and imported critical-module origins.
3. Fail closed if a consequential runtime resolves critical modules outside the attested allowed roots.

## Next falsifier / promotion requirement

On the exact accepted productive Frank launch path, inject a bounded inherited `PYTHONPATH` contamination (`.` and empty segment) and prove one of:

- the launcher strips/rejects it before interpreter startup; or
- isolation makes it ineffective; or
- an equivalent machine-checked mechanism prevents critical-module resolution from untrusted roots.

Then restart/replay the exact runtime and confirm the same result with provenance-bound receipts. Until then this finding does **not** promote release acceptance and does not close F-V01-13.

## Negative/uncertain evidence preserved

- Repository code search during this cycle returned no matches for `PYTHONPATH`, `PYTHONSAFEPATH`, or `python3 -P` in the searched current alias repo; this is a search observation, not proof that no runtime wrapper or external service configuration performs equivalent sanitization.
- The unusual experiment was local, not accepted-VPS productive-path evidence.
- No final model training was authorized or started.
