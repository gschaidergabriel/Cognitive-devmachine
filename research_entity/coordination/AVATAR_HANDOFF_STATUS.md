# Avatar Handoff Status — FranKenstein `buehne.html` / `buehne_daemon.py`

Canonical, always-check-here status for the avatar-redesign work ChatGPT-FranKenstein
is doing. This file lives on **`main`** of `gschaidergabriel/clay-global-research-entity`
(not a feature branch) precisely so any agent that checks this repo's default branch
finds it without hunting through branches. Written 2026-09-12 by the architect agent
that resolved a GO-GATE-0 block caused by ChatGPT looking in the wrong repo
(`gschaidergabriel/frankenstein` instead of this one — see
`AI_START_HERE_DO_NOT_SCAN_REPO/ARTIFACTS/AVATAR_AND_COORDINATION_POINTER.md` in that
repo for the pointer that now prevents the same confusion).

## Three-repo map (read this once, stop guessing which repo)

| Repo | Role | Avatar handoffs live here? |
|---|---|---|
| `gschaidergabriel/frankenstein` | Plugin/distribution repo + install routing (`AI_START_HERE_DO_NOT_SCAN_REPO/`) + `bridge-kit` reference architecture | **No** — code/plugin only, now carries a pointer to this repo |
| `gschaidergabriel/frankenstein-2.0` | F2WP1207 GRID10-cognition research/build (separate subject entirely) | No |
| `gschaidergabriel/clay-global-research-entity` (**this repo**) | Coordination hub: `research_entity/`, `chatgpt-vps-*`/`chatgpt-local-*` bridge branches, autonomous research state | **Yes** |

## The live app itself

- Process: `buehne_daemon.py`, systemd user unit `frankenstein-buehne.service`,
  `127.0.0.1:8788` on **ai-core-node**.
- Directory: `/home/ai-core-node/.claude/star/visual/` — **not a git repo**. That is why
  the handoffs below are file-drop exports/branches, not a normal repo clone.
- Frontend: `buehne.html` + `filmlook.js` (vanilla HTML/CSS/JS).

## Round 1 — environment truth + full inventory (COMPLETE, on GitHub)

- Branch: `chatgpt-vps-work/frank-avatar-handoff-round1`
- Commit: `2cb05a83b1f6cd3fae6973c6fdb625079ad19e0d` (2026-09-11T19:05:27Z) — verified via
  `gh api repos/gschaidergabriel/clay-global-research-entity/commits/2cb05a83...`.
- Lightweight docs on that branch: `handoff/frank-avatar-round1/` (`README_FIRST.md`,
  `ACTIVE_RUNTIME_MAP.md`, `RUNBOOK.md`, `HANDOFF_READY.json`, `INVENTORY.csv`,
  `POINTER.md`, `ROUND1_EXPORT_SHA256SUMS.txt`, `README_COMBINED.md`).
- Full binary package (too large for git, per `POINTER.md` on that branch):
  - Host path: `/srv/claylab/artifacts/frank-avatar-handoff-round1/COMBINED_HANDOFF_20260911T184549Z.zip`
  - Sandbox path (inside `clay-direct-dev`): `/artifacts/frank-avatar-handoff-round1/COMBINED_HANDOFF_20260911T184549Z.zip`
  - bytes: `719712890`
  - sha256: `03ad0dd38ba2cb3b09f01b3b38496e5acda9b700d4979e7ee28cf334f0b7d6d1`
  - Contains, among other things: `QA/ACCEPTANCE_TESTS.md`, `BASELINES/BASELINE_PROTOCOL.md`,
    `BASELINES/dream_target_metrics.json`, `CONTRACTS/animation_contract.json`,
    `CONTRACTS/layout_contract.json`, `RESEARCH/EMPIRICAL_DREAM_TARGET.md`,
    `CODE_REFERENCE/visual_gate.py`, `CODE_REFERENCE/runtime_probe.js`,
    `CODE_REFERENCE/background_loop_gate.py`, `CODE_REFERENCE/verify_handoff.py`,
    `TARGET_VISUALS/`, `MOCKUPS/`, `PROMPTS/01_CLAUDE_FIRST_HANDOFF_ONLY.txt`,
    `PROMPTS/04_CLAUDE_DREAM_TARGET_BUILD.txt`.
- Key finding from Round 1: the assumption that the avatar app lives in
  `/home/ai-core-node/frankenstein-repo` was **wrong** — that repo is the unrelated
  GRID10-cognition project. The real app is the non-git directory above.
- `HANDOFF_READY.json` on that branch: `completeness: false`, honestly, only because
  video capture / rAF-performance trace / full CDP console capture were not done —
  everything else in the round-1 checklist is `pass`.

## Round 2 — real root-cause fix, built + tested 2026-09-11/12

