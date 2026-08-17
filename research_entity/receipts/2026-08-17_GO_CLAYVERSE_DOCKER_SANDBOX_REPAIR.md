# GO ClayVerse Docker-in-Sandbox repair receipt — 2026-08-17

Trigger: `go`

## Scope

This receipt corrects the current ClayVerse OCI execution frontier only. It does not claim whole-product PASS and does not authorize VPS testing.

## Empirical predecessor

Vercel deployment `dpl_9Q28fMrNLwGkSwWJZx342duTyuwT` executed the existing build-internal ClayVerse Sandbox gate from `gschaidergabriel/Dr.-Unterweger` branch `clay/go-clayverse-container-sandbox-20260817` at commit `efde98e8406f920aa9626da00a72afe77e509ed8`.

Observed evidence from that deployment:

- exact staged research source: `edaee6307c56669819164cd95b0f2dbca0985e1e`;
- exact staged artefact tree: `35ca41cf1ac44a61eab2222c60ff65519156172a`;
- 30-file source closure with Git-blob verification PASS;
- source TAR materialization inside a real Vercel Sandbox PASS;
- source TAR SHA-256: `11ec60a63c2c75faca558e324948b12a6397d6e725880e5bbbbec47a278dd1d6`;
- Sandbox execution then failed only at `dnf install -y podman` because Amazon Linux 2023 returned `No match for argument: podman`;
- Sandbox stop was observed successful.

## Repair discriminator

Current Vercel documentation explicitly supports Docker inside Vercel Sandbox using:

1. `dnf install -y docker` with sudo;
2. detached `dockerd` with sudo;
3. wait for `sudo docker info` before container commands.

Vercel also supports starting Sandboxes directly from custom OCI images stored in Vercel Container Registry. Therefore Podman is not an architectural requirement for the ClayVerse isolated container gate.

The existing infrastructure branch was repaired without changing the reviewed source-staging or ClayVerse test logic:

- `4a5adaa6bc7eceb632e8a797aedbce67ed204467`: add fail-closed Docker runtime substitution wrapper;
- `73ed538995b8427e14f6c64cffec9622d887613f`: make the branch Vercel build run that wrapper;
- wrapper requires base runner Git blob `ee0f95104abd35e56cba9601dcf03584ee99a0a5` exactly;
- exactly four runtime substitutions are admitted: Podman package install -> Docker install/daemon, OCI build -> Docker build, image identity -> Docker inspect, runtime probe -> Docker run;
- any base-runner drift or substitution-cardinality drift fails closed;
- classification is infrastructure regression only; no new unusual experiment is added.

## Current execution blocker

The Git/Vercel integration saw repaired branch commit `73ed538995b8427e14f6c64cffec9622d887613f`, but its GitHub `Vercel` status is currently `failure` with target indicating `build-rate-limit` / upgrade-to-Pro. No new Vercel deployment exists for the repaired branch revision yet.

Therefore:

- `DOCKER_REPAIR_SOURCE_READY`: YES;
- `REPAIRED_VERCEL_SANDBOX_EXECUTED`: NO;
- `REPAIRED_DOCKER_GATE_PASS`: UNEXECUTED;
- `CURRENT_BLOCKER`: VERCEL_BUILD_RATE_LIMIT;
- no repeated deployment attempts should be generated while the rate limiter is the active discriminator.

## Current ClayVerse head relation

The canonical research main advanced beyond the predecessor `edaee...` candidate during this macro-cycle. The current artifact remains a single OCI/Docker-compatible ClayVerse image, with a newer Dockerfile including the persistent terminal pivot, managed Claude policy, and staged digest-bound EntityOS substrate. Any PASS from the repaired predecessor runner would prove the Docker-in-Sandbox infrastructure path only; it must not be generalized to the newer current research head.

## Next exact step

When Vercel accepts another preview build, run the repaired Docker gate once. If Docker provisioning/daemon/build/runtime succeeds, promote that infrastructure result only, then restage the exact then-current ClayVerse head and execute the full coordinated current-head Sandbox suite/container/restart/two-user gates. If Docker itself fails, persist the exact Sandbox failure and use Vercel custom-image/VCR boot as the next supported discriminator instead of returning to Podman guessing.
