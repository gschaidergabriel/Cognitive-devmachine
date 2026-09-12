#!/usr/bin/env python3
"""Runtime-quiesced matched eye A/B, successor to the failed freeze harnesses.

Evidence lineage:
- v1 virtual-time-only: runtime ready after ordering repair, but OFF->OFF drifted
  across ~39% of the canvas.
- derived main-rAF/CSS freeze: reduced residual drift to ~0.72%, proving the
  moving avatar/background was the confound, but one or more timer/rand paths
  remained active.

This gate preserves the original exact-subject and visual thresholds.  After the
special expression is active it quiesces the already-running test page in place:
block future rAF/timers, cancel existing rAF/timer/interval IDs, pause CSS/Web
Animations and media, stop pending loads, then also pause Chrome virtual time.
Only the isolated shadow page is touched; live source/assets remain read-only.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "validate_matched_eye_ab.py"
src = BASE.read_text(encoding="utf-8")

old_freeze = '''        # Freeze only after runtime readiness and special-expression activation.\n        # From here onward the two screenshots differ only by canonical eye\n        # opacity/src, while timers/rAF stay pinned at the same visual state.\n        cdp.call("Emulation.setVirtualTimePolicy", {"policy": "pause"})\n        geometry = json.loads(cdp.eval('''
assert src.count(old_freeze) == 1, src.count(old_freeze)

new_freeze = r'''        # Quiesce every known browser-side producer in the isolated shadow.
        # Existing timer/rAF IDs in Chromium are monotonically allocated integer
        # handles.  Obtain current high-water marks, cancel the full live ranges,
        # then replace scheduling entry points so pending callbacks cannot restart
        # motion.  This is a test-page intervention only, never a live-source edit.
        quiesce_state = json.loads(cdp.eval(r"""
JSON.stringify((()=>{
  const nativeRAF = window.requestAnimationFrame.bind(window);
  const nativeCAF = window.cancelAnimationFrame.bind(window);
  const nativeST = window.setTimeout.bind(window);
  const nativeCT = window.clearTimeout.bind(window);
  const nativeSI = window.setInterval.bind(window);
  const nativeCI = window.clearInterval.bind(window);

  const rafHigh = nativeRAF(()=>{});
  const timerHigh = nativeST(()=>{}, 2147483647);

  window.requestAnimationFrame = ()=>0;
  window.setTimeout = ()=>0;
  window.setInterval = ()=>0;

  let rafCancelAttempts = 0;
  for (let i=1; i<=rafHigh; i++) { nativeCAF(i); rafCancelAttempts++; }
  let timerCancelAttempts = 0;
  for (let i=1; i<=timerHigh; i++) {
    nativeCT(i); nativeCI(i); timerCancelAttempts++;
  }

  let animationsPaused = 0;
  try {
    for (const a of document.getAnimations({subtree:true})) {
      try { a.pause(); animationsPaused++; } catch (_) {}
    }
  } catch (_) {}
  let mediaPaused = 0;
  for (const m of document.querySelectorAll('video,audio')) {
    try { m.pause(); mediaPaused++; } catch (_) {}
  }
  const style = document.createElement('style');
  style.id = '__go-quiesce-style';
  style.textContent = '*{animation-play-state:paused!important;transition:none!important;caret-color:transparent!important}';
  document.documentElement.appendChild(style);
  try { window.stop(); } catch (_) {}
  return {rafHigh, timerHigh, rafCancelAttempts, timerCancelAttempts,
          animationsPaused, mediaPaused, futureSchedulersBlocked:true};
})())
"""))
        # Let any callback already on the JS stack finish exactly once; all of its
        # future scheduling calls are now inert.  Then freeze Chrome's clock too.
        time.sleep(0.20)
        cdp.call("Emulation.setVirtualTimePolicy", {"policy": "pause"})
        time.sleep(0.05)
        geometry = json.loads(cdp.eval('''

src = src.replace(old_freeze, new_freeze)
src = src.replace('"GO_AVATAR_EYE_MATCHED_FROZEN_AB/v1"', '"GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3"')
src = src.replace(
    '"ISOLATED_REAL_BROWSER_VIRTUAL_TIME_FROZEN_NO_LIVE_SOURCE_WRITE"',
    '"ISOLATED_REAL_BROWSER_FULL_RUNTIME_QUIESCENCE_NO_LIVE_SOURCE_WRITE"',
)
needle = '            "geometry": geometry,\n            "eye_off_to_on": ab,'
assert src.count(needle) == 1, src.count(needle)
src = src.replace(needle, '            "geometry": geometry,\n            "quiesce": quiesce_state,\n            "eye_off_to_on": ab,')

ns = {"__name__": "__main__", "__file__": str(BASE), "__package__": None}
exec(compile(src, str(BASE) + "#quiesced-v3", "exec"), ns, ns)