**Status as of this writing: built and verified locally, exists ONLY as a file on the
VPS — it was NOT reachable via git until this status update, because the agent that
built it (running inside the `clay-direct-dev` sandbox as user `claylab`) hit a hard
permission wall pushing to GitHub.** See "Round 2 git-push blocker" below for the
verbatim diagnosis from that agent's own report — this is a real, documented
limitation, not an oversight to silently repeat.

- Source artifact: `/srv/claylab/artifacts/frank-avatar-handoff-round2/ROUND2_EXPORT_20260911T193830Z.tgz`
  (sandbox path: `/artifacts/frank-avatar-handoff-round2/ROUND2_EXPORT_20260911T193830Z.tgz`)
  - bytes: `7415457`
  - sha256: `1b9d861faa07f9f65b88a460bc5c377de8e7c4f751b7f53ab88e3710beb8ed18`
- Lightweight docs now mirrored to git (added by this status update, same
  lightweight-docs-not-binaries pattern as Round 1): branch
  `chatgpt-vps-work/frank-avatar-handoff-round2`, commit
  `c48211223e90496f65b435ce6f5840983e64e07e`, path `handoff/frank-avatar-round2/`
  (`ROUND2_REPORT.md` — the full report quoted/summarized below,
  `ROUND2_SHA256SUMS.txt`, `POINTER.md`). The screenshots/DOM-dump/source files stay in
  the 7.4 MB tarball on the VPS at the path/hash above — not re-uploaded to git, same
  reasoning as Round 1's 656 MB asset set (just smaller).

### What Round 2 actually fixed (real, verified — not "looks better")

- **Root cause of the long-standing "Doppelgesicht"/ghost-head bug**: the old flat,
  opaque `#gesicht`/`#gesicht2` layers (RGB, no alpha, z-index above the real RGBA head,
  different head position) were removed from DOM+CSS entirely. A single transform chain
  now governs the head (`#kamera → #gesicht-rahmen → #kopf-canvas → #kopf-dreh/
  #koerper-dreh`), with anatomically correct rotation origins
  (`#kopf-dreh{transform-origin:50% 58.59%}` = neck-vertebra anchor at (768,600) on the
  1536×1024 canvas; `#koerper-dreh{transform-origin:50% 100%}` = hip). Neck seam is now
  a soft mask gradient instead of a hard cut. Eye-glow/blink layers were moved inside
  `#kopf-dreh` so they rotate with the head instead of staying screen-fixed.
- Verified by: live DOM dump (`#kopf-schicht2` etc. carry no inline opacity override →
  CSS default `opacity:0` → exactly one visible head layer at capture time), a clean
  before/after screenshot pair showing no double-image even zoomed on the neck, and a
  console log free of real JS errors.
- **Honest self-correction inside the same report** (the coordinator pushed back on an
  initially-too-clean claim, and the agent re-measured rather than defend the first
  answer): the DOM-level unification is real and complete, but the head-roll rotation
  itself still runs via **photo-swap** (`kopfRollDatei()`, real ±5°-step photographs)
  while the eye-glow/blink layers use **live CSS transform** — the two mechanisms are
  kept in sync only by a hand-fitted compensation formula
  (`kopfRollAusgleichDeg`, constants `0.12/0.34/0.4`, fitted by eye against screenshots,
  already re-tuned three separate times for three different symptoms historically).
  This is flagged as the **actual architectural reason** avatar work has repeatedly
  stalled on this symptom class — fixing it means deriving one rotation/anchor model
  both mechanisms share, not patching the constant again. Not attempted this round
  (real regression risk against 3 already-passing fixes, correctly judged out of scope
  for the remaining session time) — **explicitly left open, see below.**
- Real pixel measurement (not "looks fine"): 6 frames of a live 15° roll pose, captured
  from the actual GPU kiosk window (not headless) via `xdotool`+`import -window`,
  eye-glow centroid tracked by numpy color-mask. Largest single-frame jump: 4.9px x /
  2.9px y; residual jitter afterward ≤2.3px x / ≤1.4px y. No two-digit-pixel jump
  reproduced in this sample (an earlier report had described one). Explicitly logged as
  `not_run` against the full formal Gate-0 protocol in `EMPIRICAL_DREAM_TARGET.md`
  (which wants many samples/angles/RMS) — this was one honest, real, but partial
  measurement, not a pass claim.
- UI-chrome pass (metal/smoke-glass/claymorphism per the `ChatGPT Image Sep 12...`
  reference): pure CSS/HTML, no anchor/transform/JS logic touched. Real
  connected/disconnected status dot wired to the existing `chatHolen()` error path (no
  new claim, just a visible signal for an already-real check).
- Eye-glow halation/bloom: `drop-shadow` filter on `#pupillen-glow`, follows the alpha
  channel so it stays inside the eye mask; opacity still strictly gated on
  `serverBlick.anwesend && .nah` (real face detection, not faked-on).
