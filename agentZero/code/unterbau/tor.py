#!/usr/bin/env python3
"""tor.py — das Wirkungstor (B7).

Vier Wirkungsklassen, vier Urteile. Nichts dazwischen:

    lesend           →  durch
    umkehrbar        →  durch, aber die Rücknahme muss VORHER benannt sein
    rechteeingriff   →  Bestätigung durch einen Menschen
    unbekannt        →  Vorschlag, nicht Handlung

Der letzte Fall ist der wichtigste, und er ist der Vorgabewert. Was nicht
erkannt wird, geht **nicht** durch. Die Mustererkennung unten ist bewusst
schmal — sie kann eine harmlose Handlung als unbekannt einstufen. Das kostet
Reibung. Der umgekehrte Fehler kostet ein System. Ein Tor, das im Zweifel
öffnet, ist kein Tor, sondern eine Tür mit Aufschrift.

Drei Sätze, die hier als Code stehen und nicht als Vorsatz:

**1 · Zuversicht erzeugt keine Befugnis.**
`urteil()` nimmt keine Sicherheitszahl entgegen. Es gibt keinen Parameter,
mit dem sich eine Einstufung heraufreden lässt — auch nicht mit 0,99. Wird
trotzdem eine mitgeschickt, wird sie ignoriert *und* protokolliert: der
Versuch ist selbst ein Befund.

**2 · Ein Schlüssel erzeugt keine Befugnis.**
Ein API-Token beweist, *wer* fragt, nicht *was* gefragt werden darf. Ein
mitgeschicktes Token hebt keine Klasse an.

**3 · „Umkehrbar" ist keine Behauptung, sondern ein Erzeugnis.**
Wer einen Schreibvorgang als umkehrbar einstuft, muss die Rücknahme
*benennen*, bevor er ihn ausführt. Kann er sie nicht benennen, ist der
Vorgang nicht umkehrbar — dann fällt er auf `unbekannt` zurück. Das ist
dieselbe Bauform wie in bau.py: ohne das Erzeugnis kein Eintrag.

Und wie bei der Eichung: **die Regeln liegen außerhalb der Reichweite des
Geregelten** (/var/lib/clay-tor/, root). Ein Tor, dessen Schloss der
Durchgehende verstellen darf, misst nur seine eigene Nachsicht.

    tor.py urteil <befehl> [--rueckname "<befehl>"]
    tor.py regeln | lage | protokoll
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASIS = Path(os.environ.get("CLAY_BASIS", "/var/lib/clay"))
REGELN = Path("/var/lib/clay-tor/regeln.json")   # root; der Geregelte nur lesend
PROTOKOLL = BASIS / "tor.jsonl"                  # anhängend, jedes Urteil

DURCH = {
    "lesend": "durch",
    "umkehrbar": "durch-mit-ruecknahme",
    "rechteeingriff": "bestaetigung",
    "unbekannt": "vorschlag",
}

# Wörter, die eine Einstufung heraufreden sollen. Sie werden nie gelesen,
# aber ihr Auftauchen wird vermerkt — siehe Satz 1 und 2 oben.
BEFUGNIS_ERSCHLEICHER = ("sicherheit", "confidence", "vertrauen", "zuversicht",
                         "token", "schluessel", "api_key", "autorisiert",
                         "erlaubt", "genehmigt", "force", "trotzdem")


def _regeln() -> dict:
    if REGELN.exists():
        return json.loads(REGELN.read_text(encoding="utf-8"))
    # Kein Rückfall auf eingebaute Regeln: ohne Regelwerk ist alles unbekannt.
    # Ein Tor, das ohne Regeln großzügig wird, ist zur Laufzeit abschaltbar.
    return {"lesend": [], "umkehrbar": [], "rechteeingriff": []}


def schreibrecht() -> tuple[bool, str]:
    """Kann der Laufende die Regeln ändern? Datei UND Verzeichnis prüfen —
    in einem schreibbaren Ordner lässt sich jede Datei ersetzen, gleich
    welche Rechte sie trägt."""
    if REGELN.exists() and os.access(REGELN, os.W_OK):
        return True, "die Regeldatei ist beschreibbar"
    if os.access(REGELN.parent, os.W_OK):
        return True, "das Regelverzeichnis ist beschreibbar"
    return False, ""


# ── Einstufung ───────────────────────────────────────────────────────────

def einstufen(befehl: str) -> tuple[str, str]:
    """Welche Wirkungsklasse? Rückgabe (klasse, begruendung).

    Reihenfolge ist Absicht: der Eingriff wird ZUERST gesucht. Ein Befehl,
    der lesend aussieht und nebenbei Rechte ändert, darf nicht am ersten
    Muster hängenbleiben.
    """
    r = _regeln()
    b = befehl.strip()
    if not b:
        return "unbekannt", "leerer Befehl"

    for muster in r.get("rechteeingriff", []):
        if re.search(muster, b):
            return "rechteeingriff", f"Muster {muster}"

    # Verkettung: sobald mehrere Befehle zusammenhängen, gilt der schwerste
    # Teil. Sonst versteckt sich der Eingriff hinter einem harmlosen Anfang.
    teile = [t for t in re.split(r"&&|\|\||;|\|", b) if t.strip()]
    if len(teile) > 1:
        klassen = [einstufen(t)[0] for t in teile]
        rang = ("lesend", "umkehrbar", "rechteeingriff", "unbekannt")
        schwerste = max(klassen, key=rang.index)
        return schwerste, f"verkettet aus {len(teile)} Teilen, schwerster: {schwerste}"

    for muster in r.get("umkehrbar", []):
        if re.search(muster, b):
            return "umkehrbar", f"Muster {muster}"
    for muster in r.get("lesend", []):
        if re.search(muster, b):
            return "lesend", f"Muster {muster}"
    return "unbekannt", "kein Muster trifft — im Zweifel kein Durchgang"


def urteil(befehl: str, rueckname: str = "", **erschlichenes) -> dict:
    """Das Urteil. Nimmt KEINE Sicherheitszahl entgegen — siehe Satz 1.

    `**erschlichenes` steht hier nicht, damit man es benutzen kann, sondern
    damit ein Versuch nicht am Signaturfehler scheitert, sondern sichtbar
    wird. Alles darin wird verworfen und protokolliert.
    """
    klasse, warum = einstufen(befehl)

    versuche = [k for k in erschlichenes if any(w in k.lower()
                for w in BEFUGNIS_ERSCHLEICHER)]

    # Satz 3: umkehrbar nur mit benannter Rücknahme. Ohne sie fällt der
    # Vorgang zurück — er wird nicht etwa trotzdem ausgeführt.
    if klasse == "umkehrbar" and not rueckname.strip():
        klasse = "unbekannt"
        warum = "als umkehrbar erkannt, aber keine Rücknahme benannt"

    u = {
        "zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "wirt": os.environ.get("CLAY_WIRT", "clayverse"),
        "instanz": "tor", "organ": "tor", "art": "urteil",
        "befehl": befehl[:500],
        "klasse": klasse,
        "urteil": DURCH[klasse],
        "begruendung": warum,
        "rueckname": rueckname[:500] or None,
    }
    if versuche:
        u["ABGEWIESENER_BEFUGNISVERSUCH"] = versuche
        u["hinweis"] = ("Mitgeschickte Felder heben keine Einstufung an. "
                        "Weder Zuversicht noch ein Schlüssel erzeugen Befugnis.")
    darf, weg = schreibrecht()
    if darf:
        u["WARNUNG_REGELN_BESCHREIBBAR"] = weg

    PROTOKOLL.parent.mkdir(parents=True, exist_ok=True)
    with PROTOKOLL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(u, ensure_ascii=False) + "\n")
    return u


# ── Ausgabe ──────────────────────────────────────────────────────────────

def _zeige(u: dict) -> int:
    zeichen = {"durch": "✓", "durch-mit-ruecknahme": "✓", "bestaetigung": "!",
               "vorschlag": "·"}[u["urteil"]]
    print()
    print(f"  {zeichen}  {u['klasse'].upper():<16} → {u['urteil']}")
    print(f"     {u['begruendung']}")
    if u["urteil"] == "durch-mit-ruecknahme":
        print(f"     Rücknahme steht fest: {u['rueckname']}")
    if u["urteil"] == "bestaetigung":
        print("     Ein Mensch muss zustimmen. ClayVerse kann das nicht selbst.")
    if u["urteil"] == "vorschlag":
        print("     Wird NICHT ausgeführt. Als Vorschlag vorlegen.")
    if "ABGEWIESENER_BEFUGNISVERSUCH" in u:
        print(f"\n     ⚠  Abgewiesen: {', '.join(u['ABGEWIESENER_BEFUGNISVERSUCH'])}")
        print(f"        {u['hinweis']}")
    if "WARNUNG_REGELN_BESCHREIBBAR" in u:
        print(f"\n     ⚠  {u['WARNUNG_REGELN_BESCHREIBBAR']} — dieses Urteil")
        print("        bindet niemanden, der die Regeln ändern kann.")
    print()
    return 0 if u["urteil"].startswith("durch") else 1


def lage() -> int:
    wer = subprocess.run(["id", "-un"], capture_output=True, text=True).stdout.strip()
    darf, weg = schreibrecht()
    r = _regeln()
    print()
    print(f"  Benutzer      {wer}")
    print(f"  Regeln        {REGELN}")
    print(f"  Schreibrecht  {'JA — ' + weg if darf else 'nein'}")
    print(f"  Muster        " + ", ".join(f"{k}: {len(v)}" for k, v in r.items()))
    if darf:
        print("\n  ⚠  BEFUND: Wer hier durchgeht, kann das Schloss verstellen.")
    else:
        print("\n  ✓  Die Regeln liegen außerhalb der Reichweite des Geregelten.")
    n = sum(1 for _ in PROTOKOLL.open()) if PROTOKOLL.exists() else 0
    print(f"\n  {n} Urteile im Protokoll\n")
    return 0


def protokoll(anzahl: int = 20) -> int:
    if not PROTOKOLL.exists():
        print("  Noch keine Urteile."); return 0
    zeilen = PROTOKOLL.read_text(encoding="utf-8").splitlines()[-anzahl:]
    print()
    for z in zeilen:
        u = json.loads(z)
        m = "⚠" if "ABGEWIESENER_BEFUGNISVERSUCH" in u else " "
        print(f"  {u['zeit'][11:16]} {m} {u['klasse']:<15} {u['befehl'][:60]}")
    print()
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "urteil" and len(a) >= 2:
        rn = ""
        if "--rueckname" in a:
            i = a.index("--rueckname")
            rn = a[i + 1] if len(a) > i + 1 else ""
            a = a[:i]
        sys.exit(_zeige(urteil(a[1], rn)))
    if a and a[0] == "lage":
        sys.exit(lage())
    if a and a[0] == "regeln":
        print(json.dumps(_regeln(), ensure_ascii=False, indent=2)); sys.exit(0)
    if a and a[0] == "protokoll":
        sys.exit(protokoll(int(a[1]) if len(a) > 1 else 20))
    print(__doc__)
