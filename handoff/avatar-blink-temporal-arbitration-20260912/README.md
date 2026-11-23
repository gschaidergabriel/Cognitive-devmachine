# Avatar blink temporal/arbitration gate — 2026-09-12

Status: `TIMING_DEFECT_REPRODUCED; ARBITRATION_SEMANTICS_CONFLICT_FOUND; BLOCKED_ON_RECONCILIATION; LIVE_UNCHANGED`

## Exact live subject

Evidence was derived from the `ai-core-node` production `buehne.html` readback whose receipt reports SHA-256:

`18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`

The running service/HTTP subject was healthy in the companion runtime receipt. This branch does **not** mutate the live file, browser, service, VM, or assets.

## Finding A — live arbitration contract and implementation disagree

The **current live source** states that blink must not run over a special expression because special-expression frames carry their own eyes.

Observed live implementation:

1. `blinzeln()` checks `_sonderLaeuft` only at blink start.
2. `blinzelAbspielen()` continues frame callbacks without checking `_sonderLaeuft`.
3. `sonderausdruckZeigen()` sets `_sonderLaeuft = true` but does not cancel/hide an already active blink.
4. `#augen-blink` has `z-index:4`; `#ausdruck-schicht` has `z-index:3`.

Therefore, under the live rule, a special expression that begins after a blink starts can be covered by the ongoing blink overlay. That is a real implementation/contract mismatch in the exact live preimage.

### Swarm reconciliation result — do **not** patch this blindly

A parallel eye-identity lane intentionally defines a different candidate semantic:

- branch/head used by the shadow lane: `chatgpt-work/avatar-eye-identity-canonical-mask-20260912` / `d2ee0f1d36658d2072be3af2b2f9734d6ae606ec`;
- `build_semantic_shadow_html.py` deliberately removes the `_sonderLaeuft` early return from `blinzeln()`;
- it keeps the canonical open-eye plate visible after playback;
- `validate_special_auto_blink_runtime.py` deliberately starts one special expression and expects the product to auto-blink while that special expression remains active;
- that candidate is shadow-only and does not mutate production.

So there are now two explicit competing semantics:

**LIVE CONTRACT A** — special-expression frames own their eyes; blink must not overlay them.

**SHADOW CANDIDATE B** — canonical eye identity remains an independent semantic layer and is allowed to blink during special expressions.

Until the current coordinator/owner lane promotes one semantic with a valid matched runtime/perceptual gate, an arbitration code change is **blocked**. The earlier minimal guard/cancel patch is retained below only as the implementation for Contract A; it is **not a promotion recommendation**.

### Contract-A implementation candidate — DISABLED pending reconciliation

```js
function sonderausdruckZeigen(register, ausdruck, haltenMs){
  if(_sonderLaeuft) return;
  haltenMs = haltenMs || 1400;
  _sonderLaeuft = true;
  $("augen-blink").style.opacity = "0";
  blinzelPhase = null;
  // existing function continues...
}

function blinzelAbspielen(schritte, idx, zeitplanNeu){
  if(_sonderLaeuft){
    $("augen-blink").style.opacity = "0";
    blinzelPhase = null;
    if(zeitplanNeu) blinzelWeiterPlanen();
    return;
  }
  // existing function continues...
}
```

If Contract A eventually wins, this preserves the prior Galton-Watson leak fix: a normal chain re-plans once, while a bonus double blink never becomes a self-propagating second chain.

## Finding B — temporal asymmetry is independently wrong

This does **not** depend on whether Contract A or B wins.

Current exact timing functions:

- close frame delay: `15 + random*5` ms; 9 closing frames -> 135–180 ms
- closed hold: `30 + random*20` ms
- open frame delay: `40 + random*12` ms; 3 opening frames -> 120–156 ms

Consequences:

- complete blink theoretical range: 285–386 ms;
- the declared 250–350 ms corridor is violated at the upper tail;
- closing is not reliably faster than opening; its mean is 157.5 ms versus 138 ms opening, opposite to the source's stated biological asymmetry.

A 5,000,000-sample independent Monte-Carlo check of the exact distributions produced mean ≈335.49 ms and `P(total > 350 ms) ≈ 0.0622` (diagnostic only; the analytic bounds above are sufficient to prove the corridor violation).

### Timing candidate for matched visual A/B

Do **not** promote these numbers from prose alone. They are a bounded candidate that satisfies the source's own temporal invariants before perceptual testing:

```js
function blinzelDauerSchliessen(){ return 11 + Math.random()*2; } // 11–13 ms × 9 => 99–117 ms
function blinzelDauerGeschlossenHalten(){ return 40 + Math.random()*15; } // 40–55 ms
function blinzelDauerOeffnen(){ return 46 + Math.random()*9; } // 46–55 ms × 3 => 138–165 ms
```

Candidate total: 277–337 ms. Closing is strictly faster than opening across the support (117 < 138), while the total remains inside 250–350 ms.

## Non-gating documentation drift

The live block comment says blink interval `3–8s`, while `blinzelWeiterPlanen()` currently uses `2000 + Math.random()*5000`, i.e. 2–7 s. Another inline comment labels 2–7 s as Gabriel's requirement. This is contradictory documentation/intent, so this branch records it but does not choose one interval without stronger authority.

## Highest-information next discriminator

Do **one** matched shadow experiment, not two competing implementations:

1. same exact source/assets/viewport/timing;
2. Condition A: special expression owns eyes (blink suppressed/cancelled);
3. Condition B: canonical eye semantic layer remains active and auto-blinks over special expression;
4. deterministic special-expression trigger and deterministic blink phase;
5. matched pixel/perceptual eye-region evidence, non-eye invariance, no rectangular patch edge;
6. event-loop/FPS control;
7. no production mutation;
8. promote only the winning semantic after coordinator/owner admission.

The existing `validate_special_auto_blink_runtime.py` is useful for Condition B, but the most recent host run observed in the swarm ended in a CDP/WebSocket timeout. That is instrumentation failure, not product acceptance or rejection.

## Promotion fence

Before any live promotion: re-read the current production preimage hash and exact existing Chrome/window subject; require a valid non-timeout discriminator; preserve rollback; reload the **existing** production Avatar only; independently read back source/runtime. No whole-avatar, GRID, GWT/J-Space, training, or whole-product credit is implied.