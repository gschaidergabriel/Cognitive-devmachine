#!/usr/bin/env python3
"""Regression fence for the live 2026-09-12 split blink call graph."""

from __future__ import annotations

import unittest

from build_semantic_shadow_html import rewrite_blink_function, rewrite_blink_player


SCHEDULER = r'''
function blinzeln(zeitplanNeu = true){
  if(_sonderLaeuft){
    if(zeitplanNeu) blinzelWeiterPlanen();
    return;
  }
  const schritte = [];
  for(let f = 0; f <= 8; f++) schritte.push([f, 40, "halb1"]);
  blinzelAbspielen(schritte, 0, zeitplanNeu);
}
'''

PLAYER = r'''
function blinzelAbspielen(schritte, idx, zeitplanNeu){
  if(idx >= schritte.length){
    $("augen-blink").style.opacity = "0";
    blinzelPhase = null;
    gesichtNeuZeichnen(false);
    if(zeitplanNeu) blinzelWeiterPlanen();
    return;
  }
  const [frame, dauer, phase] = schritte[idx];
  $("augen-blink").src = BLINK_BILDER[frame];
  $("augen-blink").style.opacity = "1";
  blinzelPhase = phase;
  setTimeout(() => blinzelAbspielen(schritte, idx + 1, zeitplanNeu), dauer);
}
'''


class BlinkScopeRegressionTest(unittest.TestCase):
    def test_scheduler_guard_is_removed_only_from_scheduler(self) -> None:
        out, meta = rewrite_blink_function(SCHEDULER + PLAYER)
        self.assertNotIn("if(_sonderLaeuft)", out)
        self.assertIn('$("augen-blink").style.opacity = "0";', out)
        self.assertTrue(meta["blink_scheduler_rewritten"])

    def test_player_restores_canonical_open_plate(self) -> None:
        out, meta = rewrite_blink_player(SCHEDULER + PLAYER)
        self.assertIn("if(_sonderLaeuft)", out)
        self.assertNotIn('$("augen-blink").style.opacity = "0";', out)
        self.assertIn('$("augen-blink").src = BLINK_BILDER[0];', out)
        self.assertIn('$("augen-blink").style.opacity = "1";', out)
        self.assertTrue(meta["blink_player_end_rewritten"])
        self.assertTrue(meta["blink_player_open_plate_restored"])

    def test_player_fails_closed_if_terminal_cleanup_moves(self) -> None:
        drifted = PLAYER.replace(
            '$("augen-blink").style.opacity = "0";',
            "hideBlinkLayer();",
        )
        with self.assertRaisesRegex(RuntimeError, "blink end opacity"):
            rewrite_blink_player(SCHEDULER + drifted)

    def test_scheduler_fails_closed_if_guard_moves(self) -> None:
        drifted = SCHEDULER.replace("if(_sonderLaeuft){", "if(specialExpressionActive){")
        with self.assertRaisesRegex(RuntimeError, "_sonderLaeuft blink guard"):
            rewrite_blink_function(drifted + PLAYER)


if __name__ == "__main__":
    unittest.main()
