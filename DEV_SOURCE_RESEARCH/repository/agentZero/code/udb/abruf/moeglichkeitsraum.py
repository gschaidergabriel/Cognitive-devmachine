#!/usr/bin/env python3
"""moeglichkeitsraum.py -- baut aus paket() einen MOEGLICHKEITSRAUM: eine
CONDENSED DERIVATIVE aus Hypothesen UND Gegenhypothesen, formuliert als
ERWARTUNGSFELD (was ist plausibel, was spricht dagegen) -- NIE als Antwort.
Der Verzehrer (VLM/Modell) muss UNTERSCHEIDEN, nicht BESTAETIGEN.

    NAIV      "das wissen wir -> such danach"           -> BESTAETIGUNG. faellt.
    RICHTIG   Hypothese + GEGENhypothese, verdichtet, als FELD formuliert.
              das Modell muss diskriminieren, nicht bestaetigen.
              die Gegenhypothese ist der Falsifikator, IM Prompt.

Baut auf udb.abruf.paket.paket() OHNE paket.py anzufassen -- eigene, neue
Datei, konsumiert nur seine Rueckgabe (dict rein/raus, kein SQL hier).
⚠️ paket.py wird von einer anderen Instanz gerade bearbeitet -- diese Datei
importiert paket() nur, aendert nichts an ihr.

INVARIANTE (Auftrag, F24): ⭐ EIN RAUM MIT NUR EINER LESART IST KEIN RAUM.
Fehlt eine Seite (Hypothese ODER Gegenseite), wird das EXPLIZIT gemeldet
("Gegenseite fehlt" / "Hypothesenseite fehlt") -- nie eine einseitige
Behauptung stillschweigend als Raum ausgeliefert. Genau das waere die
naive Fassung, die dieses Werkzeug ersetzen soll.

Verdichtung ist HIER deterministisch: dedupliziert, hart gekappt, woertliche
Auszuege aus paket() (kein eigener Modellaufruf beim Bauen). Grund: jede
Paraphrase ist ein neuer Erfindungskanal -- genau der Fehler, den dieses
Werkzeug abbauen soll, nicht vermehren. Trotzdem wird der ERFINDUNGSMELDER
aus verdichtung.py (zahl_marken/zahlen/schluessel) hier ECHT ausgefuehrt --
als mechanischer Beweis, nicht "sollte per Bauart stimmen": jede Zahl im
Ergebnis muss in mindestens einer paket()-Quelle dieser Anfrage stehen.
Importiert, nicht neu geschrieben (Auftrag: "keep it, do not reimplement it").
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Optional

sys.path.insert(0, "/opt/unifieddb")
sys.path.insert(0, "/opt/clayverse/werkzeug")

from udb.abruf.paket import paket  # noqa: E402  -- nur lesend benutzt, nichts geaendert
from verdichtung import zahl_marken, zahlen, schluessel  # noqa: E402  -- Erfindungsmelder, wiederverwendet

# ── Caps: hart, damit die Groesse NIE unbegrenzt waechst (F45: zuviel ist
# unumkehrbar). Grobe Zeichenbremse hier; die tatsaechliche Token-Kappung
# wird von moeglichkeitsraum_mess.py GEMESSEN (echter Tokenizer, nicht
# geschaetzt -- siehe zustand_mess.py-Konvention in diesem Repo).
CAP_SEITE = 6                    # max. Aussagen je Seite (Hypothese / Gegenseite)
CAP_ZEICHEN_JE_AUSSAGE = 220


def _kurz(text, cap: int = CAP_ZEICHEN_JE_AUSSAGE) -> str:
    t = " ".join(str(text or "").split())
    return t[:cap]


def _beleg_texte(beleg) -> list:
    """paket() traegt 'beleg' in ZWEI verschiedenen Formen: eine Liste von
    {'art','ref'}-Dicts (folgerung_beleg) ODER einen rohen String (kante.beleg,
    bis 200 Zeichen). Beide vorkommen lassen, keine annehmen."""
    if isinstance(beleg, list):
        return [str(b.get("ref", "")) for b in beleg if isinstance(b, dict)]
    if isinstance(beleg, str) and beleg:
        return [beleg]
    return []


def _aussage_text(e: dict) -> str:
    """gegenseite ist HETEROGEN: gegen_folg/art_gegen tragen 'aussage', aber
    die kante/graph_kante-Eintraege aus _gegenseite_ids() tragen KEINE --
    dort ist die KANTE SELBST die Behauptung (von/art/nach + Beleg). Ohne
    diese Umwandlung faellt jede kante-foermige Gegenseite in _seite() als
    leerer Text raus -- GENAU der Bug, der Kanten-Gegenseite unsichtbar
    machte, obwohl paket() sie geliefert hatte (gemessen beim Bau, siehe
    Baubericht)."""
    if e.get("aussage"):
        return str(e["aussage"])
    von, nach, art = e.get("von"), e.get("nach"), e.get("art")
    if von and nach and art:
        belege = _beleg_texte(e.get("beleg"))
        kern = "%s %s %s" % (von, art, nach)
        return (kern + " -- " + " / ".join(belege)) if belege else kern
    return ""


def _quelltext(eintraege: list) -> str:
    """Ein Fliesstext aller Quellzeilen dieser Anfrage -- das ist die
    Grundlage, gegen die der Erfindungsmelder jede Zahl im Ergebnis prueft."""
    teile = []
    for e in eintraege:
        teile.append(_aussage_text(e))
        teile.append(str(e.get("gilt_fuer", "")))
        teile.extend(_beleg_texte(e.get("beleg")))
        if e.get("von"):
            teile.append(str(e.get("von")))
        if e.get("nach"):
            teile.append(str(e.get("nach")))
    return " ".join(teile)


def _seite(eintraege: list, label: str) -> tuple:
    """Dedupliziert (nach Text), kappt hart auf CAP_SEITE. Gibt (behalten,
    Kappungsvermerke) zurueck -- die Vermerke werden offen ausgewiesen,
    wie 'politik' in paket() (drop_order/gedeckelt), nichts verschwindet
    spurlos."""
    gesehen: set = set()
    out = []
    vermerke = []
    uebersprungen_leer = 0
    for e in eintraege:
        txt = _kurz(_aussage_text(e))
        if not txt:
            uebersprungen_leer += 1
            continue
        if txt in gesehen:
            continue
        gesehen.add(txt)
        out.append({"text": txt, "ref": e.get("ref"), "art": e.get("art"),
                     "status": e.get("status")})
        if len(out) >= CAP_SEITE:
            break
    if len(eintraege) > len(out):
        vermerke.append("%s: %d von %d verwendet (Cap %d, Dubletten oder ohne jede Kennung "
                         "%d)" % (label, len(out), len(eintraege), CAP_SEITE, uebersprungen_leer))
    return out, vermerke


def _erfindungsmelder(seite: list, quellzahlen: set) -> tuple:
    """Reuse, nicht Neubau: jede Zahl in einer Aussage muss in einer
    paket()-Quelle dieser Anfrage stehen (verdichtung.zahl_marken/schluessel).
    Eine Aussage, die eine Zahl OHNE Quelle traegt, wird verworfen -- nicht
    das ganze Paket, nur diese eine Aussage."""
    behalten, verworfen = [], []
    for s in seite:
        marken = zahl_marken(s["text"])
        erfunden = [m for m in marken if not (schluessel(m) & quellzahlen)]
        if erfunden:
            verworfen.append("verworfen (Erfindungsmelder, Zahl ohne Quelle %r): %s"
                              % (erfunden, s["text"][:80]))
            continue
        behalten.append(s)
    return behalten, verworfen


def moeglichkeitsraum(text: str, *, budget: int = 8, wirt: Optional[str] = None,
                       conn=None, pkt: Optional[dict] = None) -> dict:
    """DIE Schnittstelle. Frage rein (caveman englisch oder deutsch, wie
    paket()), ein MOEGLICHKEITSRAUM raus -- oder ein expliziter Befund, warum
    keiner gebaut werden konnte. NIE eine einseitige Behauptung als Raum
    ausgegeben (Invariante)."""
    # ⚠️ Zeitnahme beginnt ERST NACH paket() -- das ist der Zusatzaufwand
    # DIESES Werkzeugs, nicht paket()s eigene Latenz (die steht separat als
    # pkt['latenz_us'] / basis['paket_latenz_us']). Wurde pkt schon uebergeben,
    # ist der Zusatz hier ohnehin nur die reine Verdichtung.
    if pkt is None:
        pkt = paket(text, budget=budget, wirt=wirt, conn=conn)
    t0 = time.perf_counter_ns()

    roh_hyp = pkt.get("hypothesen") or []
    roh_gegen = pkt.get("gegenseite") or []

    basis = {
        "paket_id": pkt.get("paket_id"),
        "paket_latenz_us": pkt.get("latenz_us"),
        "quelle_treffer": len(pkt.get("treffer") or []),
        "quelle_hypothesen": len(roh_hyp),
        "quelle_gegenseite": len(roh_gegen),
    }

    if not roh_hyp and not roh_gegen:
        return {
            "raum": None, "einseitig": None,
            "befund": "kein Material -- paket() lieferte weder Hypothese noch Gegenseite",
            **basis,
            "latenz_zusatz_us": int((time.perf_counter_ns() - t0) // 1000),
        }

    hyp_seite, hyp_vermerk = _seite(roh_hyp, "hypothesenseite")
    gegen_seite, gegen_vermerk = _seite(roh_gegen, "gegenseite")

    quelltext = _quelltext(roh_hyp) + " " + _quelltext(roh_gegen)
    quellzahlen = zahlen(quelltext)
    hyp_seite, hyp_raus = _erfindungsmelder(hyp_seite, quellzahlen)
    gegen_seite, gegen_raus = _erfindungsmelder(gegen_seite, quellzahlen)

    verworfen = hyp_vermerk + gegen_vermerk + hyp_raus + gegen_raus

    if not hyp_seite and not gegen_seite:
        return {
            "raum": None, "einseitig": None,
            "befund": "beide Seiten nach Pruefung leer (Dubletten/Erfindungsmelder) -- kein Raum",
            **basis, "verworfen": verworfen,
            "latenz_zusatz_us": int((time.perf_counter_ns() - t0) // 1000),
        }

    gegenseite_fehlt = len(gegen_seite) == 0
    hypothesenseite_fehlt = len(hyp_seite) == 0

    raum = {
        "feld": "moeglichkeitsraum",   # ein FELD, kein Ergebnis
        "plausibel_richtung": [s["text"] for s in hyp_seite],
        "plausibel_ref": [s["ref"] for s in hyp_seite if s.get("ref")],
        "spricht_dagegen": [s["text"] for s in gegen_seite],
        "spricht_dagegen_ref": [s["ref"] for s in gegen_seite if s.get("ref")],
        "hinweis": ("Hypothese UND Gegenhypothese zusammen -- keine Seite ist die Antwort, "
                    "keine Seite ist bevorzugt. Diskriminieren, nicht bestaetigen."),
    }
    if gegenseite_fehlt:
        raum["warnung"] = "Gegenseite fehlt -- nur Hypothesenseite vorhanden, KEIN vollstaendiger Raum"
    elif hypothesenseite_fehlt:
        raum["warnung"] = "Hypothesenseite fehlt -- nur Gegenseite vorhanden, KEIN vollstaendiger Raum"

    return {
        "raum": raum,
        "einseitig": bool(gegenseite_fehlt or hypothesenseite_fehlt),
        **basis,
        "verwendet_hypothesen": len(hyp_seite), "verwendet_gegenseite": len(gegen_seite),
        "verworfen": verworfen,
        "caps": {"seite": CAP_SEITE, "zeichen_je_aussage": CAP_ZEICHEN_JE_AUSSAGE},
        "latenz_zusatz_us": int((time.perf_counter_ns() - t0) // 1000),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frage")
    ap.add_argument("--budget", type=int, default=8)
    ap.add_argument("--wirt", default=None)
    a = ap.parse_args()
    r = moeglichkeitsraum(a.frage, budget=a.budget, wirt=a.wirt)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
