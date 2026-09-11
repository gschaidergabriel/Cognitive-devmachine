# POINTER — where the Round 2 package actually lives

This branch (`chatgpt-vps-work/frank-avatar-handoff-round2`) carries only the
lightweight report/checksum docs. The full package — screenshots (before/after UI,
eye-glow zoom, live-roll-test frames), a live DOM dump, console log, and the touched
source files (`buehne.html`, `filmlook.js`, `buehne_daemon.py`) — is a 7.4 MB tarball
that was built and verified inside the `clay-direct-dev` sandbox but could not be
pushed to GitHub from there (see `ROUND2_REPORT.md` section 6, "Offener Blocker", and
`research_entity/coordination/AVATAR_HANDOFF_STATUS.md` on `main` of this repo for the
full diagnosis). It sits as a plain file drop instead:

    Host path:    /srv/claylab/artifacts/frank-avatar-handoff-round2/ROUND2_EXPORT_20260911T193830Z.tgz
    Sandbox path: /artifacts/frank-avatar-handoff-round2/ROUND2_EXPORT_20260911T193830Z.tgz
                  (visible inside the clay-direct-dev container at that exact path)

    bytes:  7415457
    sha256: 1b9d861faa07f9f65b88a460bc5c377de8e7c4f751b7f53ab88e3710beb8ed18

To open it inside the sandbox:

    podman exec -it clay-direct-dev bash
    cd /artifacts/frank-avatar-handoff-round2
    sha256sum -c ROUND2_EXPORT_20260911T193830Z.tgz.sha256
    tar tzf ROUND2_EXPORT_20260911T193830Z.tgz | head
    tar xzf ROUND2_EXPORT_20260911T193830Z.tgz -C /workspace/

Inside the tarball: `ROUND2_REPORT.md` (byte-identical to the copy alongside this
file), `SHA256SUMS.txt`, `SOURCE/{buehne.html,filmlook.js,buehne_daemon.py}`,
`EVIDENCE/screenshots/*`, `EVIDENCE/dom/{dom_dump_after.html,console_after.log}`,
`EVIDENCE/live_roll_test/*` (the 6-frame pixel-measurement raw data referenced in the
report).

For the live, running app itself (not a static export), use the local bridge —
see `research_entity/coordination/LOCAL_BRIDGE_PROTOCOL.md` on `main` of this repo.

Round 1 (env truth + full inventory, predecessor to this round):
`chatgpt-vps-work/frank-avatar-handoff-round1`, commit `2cb05a83b1f6cd3fae6973c6fdb625079ad19e0d`.
