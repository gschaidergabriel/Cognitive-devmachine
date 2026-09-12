# Avatar blink temporal/arbitration gate — 2026-09-12

Status: `DEFECT_REPRODUCED_FROM_EXACT_LIVE_SOURCE; CANDIDATE_ONLY; LIVE_UNCHANGED`

## Exact subject

Evidence was derived from the `ai-core-node` production `buehne.html` readback whose receipt reports SHA-256:

`18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`

The running service/HTTP subject was healthy in the companion runtime receipt. This branch does **not** mutate the live file, browser, service, VM, or assets.

## Defect A — special-expression arbitration race

The source states that blink must not run over a special expression because special-expression frames carry their own eyes.

Observed implementation:

1. `blinzeln()` checks `_sonderLaeuft` only at blink start.
2. `blinzelAbspielen()` continues frame callbacks without checking `_sonderLaeuft`.
3. `sonderausdruckZeigen()` sets `_sonderLaeuft = true` but does not cancel/hide an already active blink.
4. `#augen-blink` has `z-index:4`; `#ausdruck-schicht` has `z-index:3`.

Therefore, if `sonderausdruckZeigen()` begins after a blink has started but before its finite frame chain finishes, the blink overlay remains/reappears above the special-expression face. This contradicts the declared visual arbitration rule.

### Minimal candidate repair

Do both, not only one:

- immediately hide the active blink and clear `blinzelPhase` when a special expression acquires the visual lane;
- at the start of every `blinzelAbspielen()` callback, fail closed if `_sonderLaeuft` became true after the blink started. For `zeitplanNeu=true`, schedule exactly one later normal blink chain; for the one-shot double-blink bonus (`zeitplanNeu=false`), do not create a new chain.

Candidate logic:

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

This preserves the prior Galton-Watson leak fix: a normal chain re-plans once, while a bonus double blink never becomes a self-propagating second chain.

## Defect B — temporal asymmetry contradicts its own target

Current exact timing functions:

- close frame delay: `15 + random*5` ms; 9 closing frames -> 135–180 ms
- closed hold: `30 + random*20` ms
- open frame delay: `40 + random*12` ms; 3 opening frames -> 120–156 ms

Consequences:

- complete blink theoretical range: 285–386 ms;
- the declared 250–350 ms corridor is violated at the upper tail;
- closing is not reliably faster than opening; its mean is 157.5 ms versus 138 ms opening, opposite to the source's stated biological asymmetry.

A 5,000,000-sample independent Monte-Carlo check of the exact distributions produced mean ≈335.49 ms and `P(total > 350 ms) ≈ 0.0622` (diagnostic only; the analytic bounds above are sufficient to prove the corridor violation).

### Timing candidate for a later matched visual A/B

Do **not** promote these numbers from prose alone. They are a bounded candidate that satisfies the source's own invariants before perceptual testing:

```js
function blinzelDauerSchliessen(){ return 11 + Math.random()*2; } // 11–13 ms × 9 => 99–117 ms
function blinzelDauerGeschlossenHalten(){ return 40 + Math.random()*15; } // 40–55 ms
function blinzelDauerOeffnen(){ return 46 + Math.random()*9; } // 46–55 ms × 3 => 138–165 ms
```

Candidate total: 277–337 ms. Closing is strictly faster than opening across the support (117 < 138), while the total remains inside 250–350 ms.

## Non-gating documentation drift

The block comment says blink interval `3–8s`, while `blinzelWeiterPlanen()` currently uses `2000 + Math.random()*5000`, i.e. 2–7 s. Another inline comment labels 2–7 s as Gabriel's requirement. This is contradictory documentation/intent, so this branch records it but does not choose one interval without a stronger authority source.

## Promotion fence

Required before any live promotion:

1. re-read current production preimage hash and exact existing Chrome/window subject;
2. run `blink_temporal_arbitration_gate.py` against the current source;
3. apply a candidate only in an admitted scratch/integration lane first;
4. deterministic forced blink + forced special-expression overlap test;
5. prove blink overlay opacity stays zero for the entire special-expression interval;
6. matched before/after visual capture on the existing production geometry;
7. performance non-regression;
8. if promoted, reload the **existing** production Avatar only and independently read back hashes/runtime.

No whole-avatar, GRID, GWT/J-Space, training, or whole-product credit is implied by this finding.