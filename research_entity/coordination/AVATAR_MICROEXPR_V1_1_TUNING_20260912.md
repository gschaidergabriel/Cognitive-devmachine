# Avatar microexpression V1.1 tuning candidate — 2026-09-12

Status: **SOURCE/TUNING CANDIDATE ONLY — NOT LIVE**

Current live production subject remains `buehne.html` SHA-256 `cfaefcd2719d7680d8b0a532aa6fae9c2920e022ab3626d18de073eb87a80cdb`, with exactly one `FRANK_MICROEXPR_V1` block, one `_mikroMimikSchritt(t)` call and one `_mikroMimikStateAktualisieren(b)` hook. Do not mutate while host admission is red.

## Why V1.1 is needed

V1 already satisfies the architecture target: one existing animation loop, no second rAF, no extra status polling timer, state-driven stochastic hazard, recent-expression suppression, speech/external-mouth arbitration and special-expression exclusion.

The next defect is semantic calibration, not architecture. Current generic regex categories do not distinguish the six actual base avatar states strongly enough. In particular `04_zugewandt_weich` and `05_erschoepft_schwer` currently fall close to neutral; `03_angespannt` still gives social smirks too much mass; `06_ueberrascht` does not make the surprise microgesture dominant enough.

## Exact base-state semantic matrix

Apply these multipliers *after* the current generic state/presence/load factors and *before* recent-history suppression.

| `b.ausdruck` | social | positive | ponder | stress | play | surprise | hazard multiplier |
|---|---:|---:|---:|---:|---:|---:|---:|
| `01_ruhig_neutral` | 0.90 | 0.75 | 0.90 | 0.62 | 0.58 | 0.20 | 0.82 |
| `02_wach_aufmerksam` | 0.95 | 0.70 | 1.55 | 0.82 | 0.45 | 0.30 | 1.02 |
| `03_angespannt` | 0.28 | 0.18 | 1.05 | 2.35 | 0.045 | 0.36 | 1.10 |
| `04_zugewandt_weich` | 1.55 | 1.85 | 0.76 | 0.22 | 1.15 | 0.22 | 1.05 |
| `05_erschoepft_schwer` | 0.40 | 0.25 | 1.10 | 0.62 | 0.035 | 0.18 | 0.46 |
| `06_ueberrascht` | 0.34 | 0.35 | 0.42 | 0.75 | 0.22 | 5.50 | 1.55 |

Intent:
- neutral: alive but low-amplitude, no clown loop;
- alert: lip purse / small asymmetry / thinking motion;
- tense: jaw set / nose scrunch / lip compression, almost no tongue;
- soft/engaged: asymmetric smirk / closed grin / occasional tongue tip;
- exhausted: much lower event rate, mostly small lip movements;
- surprised: fast short gasp/nose response dominates, then refractory calm.

## Per-expression refractory policy

V1 currently has one global `nextAllowed` plus history suppression. Add a per-profile `cooldownUntil` map so conspicuous gestures cannot recur too soon even if history has rotated out.

Recommended minimum cooldowns:

- smirk left/right: 7–11 s each; opposite side may occur after >=3.5 s;
- lip pout / lip purse: 8–12 s;
- jaw set: 12–18 s;
- nose scrunch left/right: 8–13 s each;
- tongue tip: 22–35 s;
- tongue out: 50–80 s;
- tongue left/right: 60–95 s each;
- gasp micro: 16–28 s unless a fresh surprise impulse exceeds the previous one;
- grin closed: 9–16 s.

This preserves "often something happens" while making conspicuous gestures rare enough to remain meaningful.

## Event diagnostics without another browser

The current production Chrome has no DevTools port and must remain the singleton. A later admitted version should keep an in-memory ring of the last 32 **natural** events in `window.__frankMicroexpr.events`, each containing only:

`{t, name, baseState, present, near, activation, surprise, load, reason}`

and counters:

`naturalCount`, `forcedCount`, `externalAbortCount`, `specialSuppressedCount`, `mouthBusySuppressedCount`.

Do not add a network logger or new polling loop merely for diagnostics. If exact runtime readout becomes necessary, expose it through the existing daemon/status authority in a separately admitted, low-frequency read-only route rather than starting a second browser.

## Mouth / speech ownership

Preserve the current collision discipline:
- `_sonderLaeuft` always wins;
- speech mouth changes always win;
- a changed mouth `src` or opacity not authored by the active microexpression aborts the microexpression;
- after external mouth activity, retain a short randomized refractory gap before idle mimicry can start again;
- never turn silent microexpressions into a second lip-sync engine.

## Asset-path verification

Inventory evidence confirms active 295x182 mouth assets and transition frames exist for smirk, pout, jaw clench, snarls/nose-scrunch proxies, tongue tip/out/left/right, gasp, grin and whistle/lip-purse. Both top-level `name__stufe_NN.png` forms and generated per-expression `name/stufe_NN.png` directories exist for relevant active assets. Continue fail-closed if any selected file fails to decode.

## Naturalness acceptance gate

Do not call V1.1 accepted merely because the source parses. Required runtime evidence on the same production subject:

1. singleton Chrome remains exactly one and same intended display-2 subject;
2. service/HTTP healthy and live source exact hash bound;
3. >=30 natural events, no forced-key samples counted;
4. at least 5 expression families observed when state permits;
5. inter-event intervals visibly non-periodic: coefficient of variation >=0.45 and no dominant narrow-bin cadence;
6. immediate same-expression repeats <=2% outside explicit fresh-surprise override;
7. zero expression overlap with `_sonderLaeuft`;
8. zero observed speaking-mouth corruption; external collision must abort rather than fight;
9. tongue-out/side frequency <=8% of all natural events combined under ordinary non-playful state;
10. exhausted state has materially lower event hazard than alert/soft state;
11. tense state favors stress/ponder microgestures over social/play gestures;
12. surprise state favors `gasp_micro`/scrunch over smirk;
13. no meaningful FPS regression versus the same production subject baseline;
14. no new production browser/window/process created.

## Current hold

Fresh host admission at ~10:27 local still reports `Stufe kritisch`, including `temperatur:eng`, load ~10.8, plus a body-care DB lock. Therefore this tuning is deliberately not promoted now. The correct next effect is **no additional live effect until fresh host telemetry is non-red**.
