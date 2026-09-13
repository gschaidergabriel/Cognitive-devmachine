#!/usr/bin/env python3
"""harness_aider_knopf.py -- Wrapper fuer den Desktop-Knopf (PHASE 49,
Gabriel-Auftrag 2026-09-12): "ein aider-Harness mit passendem capable
free model oeffnen, mit vollem reentry und frankenstein 2.0 und grid und
alles voellig gleich".

Waehlt selbststaendig ein sinnvolles Startmodell (bevorzugt ein aktuell
NICHT im Cooldown befindliches Tier mit voller Editier-Berechtigung),
setzt es ueber die bestehende Aktivierungssperre aktiv (stern.py
modell-aktiv-setzen), und startet danach den sichtbaren Terminal-Harness
(harness_aider.py visible-start) -- exakt derselbe Pfad wie das bestehende
Modell-Dashboard, nur ohne den manuellen Klick davor. '/model' wechselt
danach INNERHALB der Sitzung frei zwischen allen 4 Modellen (siehe
harness_aider.py visible_run()/_alle_api_keys_laden()).

Auswahlreihenfolge (real begruendet, keine erfundene Prioritaet):
  1. viable_tiers() (pool_wache.py, nicht in Cooldown UND Schluessel
     vorhanden) UND berechtigung=='voll' (Dateien wirklich editierbar,
     nicht nur ask-only) -- in MODELL_MAP-Kaskaden-Reihenfolge.
  2. sonst irgendein viable_tiers()-Treffer (auch 'eingeschraenkt') --
     besser ask-only als gar kein Modell.
  3. sonst irgendein MODELL_MAP-Eintrag mit geladenem Schluessel, auch
     wenn pool_wache ihn (evtl. veraltet/unbekannt) als in Cooldown fuehrt
     -- klare Warnzeile, kein stiller Fallback.
  4. sonst harter Abbruch mit klarer Fehlermeldung (all_exhausted() ODER
     kein einziger Schluessel geladen).
"""
import os
import subprocess
import sys

STAR_DIR = os.path.expanduser("~/.claude/star")
sys.path.insert(0, STAR_DIR)

import harness_aider as _h  # noqa: E402  -- MODELL_MAP, _MODELL_ZU_POOL_TIER, _api_key_laden
import pool_wache as _pw  # noqa: E402


def _waehle_modell():
    """Gibt (modell_id, hinweis_text) zurueck, oder (None, fehlergrund)."""
    geladene_keys = {mid: bool(_h._api_key_laden(mid)) for mid in _h.MODELL_MAP}
    if not any(geladene_keys.values()):
        return None, "kein einziger Free-Pool-API-Schluessel in ~/.last-resort/keys.env gefunden"

    try:
        viable_pool_tiers = set(_pw.viable_tiers())
        exhausted = _pw.all_exhausted()
    except Exception as e:
        viable_pool_tiers, exhausted = set(), False
        print(f"Warnung: pool_wache-Status nicht lesbar ({e}) -- waehle rein nach vorhandenem Schluessel.",
              file=sys.stderr)

    # Kaskaden-Reihenfolge = MODELL_MAP-Insertion-Reihenfolge (Python 3.7+
    # Dicts sind ordnungserhaltend) -- keine eigene Sortierung erfunden.
    kandidaten = list(_h.MODELL_MAP.items())

    # 1) viable + voll
    for mid, info in kandidaten:
        tier = _h._MODELL_ZU_POOL_TIER.get(mid)
        if geladene_keys.get(mid) and tier in viable_pool_tiers and info["berechtigung"] == "voll":
            return mid, f"gewaehlt: {mid} (viable, volle Editierrechte)"

    # 2) irgendein viable
    for mid, info in kandidaten:
        tier = _h._MODELL_ZU_POOL_TIER.get(mid)
        if geladene_keys.get(mid) and tier in viable_pool_tiers:
            return mid, f"gewaehlt: {mid} (viable, ask-only -- kein volles Modell aktuell frei)"

    # 3) irgendein Schluessel vorhanden, auch wenn pool_wache Cooldown meldet
    for mid, info in kandidaten:
        if geladene_keys.get(mid):
            return mid, (f"gewaehlt: {mid} (WARNUNG: pool_wache meldet moeglichen Cooldown/"
                          f"unbekannten Zustand -- Schluessel ist trotzdem vorhanden)")

    grund = "alle Tiers erschoepft (Cooldown)" if exhausted else "kein nutzbares Modell gefunden"
    return None, grund


def main():
    modell_id, hinweis = _waehle_modell()
    if modell_id is None:
        print(f"Abbruch: {hinweis}", file=sys.stderr)
        return 1
    print(hinweis)

    # "python3" (System-Interpreter), nicht sys.executable -- exakt dieselbe
    # Aufrufkonvention wie stern.py's eigener harness_aider.py-Aufruf
    # (_chatgpt_harness_fallback(), STERN_DIR/harness_aider.py via
    # subprocess.run(["python3", ...])). harness_aider.py selbst braucht nur
    # Stdlib+stern -- die harness-venv ist NUR fuer den aider-Subprozess
    # noetig, den harness_aider.py intern ueber AIDER_VENV_PYTHON aufruft.
    setzen = subprocess.run(
        ["python3", os.path.join(STAR_DIR, "stern.py"), "modell-aktiv-setzen",
         "--modell", modell_id, "--von", "harness-desktop-knopf"],
        cwd=STAR_DIR,
    )
    if setzen.returncode != 0:
        print(f"Abbruch: modell-aktiv-setzen fehlgeschlagen (exit {setzen.returncode})", file=sys.stderr)
        return setzen.returncode

    lauf = subprocess.run(
        ["python3", os.path.join(STAR_DIR, "harness_aider.py"), "visible-start",
         "--modell", modell_id],
        cwd=STAR_DIR,
    )
    return lauf.returncode


if __name__ == "__main__":
    sys.exit(main())
