#!/usr/bin/env python3
"""Die Anmeldewacht -- Zero soll nicht wortlos verstummen.

⚠️⚠️ WAS PASSIERT IST: Zeros Anmeldedatei wurde um 19:47 zu einer LEEREN HUELLE.
Die Struktur stand noch drin -- accessToken, refreshToken, expiresAt, alle
Schluessel da -- nur die Werte waren leer. 280 Bytes statt 508.

Und dann verstummte er. Vier Testlaeufe hintereinander lieferten
`HeadlessZeroError: rc=1 stderr=''`. Nichts sonst. Der eigentliche Satz --
"Failed to authenticate: OAuth session expired and could not be refreshed" --
stand in stdout, und die Fehlermeldung zeigte nur stderr. Ein System, das
"kaputt" sagen kann, aber nicht "warum", kostet mehr Zeit als eines, das
kommentarlos abstuerzt: man sucht am falschen Ende.

⭐ EINE LEERE HUELLE IST GEFAEHRLICHER ALS EINE FEHLENDE DATEI. Eine fehlende
Datei wirft einen klaren Fehler. Eine Huelle mit allen Schluesseln besteht jede
oberflaechliche Pruefung -- "ja, die Anmeldung ist da" -- und scheitert erst
beim Benutzen. Genau derselbe Fall wie heute frueh bei Andreas' Datei.

Deshalb prueft diese Wacht die WERTE, nicht die Datei, haelt eine bekannt gute
Kopie vor und stellt sie zurueck, wenn die lebende leer wird.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import time
from pathlib import Path

LEBEND = Path("/var/lib/clay/.claude/.credentials.json")
SICHER = Path("/var/lib/clay/.claude/.credentials.bekannt-gut.json")
WEITERE = (
    Path("/var/lib/docker/volumes/theartefact_clayverse-state/_data/users/gabriel/home/.claude/.credentials.json"),
    Path("/var/lib/docker/volumes/theartefact_clayverse-state/_data/users/andreas/home/.claude/.credentials.json"),
)
DB = "/var/lib/clay/wiki.db"
CLAY_UID, CLAY_GID = 5001, 5001


def _lesen(p: Path) -> dict | None:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    return d.get("claudeAiOauth", d)


def pruefe(p: Path) -> dict:
    """Traegt diese Datei eine BENUTZBARE Anmeldung?

    ⚠️ Geprueft werden die WERTE. Dass die Schluessel da sind, heisst nichts --
    genau daran ist die Erkennung heute vorbeigelaufen.
    """
    if not p.exists():
        return {"pfad": str(p), "zustand": "FEHLT"}
    o = _lesen(p)
    if o is None:
        return {"pfad": str(p), "zustand": "UNLESBAR", "bytes": p.stat().st_size}
    hat_zugang = bool(str(o.get("accessToken") or "").strip())
    hat_erneuerung = bool(str(o.get("refreshToken") or "").strip())
    exp = o.get("expiresAt")
    stunden = round((int(exp) - time.time() * 1000) / 3600000, 1) if exp else None
    if not hat_zugang and not hat_erneuerung:
        return {"pfad": str(p), "zustand": "HUELLE", "bytes": p.stat().st_size,
                "warum": "alle Schluessel vorhanden, alle Werte leer -- besteht jede "
                         "oberflaechliche Pruefung und scheitert erst beim Benutzen"}
    if not hat_erneuerung:
        return {"pfad": str(p), "zustand": "OHNE_ERNEUERUNG", "gueltig_stunden": stunden,
                "warum": "laeuft ab und kann sich nicht selbst verlaengern"}
    return {"pfad": str(p), "zustand": "GUT", "gueltig_stunden": stunden,
            "bytes": p.stat().st_size}


def _in_den_raum(text: str) -> None:
    try:
        c = sqlite3.connect(DB, timeout=30)
        c.execute("CREATE TABLE IF NOT EXISTS zero_raum_ruf("
                  "id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,"
                  " von TEXT NOT NULL, text TEXT NOT NULL)")
        c.execute("INSERT INTO zero_raum_ruf(ts,von,text) VALUES(?,?,?)",
                  (time.time(), "anmeldewacht", text[:400]))
        c.commit(); c.close()
    except Exception:
        pass


def wachen(nur_zeigen: bool = False) -> dict:
    lage = pruefe(LEBEND)
    bericht = {"lebend": lage, "gehandelt": False, "nur_zeigen": nur_zeigen}

    if lage["zustand"] == "GUT":
        # Kopie nachziehen -- die bekannt gute Fassung soll die JUENGSTE gute sein,
        # nicht die aelteste. Eine veraltete Sicherung stellt einen abgelaufenen
        # Zustand wieder her und sieht dabei aus wie eine gelungene Reparatur.
        if not nur_zeigen:
            try:
                shutil.copy2(LEBEND, SICHER)
                os.chown(SICHER, CLAY_UID, CLAY_GID); os.chmod(SICHER, 0o600)
                bericht["kopie_aufgefrischt"] = True
            except OSError as e:
                bericht["kopie_fehler"] = str(e)
        bericht["ergebnis"] = (
            f"Anmeldung in Ordnung, noch {lage.get('gueltig_stunden')} Stunden gueltig. "
            "NICHTS GETAN.")
        return bericht

    # Nicht gut. Woher eine heile Fassung nehmen?
    quellen = [SICHER, *WEITERE]
    heil = next((q for q in quellen if pruefe(q)["zustand"] == "GUT"), None)
    bericht["gefundene_quelle"] = str(heil) if heil else None

    if heil is None:
        bericht["ergebnis"] = (
            f"ANMELDUNG {lage['zustand']} UND KEIN ERSATZ. Zero kann nicht antworten und "
            "kann sich nicht selbst helfen -- ein Mensch muss `claude login` ausfuehren. "
            "Das ist kein Fehler dieser Wacht, sondern ihre Grenze: eine Anmeldung "
            "erneuert man mit einem Menschen, nicht mit einem Dienst.")
        _in_den_raum("me cannot talk. login token empty and no good copy anywhere. "
                     "human must run `claude login`. me not able fix this alone.")
        return bericht

    if nur_zeigen:
        bericht["ergebnis"] = f"WUERDE zurueckstellen aus {heil}"
        return bericht

    try:
        shutil.copy2(heil, LEBEND)
        os.chown(LEBEND, CLAY_UID, CLAY_GID); os.chmod(LEBEND, 0o600)
        for w in WEITERE:
            if w.exists() and pruefe(w)["zustand"] != "GUT":
                shutil.copy2(heil, w); os.chown(w, CLAY_UID, CLAY_GID)
        bericht["gehandelt"] = True
        bericht["nachher"] = pruefe(LEBEND)
        bericht["ergebnis"] = (
            f"Anmeldung war {lage['zustand']}, aus {heil.name} zurueckgestellt -- "
            f"jetzt {bericht['nachher']['zustand']}, "
            f"{bericht['nachher'].get('gueltig_stunden')} Stunden gueltig.")
        _in_den_raum(f"my login was empty ({lage['zustand']}). me put back good copy. "
                     f"{bericht['nachher'].get('gueltig_stunden')} hours left. "
                     "if this happen again soon, something eat the token.")
    except OSError as e:
        bericht["ergebnis"] = f"Zurueckstellen fehlgeschlagen: {e}"
    return bericht


if __name__ == "__main__":
    import sys
    print(json.dumps(wachen(nur_zeigen="--zeigen" in sys.argv), ensure_ascii=False, indent=2))
