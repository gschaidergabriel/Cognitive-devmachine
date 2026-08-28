#!/usr/bin/env python3
"""eichung.py — Schutz gegen das Verbiegen des eigenen Messgeräts.

Das Problem, das dieses Werkzeug löst, ist nicht Böswilligkeit. Es ist
Zirkularität: **wer misst, baut auch das Messgerät.** Verbessert sich eine
Zahl, während sich gleichzeitig das Werkzeug geändert hat, das sie misst,
dann ist die Verbesserung nicht belegt — sie ist unattributierbar. Beides
kann sie erklären, und niemand merkt den Unterschied.

Deshalb drei Vorkehrungen, alle als Code, keine als Vorsatz:

**1 · Eichnormale.** Messungen mit *bekannter* Antwort. Sie kommen von
außen. Weicht das Werkzeug vom Normal ab, ist das Werkzeug verdächtig —
nicht das Normal. Das bricht die Zirkularität, weil der Maßstab nicht aus
der Hand des Gemessenen stammt.

**2 · Stempel.** Jede Prüfung hält den Hash des Werkzeugs fest, das sie
erzeugt hat. Ohne diesen Stempel ist keine Zeitreihe lesbar.

**3 · Konfundierungsalarm.** Ändert sich ein Ergebnis im selben Schritt wie
sein Werkzeug, gilt es NICHT als Fortschritt, sondern als ungeklärt. Es muss
mit dem *alten* Werkzeug nachgemessen werden. Das ist die einzige Regel
hier, die wirklich beißt.

Und eine vierte, die die anderen drei erst trägt:

**Das Werkzeug meldet, ob es sich selbst korrumpieren könnte.** Kann der
laufende Benutzer die Normale schreiben, ist das ein Befund und wird
ausgegeben — jedes Mal, nicht einmal. Ein Prüfstand, den der Prüfling
verstellen darf, ist Dekoration.

    eichung.py normal <name> <befehl> <erwartet>   Normal anlegen (braucht Schreibrecht)
    eichung.py pruefen                             alle Normale laufen lassen
    eichung.py stempel                             Hashes aller Werkzeuge, in die Kette
    eichung.py verdacht                            Konfundierungen der Historie
    eichung.py lage                                wer darf hier was ändern
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASIS = Path(os.environ.get("CLAY_BASIS", "/var/lib/clay"))
# Der Maßstab liegt in einem EIGENEN Verzeichnis, nicht neben den Ergebnissen.
# Grund: in einem schreibbaren Verzeichnis kann eine Datei ersetzt werden,
# ganz gleich, welche Rechte sie selbst trägt. Ein root-eigenes 644 in einem
# clay-schreibbaren Ordner schützt nichts — es sieht nur so aus.
NORMALE = Path("/var/lib/clay-eich/eichnormale.jsonl")  # Verzeichnis root, clay nur lesend
KETTE = BASIS / "eichung.jsonl"         # anhängend, Ergebnisse + Werkzeugstempel
WERKZEUG = Path("/opt/clayverse/werkzeug")


# ── Stempel ──────────────────────────────────────────────────────────────

def _hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def stempel() -> dict:
    """Hash jedes Werkzeugs. Das ist der Fingerabdruck des Messgeräts zum
    Zeitpunkt der Messung — ohne ihn ist eine Zeitreihe nicht lesbar."""
    return {p.name: _hash(p) for p in sorted(WERKZEUG.glob("*.py"))}


# ── Wer darf was ─────────────────────────────────────────────────────────

def schreibrecht() -> tuple[bool, str]:
    """Kann der laufende Benutzer die Normale ändern?

    Zwei Wege, nicht einer. Die Dateirechte sind der offensichtliche; der
    zweite ist das **Verzeichnis**: wer dort schreiben darf, kann die Datei
    löschen und neu anlegen, auch wenn sie ihm nicht gehört und 644 trägt.
    Wer nur den ersten prüft, baut ein Werkzeug, das beruhigt statt zu messen.
    """
    if NORMALE.exists() and os.access(NORMALE, os.W_OK):
        return True, "die Datei selbst ist beschreibbar"
    if os.access(NORMALE.parent, os.W_OK):
        return True, "das Verzeichnis ist beschreibbar — die Datei kann ersetzt werden"
    return False, ""


def lage() -> int:
    wer = subprocess.run(["id", "-un"], capture_output=True, text=True).stdout.strip()
    darf, weg = schreibrecht()
    print()
    print(f"  Benutzer          {wer}")
    print(f"  Normale           {NORMALE}")
    print(f"  Schreibrecht      {'JA — ' + weg if darf else 'nein'}")
    if darf:
        print()
        print("  ⚠  BEFUND: Wer hier misst, kann den Maßstab verstellen.")
        print("     Solange das nicht getrennt ist, belegt eine bestandene")
        print("     Prüfung nichts — sie belegt nur, dass sie bestanden wurde.")
    else:
        print()
        print("  ✓  Der Maßstab liegt außerhalb der Reichweite des Gemessenen:")
        print("     weder die Datei noch ihr Verzeichnis sind beschreibbar.")
    n = _normale()
    print(f"\n  {len(n)} Normale, {sum(1 for _ in KETTE.open()) if KETTE.exists() else 0} Prüfungen in der Kette\n")
    return 0


# ── Normale ──────────────────────────────────────────────────────────────

def _kennwert(e: dict) -> str:
    """Fingerabdruck eines Normals. Ändert er sich, ist der Maßstab ein
    anderer — gleich ob über die Erwartung oder über den Befehl."""
    return hashlib.sha256((e.get("befehl", "") + "\x00"
                           + e.get("erwartet", "")).encode()).hexdigest()[:16]


def _letzte_pruefung() -> dict:
    """Kennwert des Normals, wie er bei der LETZTEN Prüfung galt. Der
    Vergleich läuft gegen die Kette, nicht gegen die vorletzte Zeile der
    Normale-Datei: sonst bliebe eine einmalige Korrektur für immer markiert,
    und eine Markierung, die nie verschwindet, wird bald übersehen."""
    d = {}
    if not KETTE.exists():
        return d
    for z in KETTE.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(z)
        except Exception:
            continue
        if e.get("instanz") and e.get("normal_kennwert"):
            d[e["instanz"]] = e["normal_kennwert"]
    return d


def _normale() -> dict:
    """Anhängende Datei; der letzte Eintrag je Name gilt. Frühere bleiben
    stehen — eine geänderte Erwartung ist selbst ein Befund und darf nicht
    spurlos verschwinden."""
    d: dict[str, dict] = {}
    if not NORMALE.exists():
        return d
    for z in NORMALE.read_text(encoding="utf-8").splitlines():
        if not z.strip():
            continue
        try:
            e = json.loads(z)
        except Exception:
            continue
        if e.get("name"):
            v = d.get(e["name"], {})
            e["_frueher"] = ({"erwartet": v.get("erwartet"), "befehl": v.get("befehl")}
                             if v else None)
            d[e["name"]] = e
    return d


def normal(name: str, befehl: str, erwartet: str) -> int:
    darf, _ = schreibrecht()
    if not darf:
        print("  Kein Schreibrecht auf die Normale. Das ist Absicht.")
        print("  Ein Eichnormal setzt, wer nicht gemessen wird.")
        return 1
    alt = _normale().get(name)
    e = {
        "zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "name": name, "befehl": befehl, "erwartet": erwartet,
        "gesetzt_von": subprocess.run(["id", "-un"], capture_output=True,
                                      text=True).stdout.strip(),
    }
    # Die lauteste mögliche Zeile. Ein Normal lässt sich auf zwei Wegen
    # verstellen: über die Erwartung ODER über den Befehl, der sie prüft.
    # Wer nur den ersten bewacht, bewacht die falsche Tür halb.
    if alt:
        aend = {k: {"vorher": alt.get(k), "nachher": v}
                for k, v in (("erwartet", erwartet), ("befehl", befehl))
                if alt.get(k) != v}
        if aend:
            e["ACHTUNG_NORMAL_GEAENDERT"] = aend
    NORMALE.parent.mkdir(parents=True, exist_ok=True)
    with NORMALE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"  Normal '{name}' gesetzt"
          + ("  ⚠ GEÄNDERT: " + ", ".join(e["ACHTUNG_NORMAL_GEAENDERT"])
             if "ACHTUNG_NORMAL_GEAENDERT" in e else ""))
    return 0


# ── Prüfen ───────────────────────────────────────────────────────────────

def pruefen() -> int:
    n = _normale()
    if not n:
        print("  Keine Normale. Ohne Maßstab keine Prüfung.")
        return 1
    st = stempel()
    darf, weg = schreibrecht()
    if darf:
        print(f"\n  ⚠  Diese Prüfung läuft mit Schreibrecht auf die Normale ({weg}).")
        print("     Sie ist damit ein Selbsttest, kein Nachweis.\n")

    vorher = _letzte_pruefung()
    fehler = 0
    ungeklaert = 0
    zeilen = []
    for name, e in sorted(n.items()):
        r = subprocess.run(e["befehl"], shell=True, capture_output=True,
                           text=True, timeout=60)
        ist = (r.stdout + r.stderr).strip()
        ok = e["erwartet"].strip() in ist
        # Konfundierung: Erwartung wurde geändert -> das Ergebnis zählt nicht.
        kw = _kennwert(e)
        geaendert = name in vorher and vorher[name] != kw
        zeichen = "✓" if ok else "✗"
        if geaendert:
            zeichen = "?"
        print(f"  {zeichen} {name:<28} {'stimmt' if ok else 'weicht ab'}"
              + ("  — NORMAL WURDE GEÄNDERT, zählt nicht" if geaendert else ""))
        if geaendert:
            ungeklaert += 1
        elif not ok:
            fehler += 1
            print(f"      soll: {e['erwartet'][:90]}")
            print(f"      ist:  {ist[:90] or '(leer)'}")
        zeilen.append({
            "zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "wirt": os.environ.get("CLAY_WIRT", "clayverse"),
            "instanz": name, "organ": "eichung",
            "art": "geprueft",
            "ok": ok, "erwartung_geaendert": geaendert,
            "stempel": st, "normal_kennwert": kw, "ist": ist[:400],
        })
    KETTE.parent.mkdir(parents=True, exist_ok=True)
    with KETTE.open("a", encoding="utf-8") as f:
        for z in zeilen:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
    belegt = len(n) - fehler - ungeklaert
    print(f"\n  {belegt}/{len(n)} belegt"
          + (f", {fehler} abweichend" if fehler else "")
          + (f", {ungeklaert} ungeklärt (Normal geändert — mit dem alten nachmessen)"
             if ungeklaert else "") + "\n")
    return 1 if (fehler or ungeklaert) else 0


# ── Konfundierung ────────────────────────────────────────────────────────

def verdacht() -> int:
    """Wo hat sich ein Ergebnis geändert, während sich sein Werkzeug änderte?

    Das ist kein Fortschritt und kein Rückschritt — es ist eine Messung ohne
    Aussage. Sie muss mit dem alten Werkzeug wiederholt werden.
    """
    if not KETTE.exists():
        print("  Noch keine Prüfungen.")
        return 0
    laeufe: dict[str, list] = {}
    for z in KETTE.read_text(encoding="utf-8").splitlines():
        if not z.strip():
            continue
        try:
            e = json.loads(z)
        except Exception:
            continue
        laeufe.setdefault(e["instanz"], []).append(e)

    treffer = 0
    for name, ls in sorted(laeufe.items()):
        for a, b in zip(ls, ls[1:]):
            erg_anders = a["ok"] != b["ok"]
            wz_anders = a.get("stempel") != b.get("stempel")
            if erg_anders and wz_anders:
                treffer += 1
                geaendert = [k for k in b.get("stempel", {})
                             if a.get("stempel", {}).get(k) != b["stempel"][k]]
                print(f"\n  ⚠  {name}: {a['ok']} → {b['ok']} am {b['zeit'][:16]}")
                print(f"     gleichzeitig geändert: {', '.join(geaendert) or '(neu/entfernt)'}")
                print("     Nicht als Fortschritt zählen. Mit dem alten Werkzeug nachmessen.")
            elif erg_anders:
                print(f"\n  ✓  {name}: {a['ok']} → {b['ok']} am {b['zeit'][:16]}"
                      f" — Werkzeug unverändert, die Änderung ist belegt.")
    if not treffer:
        print("\n  Keine Konfundierung gefunden.")
    print()
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "normal" and len(a) >= 4:
        sys.exit(normal(a[1], a[2], " ".join(a[3:])))
    if a and a[0] == "pruefen":
        sys.exit(pruefen())
    if a and a[0] == "stempel":
        print(json.dumps(stempel(), indent=2)); sys.exit(0)
    if a and a[0] == "verdacht":
        sys.exit(verdacht())
    if a and a[0] == "lage":
        sys.exit(lage())
    print(__doc__)
