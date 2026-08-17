# EntityOS Python package artifact-hash authority frontier

Date: 2026-08-17
Program: CLAYVERSE_CLAY_MACHINE_ONLY / CLAY_MACHINE
Product boundary: exactly one executable `EntityOS`
Trigger context: `go`
Execution classification: PRIMARY-DOC RESEARCH / TEST-OBLIGATION DELTA ONLY. No new Vercel Sandbox execution and zero new unusual experiments.

## Current observed boundary

Exact Vercel Sandbox evidence exists for PR #787 head `92b629566452d8f45fd208fba943b823ddd37e8c`, including the reviewed resolved Python distribution version set. Descendant source work has since added an exact installed-distribution + requirements-byte lock verifier and binds the build requirements-lock digest into the v7 receipt.

That is stronger than direct version pins, but it does **not** yet bind package supply to exact downloaded wheel/sdist bytes. Two index artifacts can share the same package/version while having different bytes and platform tags. Therefore version-set equality is not by itself package artifact authority.

## Primary upstream evidence

Current uv CLI documentation states that `--require-hashes` requires a matching hash for every requirement; all requirements must be exactly pinned or direct URLs. uv also documents `--generate-hashes` for including distribution hashes in generated output, and `--only-binary` to reject source-distribution builds. The uv docs further state that hash checking is all-or-nothing when required.

PyPI exposes SHA-256 per uploaded distribution. As one concrete current example, PyInstaller 6.21.0 publishes `pyinstaller-6.21.0-py3-none-manylinux2014_x86_64.whl` with SHA-256 `605169523a6b5ace39f13dfbff21add9f2bc43df99c7daf9394fefb2c45e8b6f`.

Primary sources consulted:
- https://docs.astral.sh/uv/reference/cli/ (`--require-hashes`, `--generate-hashes`, `--only-binary`)
- https://docs.astral.sh/uv/reference/settings/ (`require-hashes` all-or-nothing semantics)
- https://pypi.org/project/pyinstaller/6.21.0/ (distribution filenames and SHA-256 values)

## Alternatives

### A. Generated multi-hash requirements lock

Use `uv pip compile --generate-hashes`, then install with `uv pip install --require-hashes`.

Benefit: small delta and upstream-supported hash validation.

Counterhypothesis: if a requirement authorizes several hashes for the same version, the lock proves membership in an allowed artifact set, not one exact artifact identity. That may be acceptable for a portability policy but is weaker than an exact release-build artifact receipt.

### B. Platform-scoped exact wheel artifact lock — preferred next discriminator

For the admitted Vercel build platform/Python ABI, commit a canonical machine-readable lock that binds for every build/test distribution:
- normalized package name;
- exact version;
- exact wheel filename;
- exact SHA-256;
- wheel/platform tags or explicit `py3-none-any` identity;
- source index authority;
- lock schema/version and canonical lock digest.

Provision with hash enforcement and binary-only policy (`--require-hashes` plus `--only-binary :all:` or equivalent exact wheel-file installation). Require exactly one admitted artifact hash per package for the scoped build environment unless a broader portability set is explicitly part of the contract.

Benefit: closes version-equality ambiguity and avoids arbitrary sdist build code during package provisioning.

Risk/counterhypothesis: an over-specific x86_64 lock can accidentally become a hidden portability assumption. Therefore platform-scoped locks must be explicit and final EntityOS portability claims require separate admitted-platform artifacts/tests rather than silently widening hashes.

### C. Staged hash-bound wheelhouse

Resolve/download the admitted wheels in a bounded staging step, record filename+SHA-256 manifest, transfer that exact wheelhouse into the isolated Sandbox, verify all wheel bytes before install, then perform install/tests under `DENY_ALL`.

Benefit: strongest replay boundary and removes live-index choice from the test phase.

Cost: extra staging substrate and more bytes. It should be justified if option B cannot expose and receipt the exact selected artifact bytes strongly enough.

## Cheapest ordinary discriminator

When Vercel accepts a Git-bound descendant again, extend the existing dependency lane without adding a new unusual experiment:

1. Build a platform-scoped hash lock for the exact six build distributions and exact ten full-pytest distributions.
2. Require hash-checking mode for every package and reject un-hashed requirements.
3. Prefer wheel-only installation for the admitted Linux x86_64/Python 3.13 sandbox scope.
4. Emit a receipt containing the canonical lock SHA-256 and the exact admitted artifact filename/SHA-256 set.
5. Verify the installed distribution set as already implemented; both artifact-byte authority and installed-set equality must pass.
6. Deterministic negative controls: wrong hash fails closed; missing hash fails closed; extra installed distribution fails closed; source-distribution substitution fails closed under wheel-only policy.
7. Preserve `new_unusual_experiment_count=0`; these are ordinary supply-chain/provenance regressions.
8. Only after this gate passes should the exact EntityOS artifact receipt promote package dependency authority at that exact head/environment.

## Important non-equivalences

- exact package versions != exact package artifact bytes;
- `--generate-hashes` with multiple permitted artifacts != single-artifact identity;
- an index page SHA != proof that the Sandbox installed that artifact unless the install path is hash-enforced and the receipt binds the chosen artifact;
- exact package artifact authority != whole EntityOS acceptance.

## Coordination / outcome

Do not open a second EntityOS build lane while PR #787 owns the product-nearest provenance path. Fuse this artifact-hash gate into the refreshed #787 successor after the current regression-only descendant obtains exact-head Vercel execution or when the owner lane explicitly takes the package-authority delta.

Outcome: RETAIN as the next package supply-chain authority discriminator. Whole EntityOS / Clay Computer acceptance remains open.
