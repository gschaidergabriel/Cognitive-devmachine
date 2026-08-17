# EntityOS transitive build dependency closure — bounded work item

Date: 2026-08-17
Program: CLAYVERSE_CLAY_MACHINE_ONLY / CLAY_MACHINE
Product boundary: one executable `EntityOS`
Trigger context: `go`
Execution classification: SOURCE / UPSTREAM-METADATA REVIEW WORK ITEM ONLY — not Vercel Sandbox acceptance evidence and not a new unusual experiment.

## Observed anchors

The active PR #787 now carries a versioned `requirements-entityos-build.txt` with direct pins:

- `lark==1.3.1`
- `pyinstaller==6.21.0`

and `requirements-test.txt` includes that file plus `pytest==9.1.1`.

The build-internal/full-pytest Vercel runners currently install these requirements with `uv pip install`. A previously observed isolated Vercel Sandbox resolved additional concrete packages for the PyInstaller build path, including:

- `altgraph==0.17.5`
- `packaging==26.3`
- `pyinstaller-hooks-contrib==2026.6`
- `setuptools==84.0.0`

alongside the direct `lark==1.3.1` and `pyinstaller==6.21.0` pins.

PyInstaller 6.21.0 upstream dependency metadata declares non-exact dependency ranges for Linux-relevant build dependencies, including `setuptools>=42`, `altgraph`, `packaging>=22`, and `pyinstaller-hooks-contrib>=2026.6`. PyInstaller's own installation documentation also states that when PyInstaller is pinned, `pyinstaller-hooks-contrib` should be pinned as well.

Therefore the current file is a pinned **direct dependency surface**, not a complete deterministic resolver closure. A future resolver run can legally select different transitive versions while all current static direct-pin checks still pass.

## Strong counterhypothesis / boundary

This does not prove that the current EntityOS artifact is non-reproducible. PyInstaller may still emit identical bytes across some admissible transitive-version changes, and the canonical twin-build gate catches divergence within one resolved environment.

The narrower gap is provenance/replay: the current build receipt and dependency preflight do not identify or fail closed on the exact transitive Python package set that participated in the freeze. A later build can silently use a different hooks/packaging/setuptools/altgraph resolution without violating the present direct-pin contract.

## Cheapest discriminators

1. In an isolated Vercel Sandbox, emit the complete installed Python distribution set and versions used by the freeze before network denial/build.
2. Repeat from a fresh exact source head/environment with the same direct requirements and compare the complete resolved set.
3. If any transitive version can drift while direct-pin preflight remains PASS, the direct-surface-is-closure hypothesis is rejected.
4. After introducing a reviewed lock/constraints surface, repeat and require exact package-set identity plus existing byte-identical `EntityOS` gates.

These are ordinary dependency/reproducibility controls. They must not consume or multiply the single reserved 2026-08-17 unusual experiment (`ATTESTED_SNAPSHOT_CONTENT_TAMPER_FAIL_CLOSED`).

## Proposed smallest canonical hardening

1. Rename claims/tests so the current two-package file is not called a complete closure until it is one.
2. Produce a reviewed, platform-scoped lock/constraints artifact for the admitted Linux/Python 3.13 EntityOS freeze environment, binding all resolver-selected Python distributions needed for the build/test path. At minimum adjudicate `pyinstaller-hooks-contrib`, `altgraph`, `packaging`, and `setuptools` in addition to direct pins.
3. Prefer immutable package artifacts/hashes or an equivalent fail-closed lock representation where the package tooling supports it; do not infer trust merely from package names/versions.
4. Bind the effective resolved package set (and lock/constraints digest) into the Vercel receipt/evidence for an exact artifact.
5. Keep Python patch version, `uv` version, relevant system freeze-toolchain versions/image identity, and network-policy transition in the evidence contract because Python-package locking alone is not the whole build environment.
6. Run full pytest and the canonical one-file EntityOS build/runtime/relocation/provenance gates from a fresh exact-identity Vercel Sandbox under the locked environment before promotion.

## Promotion rule

Do not claim deterministic dependency closure merely because `lark`, `pyinstaller`, and `pytest` match direct pins. Promotion evidence must identify the effective transitive build environment or otherwise prove an equally strong deterministic/fail-closed dependency contract.

Outcome: RETAIN as reproducibility/provenance hardening work item; no whole EntityOS PASS claim.