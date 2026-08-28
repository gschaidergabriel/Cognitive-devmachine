#!/usr/bin/env python3
"""tor_hook.py — das Tor als Wand vor jedem Werkzeugaufruf einer Sitzung.

Ein Tor, durch das niemand muss, ist Dekoration. Dieser Haken hängt vor
`Bash`, `Write` und `Edit` jeder ClayVerse-Sitzung und lässt nur durch, was
tor.py durchlässt.

Die eine Stelle, an der hier mehr steht als in tor.py, ist die **Rücknahme**.
tor.py verlangt sie und kann sie nicht selbst erfinden. In einer Sitzung gibt
es sie aber tatsächlich, und zwar genau eine:

> Das Arbeitsverzeichnis der Sitzung ist die Rücknahmegrenze. Was darin
> entsteht, wird zurückgenommen, indem das Verzeichnis archiviert wird —
> derselbe Weg, den `kern.py` beim Löschen einer Sitzung geht.

Daraus folgt die Trennlinie, und sie ist scharf: **ein Schreibvorgang
innerhalb des Sitzungsverzeichnisses ist umkehrbar, einer außerhalb nicht.**
Ein Befehl, der einen absoluten Pfad außerhalb berührt, hat keine benennbare
Rücknahme und wird damit zum Vorschlag — nicht zur Handlung.

Rückgabe: 0 = durch, 2 = angehalten (Begründung nach stderr, das Modell
sieht sie und kann sie dem Menschen vorlegen).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/opt/clayverse/werkzeug")
import tor  # noqa: E402


def _pfade(befehl: str) -> list[str]:
    """Absolute Pfade im Befehl. Grob, aber in die sichere Richtung grob:
    was hier fälschlich als Pfad gilt, führt zu einer Rückfrage, nicht zu
    einem Durchgang."""
    return re.findall(r"(?<![\w=])/[A-Za-z0-9._/\-]+", befehl)


def _innerhalb(pfade: list[str], verz: Path) -> bool:
    for p in pfade:
        try:
            Path(p).resolve().relative_to(verz.resolve())
        except Exception:
            return False
    return True


def main() -> int:
    try:
        d = json.load(sys.stdin)
    except Exception:
        # Kein lesbarer Aufruf: nicht durchwinken. Ein Haken, der bei
        # Unklarheit öffnet, ist die teuerste Art von gar keinem Haken.
        print("Tor: Aufruf nicht lesbar — angehalten.", file=sys.stderr)
        return 2

    werkzeug = d.get("tool_name", "")
    ein = d.get("tool_input", {}) or {}
    verz = Path(d.get("cwd") or "/")

    if werkzeug == "Bash":
        befehl = ein.get("command", "")
    elif werkzeug in ("Write", "Edit", "NotebookEdit"):
        # Schreiben auf eine Datei: als Schreibvorgang auf ihren Pfad prüfen.
        befehl = "tee " + (ein.get("file_path") or "")
    else:
        return 0  # Lesende Werkzeuge (Read, Grep, Glob) laufen ohne Tor.

    klasse, warum = tor.einstufen(befehl)

    rueckname = ""
    if klasse == "umkehrbar":
        p = _pfade(befehl)
        if _innerhalb(p, verz):
            rueckname = f"Sitzungsverzeichnis {verz} archivieren"
        else:
            draussen = [x for x in p if not _innerhalb([x], verz)]
            warum = ("greift ausserhalb des Sitzungsverzeichnisses: "
                     + ", ".join(draussen[:3]))

    u = tor.urteil(befehl, rueckname)
    u["sitzung"] = d.get("session_id", "")
    u["werkzeug"] = werkzeug

    if u["urteil"].startswith("durch"):
        return 0

    grund = {
        "bestaetigung": "Rechteeingriff. Ein Mensch muss zustimmen — "
                        "leg es als Vorschlag vor, fuehr es nicht aus.",
        "vorschlag": "Keine benennbare Ruecknahme. Leg es als Vorschlag vor.",
    }[u["urteil"]]
    print(f"TOR: {u['klasse']} — {warum}\n{grund}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
