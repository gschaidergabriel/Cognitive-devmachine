#!/usr/bin/env python3
"""Dienststeuerung -- der EINZIGE Ausfuehrer, der fuer die Dienste-Bubble
systemctl/docker anfasst. Laeuft als root auf dem Host, per systemd-Timer
(eos-dienststeuerung.timer, alle 3s) -- NICHT im Container (der hat weder
systemctl noch docker).

Herkunft: Gabriel 19.08., "manuelle Steuerung der Dienste" fuer die Systeme-
Bubble. Der entityos-Container (uid 5001, kein Host-Zugriff) schreibt Steuer-
Anfragen als JSON-Dateien in den Spool /var/lib/clay/steuer-spool/ -- ein
Bind-Mount, den beide Seiten sehen. Dieses Skript liest sie, VALIDIERT JEDE
Anfrage GEGEN EINE FESTE WHITELIST und fuehrt ERST DANN systemctl/docker aus.

Die Whitelist-Grundlage kommt direkt aus DIENSTE in systemwacht.py (gleicher
Ordner, gleiche Quelle, die auch die Dienste-Liste der Bubble baut) -- so kann
sie nie unbeabsichtigt hinter der Anzeige zurueckbleiben. Der IMMUNSYSTEM_UNIT-
Sonderfall kommt aus derselben Datei dazu (eigener Schalter, kein Dienste-
Zeileneintrag).

⚠️ SICHERHEITSGRENZE: Die Whitelist HIER ist der einzige Ort, der zaehlt. Der
Container prueft die Anfrage vorher auch schon (terminal_gateway.py), aber das
ist nur eine frueh-Ablehnung (400) -- KEINE Sicherheitsgrenze. Selbst wenn der
Container-Check je einen Fehler haette oder umgangen wuerde: dieses Skript
fuehrt NIE eine Unit aus, die nicht hier in WHITELIST steht, und NIE eine
andere Aktion als start/stop/restart.

Robust: ein kaputtes/unbekanntes Spool-File oder ein fehlgeschlagener Aufruf
darf das Skript nie abstuerzen lassen -- es wird protokolliert und die naechste
Anfrage trotzdem bearbeitet.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from systemwacht import DIENSTE, IMMUNSYSTEM_UNIT  # gleiche Quelle wie die Dienste-Anzeige

SPOOL = Path("/var/lib/clay/steuer-spool")
ERLEDIGT = SPOOL / "erledigt"
LOG = Path("/var/lib/clay/dienststeuerung.log")

ERLAUBTE_AKTIONEN = {"start", "stop", "restart"}


def _bau_whitelist():
    w = {}
    for d in DIENSTE:
        if d.get("steuerbar"):
            w[d["unit"]] = {"art": d["art"], "kritisch": bool(d.get("kritisch"))}
    # Immunsystem-Schalter: kein Dienste-Zeileneintrag, aber steuerbar --
    # existiert die Unit noch nicht, schlaegt der systemctl-Aufruf unten
    # sauber fehl (siehe _ausfuehren/_bearbeite), kein Sonderfall noetig.
    w.setdefault(IMMUNSYSTEM_UNIT, {"art": "systemd", "kritisch": False})
    return w


WHITELIST = _bau_whitelist()


def _protokoll(zeile):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(zeile.rstrip("\n") + "\n")
    except Exception:
        pass  # Protokollieren darf den Ausfuehrer nie stoppen


def _lauf(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        return 1, "", str(e)


def _ausfuehren(unit, art, aktion):
    if art == "docker":
        return _lauf(["docker", aktion, unit], timeout=45)
    return _lauf(["systemctl", aktion, "--", unit], timeout=30)


def _verschiebe(pfad, ergebnis):
    try:
        ERLEDIGT.mkdir(parents=True, exist_ok=True)
        daten = {}
        try:
            daten = json.loads(pfad.read_text(encoding="utf-8"))
        except Exception:
            daten = {"kaputte_anfrage": True}
        daten["ergebnis"] = ergebnis
        daten["erledigt_zeit"] = time.time()
        ziel = ERLEDIGT / pfad.name
        ziel.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
        pfad.unlink(missing_ok=True)
    except Exception as e:
        _protokoll(f"FEHLER beim Verschieben von {pfad.name}: {e}")


def _bearbeite(pfad):
    stand = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        anfrage = json.loads(pfad.read_text(encoding="utf-8"))
        if not isinstance(anfrage, dict):
            raise ValueError("Anfrage ist kein Objekt")
    except Exception as e:
        _protokoll(f"{stand} FEHLER kaputte Anfrage {pfad.name}: {e}")
        _verschiebe(pfad, {"ok": False, "grund": "kaputte Anfrage"})
        return

    unit = str(anfrage.get("unit", "")).strip()
    aktion = str(anfrage.get("aktion", "")).strip()
    wer = anfrage.get("wer", "?")
    dienst_wunsch = anfrage.get("dienst", unit)

    # ── Die Sicherheitsgrenze: nur was hier in WHITELIST steht, mit nur den
    # drei erlaubten Aktionen, wird je ausgefuehrt. Alles andere wird abgelehnt
    # und protokolliert -- der Client-Wunsch wird NIE blind ausgefuehrt.
    eintrag = WHITELIST.get(unit)
    if eintrag is None or aktion not in ERLAUBTE_AKTIONEN:
        _protokoll(f"{stand} VERWEIGERT wer={wer} dienst={dienst_wunsch} unit={unit!r} "
                    f"aktion={aktion!r} -- nicht in der Whitelist")
        _verschiebe(pfad, {"ok": False, "grund": "nicht in der Whitelist"})
        return

    rc, out, err = _ausfuehren(unit, eintrag["art"], aktion)
    ok = (rc == 0)
    _protokoll(f"{stand} {'OK' if ok else 'FEHLGESCHLAGEN'} wer={wer} dienst={dienst_wunsch} "
                f"unit={unit} art={eintrag['art']} aktion={aktion} rc={rc}"
                + (f" err={err}" if err else ""))
    _verschiebe(pfad, {"ok": ok, "rc": rc, "stdout": out, "stderr": err})


def main():
    if not SPOOL.is_dir():
        return  # noch keine Anfrage je gestellt -- kein Fehler, nichts zu tun
    for pfad in sorted(SPOOL.glob("*.json")):
        try:
            _bearbeite(pfad)
        except Exception as e:
            _protokoll(f"FEHLER bei {pfad.name}: {e}")
            try:
                _verschiebe(pfad, {"ok": False, "grund": str(e)})
            except Exception:
                pass


if __name__ == "__main__":
    main()
