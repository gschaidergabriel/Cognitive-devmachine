#!/usr/bin/env python3
"""harness_crush_knopf.py -- Desktop-Knopf-Ziel fuer den Crush-Free-Pool-
Harness (PHASE 52, Werkzeugwechsel weg von aider, siehe harness_crush.py
Modul-Docstring fuer den vollen Hintergrund). Waehlt ein Startmodell (exakt
dieselbe Auswahl-Logik wie harness_aider_knopf.py's _waehle_modell() --
wiederverwendet, nicht dupliziert), schreibt crush.json + CRUSH.md frisch,
druckt den Kontingent-Banner und startet Crush interaktiv im echten Repo
(~/frankenstein-repo, dieselbe Sandbox-Konvention wie der aider-Harness)."""
import os
import subprocess
import sys

STAR_DIR = os.path.expanduser("~/.claude/star")
sys.path.insert(0, STAR_DIR)

import harness_aider as _h  # noqa: E402 -- _waehle_modell-Logik direkt importiert unten
import harness_crush as _hc  # noqa: E402
from harness_aider_knopf import _waehle_modell  # noqa: E402 -- keine Dopplung der Auswahl-Logik

_ANSI_GRUEN = "\x1b[38;5;46m"
_ANSI_RESET = "\x1b[0m"


def _chatgpt_bridge_status() -> str:
    """Gabriel-Auftrag 2026-09-12: Free Frank soll IMMER mit sichtbarem
    ChatGPT-Bridge-Status starten. Die Bridge (frankenstein-local-bridge
    .service + -webui.service) laeuft bereits systemweit als eigener
    systemd-user-Dienst, unabhaengig von Free Frank -- hier nur PRUEFEN
    und ANZEIGEN, nicht neu erfinden/starten (kein zweiter Owner)."""
    try:
        out = subprocess.run(
            ["systemctl", "--user", "is-active",
             "frankenstein-local-bridge.service"],
            capture_output=True, text=True, timeout=5,
        )
        aktiv = out.stdout.strip() == "active"
    except Exception:
        aktiv = False
    if not aktiv:
        try:
            subprocess.run(
                ["systemctl", "--user", "start",
                 "frankenstein-local-bridge.service"],
                capture_output=True, text=True, timeout=10,
            )
            out = subprocess.run(
                ["systemctl", "--user", "is-active",
                 "frankenstein-local-bridge.service"],
                capture_output=True, text=True, timeout=5,
            )
            aktiv = out.stdout.strip() == "active"
        except Exception:
            aktiv = False
    return "ChatGPT-Bridge: AN" if aktiv else "ChatGPT-Bridge: AUS (Start fehlgeschlagen)"


def _banner_drucken():
    """PHASE 52 Nachtrag, KORRIGIERT (Gabriel woertlich nach Live-Screenshot
    des grossen toilet-Banners: 'nein der bildschirm war cooler ich will
    den' -- gemeint ist Crushs EIGENER nativer Startbildschirm, orange
    'CHARM CRUSH'-Logo mit Diagonalmuster). Gelesen als: Crushs eigenes
    Logo bleibt unangetastet und ERSCHEINT ZUERST -- kein grosses eigenes
    ASCII-Banner mehr davor. Nur noch eine kurze, kleine Textzeile, die VOR
    Crushs Start gedruckt wird (verschwindet nach oben, sobald Crush den
    Bildschirm uebernimmt) -- kein Ersatz, keine Verdraengung von Crushs
    eigenem Logo. Falls diese Lesart falsch ist: billig korrigierbar, siehe
    Bericht."""
    print(f"{_ANSI_GRUEN}FranKenstein v2.0 -- Free Pool Harness (Crush){_ANSI_RESET}")


def main():
    _banner_drucken()
    print(f"{_ANSI_GRUEN}{_chatgpt_bridge_status()}{_ANSI_RESET}")
    modell_id, hinweis = _waehle_modell()
    if modell_id is None:
        print(f"Abbruch: {hinweis}", file=sys.stderr)
        return 1
    print(hinweis)

    # Alle Free-Pool-Schluessel in os.environ laden (nicht nur den des
    # Startmodells) -- exakt dasselbe Argument wie in
    # harness_aider._alle_api_keys_laden()'s Docstring: Crush erlaubt
    # Modellwechsel MITTEN in der Sitzung, dafuer muessen alle 4 Provider-
    # Keys schon beim Start in der Umgebung stehen, nicht erst der eine.
    _h._alle_api_keys_laden()

    _hc.crush_config_schreiben(startmodell_id=modell_id)
    _hc.crush_zustand_schreiben(
        session_id=f"crush-knopf-{os.getpid()}",
        auftrag=f"Crush-Free-Pool-Harness-Start, Startmodell={modell_id}")

    _hc.kontingent_banner_drucken()

    provider_modell = _hc.provider_modell_string(modell_id)
    if provider_modell is None:
        print(f"Abbruch: kein Crush-Katalogeintrag fuer {modell_id}", file=sys.stderr)
        return 1

    crush_bin = _hc._crush_bin()
    if crush_bin is None:
        print("Abbruch: crush-Binary nicht gefunden "
              "(erwartet ~/.local/npm-global/bin/crush -- npm install -g @charmland/crush).",
              file=sys.stderr)
        return 1

    os.makedirs(_hc.SICHTBAR_REPO, exist_ok=True)
    env = dict(os.environ)
    npm_bin = os.path.expanduser("~/.local/npm-global/bin")
    env["PATH"] = npm_bin + os.pathsep + env.get("PATH", "")

    # BUGFIX (Screenshot-Beleg erster Live-Launch): interaktives `crush`
    # (ohne `run`-Unterbefehl) hat KEIN `-m`/`--model` -- nur `crush run`.
    # Das Startmodell steckt bereits in crush.json (models.large/small,
    # siehe crush_config_schreiben(startmodell_id=...) oben), kein Flag noetig.
    # Gabriel-Auftrag 2026-09-12: "voller Reentry" -- Crush setzt die letzte
    # Sitzung fuer dieses cwd fort statt jedes Mal bei Null anzufangen.
    # --continue ist ein No-Op-Fallback (startet frisch), wenn es noch
    # keine vorherige Sitzung gibt -- kein Absturzrisiko beim allerersten Lauf.
    print(f"Starte Crush mit {provider_modell} in {_hc.SICHTBAR_REPO} (Reentry) ...")
    lauf = subprocess.run(
        [crush_bin, "--cwd", _hc.SICHTBAR_REPO, "--continue"],
        env=env,
    )

    # PHASE 54 (Gabriel-Auftrag 2026-09-12, Punkt 2 "Hinrichtung"): NACH
    # crush-Exit die gerade beendete Sitzung real in die UnifiedDB
    # zurueckschreiben (durable_memory, siehe crush_sitzung_synchronisieren()-
    # Docstring) -- fire-and-forget, fail-soft, darf den Exitcode des
    # eigentlichen Crush-Laufs nie veraendern.
    try:
        letzte_sid = _hc.crush_letzte_sitzung_id()
        if letzte_sid:
            sync_ergebnis = _hc.crush_sitzung_synchronisieren(letzte_sid)
            print(f"Sync Crush-Sitzung -> UnifiedDB: {sync_ergebnis.get('stand')} "
                  f"({str(sync_ergebnis.get('bericht') or sync_ergebnis.get('grund') or '')[:160]})")
    except Exception as e:
        print(f"(Sync Crush-Sitzung -> UnifiedDB uebersprungen: {e})", file=sys.stderr)

    return lauf.returncode


if __name__ == "__main__":
    sys.exit(main())
