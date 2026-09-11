# POINTER — where the big binary package actually lives

This branch (`chatgpt-vps-work/frank-avatar-handoff-round1`) carries only
the lightweight docs/inventory (text/JSON/CSV). The full package —
including 1,340 active avatar asset PNGs (656 MB) plus Gabriel's own
BASELINES/MOCKUPS/TARGET_VISUALS/CONTRACTS/QA reference material from
FRANK_CLAUDE_HANDOFF_GUIDE_V2 — is too large for a sane git push, so it
sits as a plain file drop in the already-established artifacts bridge
location instead:

    Host path:    /srv/claylab/artifacts/frank-avatar-handoff-round1/COMBINED_HANDOFF_20260911T184549Z.zip
    Sandbox path: /artifacts/frank-avatar-handoff-round1/COMBINED_HANDOFF_20260911T184549Z.zip
                  (visible inside the clay-direct-dev container at that exact
                  path -- verified: `podman exec clay-direct-dev ls -la /artifacts/frank-avatar-handoff-round1/`)

    bytes:  719712890
    sha256: 03ad0dd38ba2cb3b09f01b3b38496e5acda9b700d4979e7ee28cf334f0b7d6d1
            (verified identical on the local build machine AND after the
            transfer landed on the VPS -- both sides match)

To open it inside the sandbox:

    podman exec -it clay-direct-dev bash
    cd /artifacts/frank-avatar-handoff-round1
    sha256sum -c COMBINED_HANDOFF_20260911T184549Z.zip.sha256
    unzip -l COMBINED_HANDOFF_20260911T184549Z.zip | head
    unzip COMBINED_HANDOFF_20260911T184549Z.zip -d /workspace/frank-avatar-handoff-round1/
    # (extracts into /srv/claylab/workspace/frank-avatar-handoff-round1/ on
    #  the host, i.e. real, persistent, git-independent scratch space)

Inside the zip, start with `README_COMBINED.md`, then
`ROUND1_EXPORT_20260911T184549Z/README_FIRST.md` and
`ROUND1_EXPORT_20260911T184549Z/ACTIVE_RUNTIME_MAP.md`.

This branch's own docs (README_FIRST.md, ACTIVE_RUNTIME_MAP.md, RUNBOOK.md,
HANDOFF_READY.json, INVENTORY.csv) are byte-identical copies of the ones
inside the zip's `ROUND1_EXPORT_20260911T184549Z/` folder -- duplicated here on
purpose so the git-based channel is self-contained for reading without
needing to unzip anything first.