- Regression check: DOM dump clean after both changes; single visible head layer still
  confirmed; no anchor/transform/physics values changed by this round's own edits.

### What Round 2 explicitly did NOT do (honestly listed, not silently skipped)

| Not done | Why | Reusable groundwork already present |
|---|---|---|
| Real Depth-Anything-V2 4-layer depth parallax | Needs an offline model-inference pipeline; multi-hour task on its own | `kopf_rgba_parallax/` (12 files) exists but is **not wired** into `buehne_daemon.py`/`buehne.html` (0 hits for "parallax" in live code) — provenance of those 12 files not yet confirmed |
| Continuous local expression deltas (lids/brows/cheeks/jaw/lips/mouth/teeth/tongue) as a warp field | What exists are discrete photographed frames (12-frame blink, mouth keyframes), not a warp field; a real system needs its own small render pipeline | The discrete sets work and are already running as an accepted interim approximation |
| Formalized 100 Hz fixed-step physics with rAF interpolation | Springs/sequences currently run directly inside the rAF-driven `schleife(t)`; converting is an architecture refactor with regression risk for every existing motion | `runtime_probe.js` reference exists under `CODE_REFERENCE/` from Round 1, not yet integrated |
| 300-frame background loop-closure certification (optical flow) | No flow tool (RAFT/Farneback) wired into the project | `background_loop_gate.py` reference exists under `CODE_REFERENCE/`, not integrated |
| Full empirical gate matrix (LPIPS, RAFT, LoAF, VMAF, n=20 blind study) | Each is its own tool/model to install+calibrate against a baseline; realistically several sessions | `visual_gate.py`/`runtime_probe.js`/`background_loop_gate.py` templates already present in Round 1's `CODE_REFERENCE/` |

Every "not done" row above is marked `not_run` in the underlying report, never claimed
as `pass` — none of the `EMPIRICAL_DREAM_TARGET.md` thresholds are being claimed as met
by Round 2.

### Round 2 git-push blocker (why this file exists — verbatim diagnosis from the Round 2 agent)

> Local machine (`ai-core-node`): no SSH key with access to this GitHub repo
> (`Permission denied (publickey)`). VPS `root@72.61.19.188`: same error. VPS user
> `claylab` (own deploy key at `/home/claylab/.ssh/id_ed25519`): GitHub also rejects it
> with `Permission denied (publickey)` — consistent with the documented **read-only**
> deploy-key restriction for that sandbox. `gh` CLI on the VPS is installed but not
> logged in. The existing checkout
> `/srv/claylab/workspace/clay-global-research-entity` is additionally dirty
> (uncommitted changes in `free swarm/*`, `tools/run_research_distillery.py`) and was
> deliberately left untouched per the round's own instructions.

**Resolution applied by this status update (2026-09-12):** since neither the
`clay-direct-dev` sandbox nor VPS root has write access to this repo, the architect
agent doing this cleanup (which does have a working `gh`/git credential with `repo`
scope) copied Round 2's lightweight docs to `chatgpt-vps-work/frank-avatar-handoff-round2`
the same way Round 1's docs got onto GitHub — someone with real push access has to be
the one who lands it. **The 7.4 MB source tarball itself still lives only on the VPS
at the path/hash above** — this file and that branch are pointers to it, not a
re-upload of the binary.

## What's next (open, not started)

1. Unify the rotation/anchor model so head-roll (photo-swap) and eye-glow (live
   transform) derive from one declared model instead of a hand-fitted compensation
   constant — see "honest self-correction" above. This is the most likely fix for the
   repeated stall pattern across agents.
2. Confirm provenance of `kopf_rgba_parallax/` (12 files) before wiring it in — is it
   really Depth-Anything-V2 output or an older unrelated experiment?
3. Wire one gate at a time from `CODE_REFERENCE/` (`visual_gate.py` →
   `runtime_probe.js` → `background_loop_gate.py`), commit each independently, do not
   attempt all of `EMPIRICAL_DREAM_TARGET.md`'s gate matrix in one pass.
4. Full multi-angle/multi-sample Gate-0 measurement (the 6-frame/15°-only sample above
   is real but partial).

## Real, fresh measurement — not just static files

See `research_entity/coordination/LOCAL_BRIDGE_PROTOCOL.md` (this repo, `main`) for how
to get ChatGPT-FranKenstein a **live** answer instead of relying on the screenshots
above: `chatgpt-local-ai-core-node-control`/`-results` branches, `op: "screenshot"`
against the actually-running `buehne.html` on port 8788, plus `exec`/`read_file` to run
any of the `CODE_REFERENCE/` gate scripts or
`/home/ai-core-node/.claude/star/visual/rig2/messen_augenanker_exakt.py` (the exact —
not estimated — eye-anchor-position tool used for Round 2's pixel measurement above;
lives on ai-core-node's real disk, not inside either handoff archive) directly against
the live app on demand.
