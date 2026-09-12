# Avatar state-driven idle microexpressions — readiness 2026-09-12

## Scope

Goal: make the existing FranKenstein production face move naturally while silent, with many small aperiodic state-derived microexpressions (lip press, smirk, unilateral upper-lip/nose-region scrunch candidates, jaw tension, pout, breath, tongue tip/out/left/right, rare whistle/gasp), without introducing a second GUI, second production Chrome, or a periodic/metronomic animation loop.

## Exact production subject used for design

- machine: `ai-core-node`
- owner: `gabriel`
- live page: `/home/ai-core-node/.claude/star/visual/buehne.html`
- live source SHA-256 at forensic read: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- service: `frankenstein-buehne.service`
- URL: `http://127.0.0.1:8788/`
- singleton law: one existing production Avatar Chrome only; normal promotion reloads that existing subject through the page's existing mtime reload path.

## Implemented on work branch

Branch: `chatgpt-work/avatar-state-idle-microexpressions-20260912`

Files:

- `idle_microexpressions.js` — stochastic state-hazard controller over the existing mouth-frame arbitration path.
- `policy_test.js` — state-bias, gating and immediate idle->speech ownership regression tests.
- `build_candidate.py` — exact-SHA, exact-marker, Node-syntax checked candidate builder; does not mutate production.
- `asset_gate.py` — read-only gate for all selected mouth/mid-face PNG assets and stage geometry.
- `host_admission.sh` — fail-closed host admission using FranKenstein body-monitor state, resource headroom, exact live SHA, service health and production-Chrome singleton count.

## Controller invariants

- No fixed animation period. Next opportunity is sampled from a bounded exponential distribution.
- 16% intentional no-op when an opportunity arrives, so due time does not imply visible motion.
- Per-action refractory windows and family-repeat suppression prevent recognizable repetition.
- Current state inputs are existing live state only: `aktuellerAusdruck`, real `serverBlick` presence/near state, and `tempo` derived from `broadcast_value`.
- Speech owns the mouth over idle behavior. When speech begins, queued idle frames are cleared immediately.
- Existing special-expression sequences own the full face over idle behavior.
- Idle behavior yields when the page is hidden, FPS is below 30, or the existing rain/performance degradation flag is active.
- No new `requestAnimationFrame` loop is added; the existing `mundSchritt()` frame player is reused.

## Policy verification already performed

The controller/policy harness passed with the intended ordering:

- tense state strongly favors tension/scrunch over play;
- warm + near presence favors smirk/smile/play over tension;
- exhausted state favors breath/pout and strongly suppresses play;
- surprised state increases O/gasp-family weight;
- event timing is denser with a near detected person than with only presence, and denser with presence than alone;
- speech, special-expression and low-FPS gates block idle motion;
- immediate idle->speech frame ownership handoff is a regression-tested invariant.

Representative mean opportunity intervals from the policy model before cooldown/no-op effects: approximately 9.5 s near, 13.2 s present, 19.1 s alone. Individual events additionally have minimum gaps and per-action cooldowns; tongue-out is deliberately rare with a 100–240 s individual cooldown.

## Current production promotion status

`LIVE_PROMOTION=0`

Reason: current real-host evidence showed `frankenstein-koerperpflege.service` repeatedly reporting `Stufe kritisch`, including `temperatur:eng` and `frankenstein-gespraech-adhoc`. Host safety therefore blocks any production mutation until a fresh readback passes `host_admission.sh` semantics.

A parallel/foreign worker also attempted a different `idle_face.js` path. Its post-live readback was negative: the file/route was missing, `INCLUDE=0`, `MARKER=0`, and `buehne.html` remained on the pre-change SHA. That path carries zero live-credit and is not the integration authority for this work.

A later independent readback also reported zero visible production-window matches. Under the current critical body state, this work does not start another Chrome merely to repair presentation. The next admitted runtime action must first establish healthy host state and exact singleton/runtime subject binding.

## Promotion gate

Promotion is allowed only when all of these are current and jointly true:

1. body monitor has fresh non-critical state;
2. exact live source SHA still matches the candidate input or the candidate is rebuilt from the new exact source;
3. avatar service is active;
4. exactly one intended production Chrome/window subject is bound (or, if absent, the singleton launcher path is separately admitted under healthy host state);
5. asset gate passes;
6. candidate inline JS syntax check passes;
7. atomic source mutation succeeds;
8. the existing production page, not a new browser, reloads;
9. post-readback proves service/HTTP/source marker/singleton/FPS and body-health remain acceptable;
10. rollback occurs on any failed postcondition.

No component PASS in this directory is production activation by itself.
