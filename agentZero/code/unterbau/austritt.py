#!/usr/bin/env python3
"""austritt.py — vom inneren Wiki zur ClaySearch für alle anderen Clays (B27).

Es gibt zwei Fassungen desselben Wissens:

* **innen** — vollständig. Sieht ClayVerse, und sehen die beiden Master-Clays
  von Gabriel und Andreas. Dort steht alles, mit Namen, Pfaden, Wirten.
* **außen** — die ClaySearch für jeden anderen Clay. Anonymisiert, und nur
  das, was **veröffentlicht und offiziell verfügbar** ist, mit Vermerk, ob
  quelloffen, und mit etwaigen Lizenzkosten bei Verwendung.

Die eine Entscheidung, an der alles hängt:

> **Die äußere Fassung entsteht durch Aufnehmen, nicht durch Schwärzen.**

Eine Schwärzungsliste fällt offen aus. Was niemand markiert hat, geht durch —
und neu Hinzugekommenes ist per Definition unmarkiert. Ein Artikel tritt hier
nur aus, wenn er vier Nachweise erbringt. Fehlt einer, bleibt er drinnen; das
ist kein Vorwurf an ihn, sondern der Vorgabewert.

    1 · veröffentlicht    mit Beleg (öffentliche URL / öffentliches Repo)
    2 · Lizenz belegt     aus LICENSE/SPDX/Paketdaten — NIE geraten,
                          samt Kosten bei Verwendung
    3 · anonym            keine bekannte Identität überlebt die Umschrift
    4 · ohne Geheimnis    nichts, was wie ein Schlüssel aussieht

Punkt 3 ist zweistufig, und das ist Absicht: die Umschrift *ersetzt*, die
Prüfung *hält an*. Die Umschrift darf etwas übersehen — die Prüfung darf es
nicht, und sie entscheidet. Ein Artikel, bei dem nach der Umschrift noch eine
bekannte Identität steht, wird nicht nachgebessert, sondern in Quarantäne
gelegt. Nachbessern hieße, dem Ersetzer zu vertrauen, den man gerade beim
Übersehen ertappt hat.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

WIKI = Path("/var/lib/clay-wiki")
INNEN = WIKI / "innen"
AUSSEN = WIKI / "aussen"
QUARANTAENE = WIKI / "quarantaene"
# Die Sperrliste liegt außerhalb der Reichweite dessen, der austritt —
# dieselbe Bauform wie beim Tor und bei der Eichung.
SPERRE = Path("/var/lib/clay-wiki-sperre/identitaeten.json")

# Muster für Dinge, die wie ein Schlüssel aussehen. Sie werden nie ersetzt,
# nur erkannt: ein Artikel mit so etwas darin tritt nicht aus.
GEHEIMNIS = [
    (r"\bgh[pousr]_[A-Za-z0-9]{20,}", "GitHub-Token"),
    (r"\bsk-[A-Za-z0-9\-_]{20,}", "API-Schlüssel"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "privater Schlüssel"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS-Schlüssel"),
    (r"(?i)\b(passwor[dt]|passphrase|secret|api[_-]?key)\s*[:=]\s*\S{6,}", "Zugangsdatum im Klartext"),
    (r"\b\d{1,3}(\.\d{1,3}){3}\b", "IP-Adresse"),
]

# Nur was hier steht, gilt als Lizenz. „Sonstiges" gibt es nicht — eine
# unbekannte Lizenz ist keine Lizenz, sondern eine offene Frage.
QUELLOFFEN = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "GPL-2.0",
              "GPL-3.0", "AGPL-3.0", "LGPL-3.0", "MPL-2.0", "ISC", "Unlicense",
              "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0"}
GESCHLOSSEN = {"proprietaer", "kommerziell", "nur-intern"}


def _sperre() -> dict:
    """Zwei Klassen, und der Unterschied ist der Kern der Sache.

    `geheim` — Personen, Adressen, innere Wirte, Pfade. Was hier steht,
    verlässt das Haus nie; die Prüfung hält daran an.
    `oeffentlich` — Projektnamen, Lizenzen, veröffentlichte Adressen. Was
    ohnehin jeder sehen kann, ist kein Geheimnis, und es zu schwärzen macht
    einen Artikel nutzlos, ohne irgendetwas zu schützen.

    Ohne diese Trennung gibt es nur zwei Ausgänge, und beide sind falsch:
    alles schwärzen (dann tritt nichts Brauchbares aus) oder nichts
    (dann tritt alles aus).
    """
    if SPERRE.exists():
        return json.loads(SPERRE.read_text(encoding="utf-8")).get("geheim", [])
    # Ohne Sperrliste tritt nichts aus. Ein Austritt, der ohne Prüfliste
    # großzügig wird, ist zur Laufzeit abschaltbar.
    return []


# ── 3a · Umschrift ───────────────────────────────────────────────────────

def umschreiben(text: str, sperre: list) -> str:
    """Ersetzt bekannte Identitäten durch Rollen.

    Zwei Feinheiten, beide teuer erkauft:

    *Länge zuerst* — sonst zerlegt ein kurzer Treffer einen längeren, und in
    einer Mailadresse bliebe nach dem Vornamen der Rest stehen.

    *Rollen fallen zusammen* — mehrere Gruppen tragen absichtlich dieselbe
    Bezeichnung („eine Person"). Ein stabiler Deckname ist keine
    Anonymisierung, sondern eine Pseudonymisierung: wer genug Artikel liest,
    erkennt an den Handlungen, wer „Mensch B" ist. Für das, wozu die äußere
    Fassung da ist — Methoden und Erfahrung, nicht Beziehungen —, kostet das
    Zusammenfallen fast nichts.
    """
    paare = sorted(((v, g["rolle"]) for g in sperre for v in g["woerter"]),
                   key=lambda x: -len(x[0]))
    for wort, rolle in paare:
        text = re.sub(re.escape(wort), f"[{rolle}]", text, flags=re.IGNORECASE)
    return text


# ── 3b · Prüfung (sie entscheidet, nicht die Umschrift) ──────────────────

def ueberlebende(text: str, sperre: list) -> list[str]:
    t = text.lower()
    return sorted({v for g in sperre for v in g["woerter"] if v.lower() in t})


def geheimnisse(text: str) -> list[str]:
    return sorted({was for muster, was in GEHEIMNIS if re.search(muster, text)})


# ── Der Austritt ─────────────────────────────────────────────────────────

def pruefe(a: dict, sperre: list) -> tuple[bool, list[str], dict | None]:
    """Vier Nachweise. Rückgabe (darf_raus, gruende, aeussere_fassung)."""
    fehlt = []

    # 1 · veröffentlicht, mit Beleg. „true" allein ist eine Behauptung.
    beleg = (a.get("veroeffentlicht_beleg") or "").strip()
    if not a.get("veroeffentlicht") or not beleg:
        fehlt.append("nicht als veröffentlicht belegt (öffentliche URL fehlt)")
    elif not re.match(r"https?://", beleg):
        fehlt.append(f"Beleg ist keine öffentliche Adresse: {beleg[:60]}")

    # 2 · Lizenz aus einem Fundort, nicht aus dem Kopf.
    liz = (a.get("lizenz") or "").strip()
    fundort = (a.get("lizenz_fundort") or "").strip()
    if not liz or not fundort:
        fehlt.append("Lizenz nicht belegt (Bezeichnung und Fundort nötig)")
    elif liz not in QUELLOFFEN and liz not in GESCHLOSSEN:
        fehlt.append(f"Lizenz '{liz}' unbekannt — unbekannt ist keine Lizenz")

    # 3 · anonym: erst umschreiben, dann prüfen. Die Prüfung entscheidet.
    text = umschreiben(a.get("text", ""), sperre)
    titel = umschreiben(a.get("titel", ""), sperre)
    ueber = ueberlebende(titel + "\n" + text, sperre)
    if ueber:
        fehlt.append(f"Identität überlebt die Umschrift: {', '.join(ueber[:3])}")

    # 4 · nichts Schlüsselförmiges.
    g = geheimnisse(titel + "\n" + text)
    if g:
        fehlt.append(f"sieht aus wie ein Geheimnis: {', '.join(g)}")

    if fehlt:
        return False, fehlt, None

    return True, [], {
        "id": a["id"],
        "titel": titel,
        "text": text,
        "art": a.get("art", "artikel"),
        "lizenz": liz,
        "quelloffen": liz in QUELLOFFEN,
        "lizenzkosten": a.get("lizenzkosten") or (
            "keine bei Einhaltung der Lizenz" if liz in QUELLOFFEN
            else "unbekannt — vor Verwendung klären"),
        "lizenz_fundort": fundort,
        "quelle": beleg,
        "ausgetreten": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "innen_kennwert": hashlib.sha256(
            json.dumps(a, sort_keys=True).encode()).hexdigest()[:16],
    }


def austreten() -> int:
    sperre = _sperre()
    if not sperre:
        print("  Keine Sperrliste — es tritt nichts aus.")
        return 1
    for d in (AUSSEN, QUARANTAENE):
        d.mkdir(parents=True, exist_ok=True)

    raus = drin = 0
    gruende: dict[str, int] = {}
    for p in sorted(INNEN.glob("*.json")):
        a = json.loads(p.read_text(encoding="utf-8"))
        ok, warum, aussen = pruefe(a, sperre)
        if ok:
            (AUSSEN / p.name).write_text(
                json.dumps(aussen, ensure_ascii=False, indent=2), encoding="utf-8")
            raus += 1
        else:
            (QUARANTAENE / p.name).write_text(json.dumps(
                {"id": a["id"], "titel_innen": a.get("titel"), "gruende": warum,
                 "geprueft": time.strftime("%Y-%m-%dT%H:%M:%S%z")},
                ensure_ascii=False, indent=2), encoding="utf-8")
            drin += 1
            for w in warum:
                schl = w.split(":")[0].split("(")[0].strip()
                gruende[schl] = gruende.get(schl, 0) + 1

    print(f"\n  {raus} ausgetreten, {drin} bleiben drinnen\n")
    for g, n in sorted(gruende.items(), key=lambda x: -x[1]):
        print(f"    {n:>4} × {g}")
    if drin:
        print("\n  Das ist kein Fehler. Was nicht austritt, ist nicht geprüft "
              "worden\n  und für gut befunden — es ist schlicht nicht belegt.")
    print()
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "austreten":
        sys.exit(austreten())
    if a and a[0] == "sperre":
        print(json.dumps(_sperre(), ensure_ascii=False, indent=2)); sys.exit(0)
    print(__doc__)
