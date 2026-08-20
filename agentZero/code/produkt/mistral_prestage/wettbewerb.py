# -*- coding: utf-8 -*-
"""Numerische Auswahlstufe vor der Ausstrahlung (GWT-2 mit Zahl).

WARUM DIESES MODUL EXISTIERT
============================
Bis 2026-08-20 gab es zwei Zustaende, und beide waren kein globaler
Arbeitsraum:

  (1) Der Korpus wurde UNBEDINGT an den Auftrag gehaengt. Dann hatte die
      Auswahlinstanz null Kausalkraft -- Kontextstopfen, keine Zuendung.
  (2) Die Vorstufe durfte `broadcast_ids` frei nennen. Gemessen an acht
      privaten Sonden: sie waehlte im Schnitt 0,7 von 3 moeglichen Stellen
      und liess in 2 von 6 Faellen genau die Stelle liegen, die die Antwort
      trug. Eine Auswahl ohne pruefbaren Grund ist von Raten nicht zu
      unterscheiden.

Hier bekommt jeder Kandidat eine ZAHL, die protokolliert und nachgerechnet
werden kann. Die Vorstufe waehlt weiterhin -- aber aus einer Liste, die nach
einem offengelegten Mass sortiert ist, und sie kann nichts waehlen, was das
Mass ausgeschlossen hat.

    wert(k) = 0,35 * salienz(k) + 0,55 * relevanz(k) + 0,10 * neuheit(k)

* salienz  -- der Rang, den der Abruf selbst vergeben hat (1/(1+i)).
             Zwei Quellen (FTS und paket()) liefern unvergleichbare
             Rohwerte; der Rang ist das einzige gemeinsame Mass.
* relevanz -- Deckung der Inhaltswoerter der FRAGE in Titel + Ausschnitt.
             Deutsch bildet Komposita, deshalb zaehlt auch ein Wort, das als
             Teil eines laengeren Wortes vorkommt ("slug" in "leihmich-slug").
* neuheit  -- Abschlag fuer Stellen, die zuletzt schon ausgestrahlt wurden:
             basis / (1 + k * haeufigkeit). Nach LIDA (novelty.py), aber
             ueber ein Fenster echter Ausstrahlungen statt ueber Gewinner-IDs
             eines Freilauf-Taktes.

DIE ZUENDUNG HAT DREI HUERDEN -- ZWEI ABSOLUTE, EINE RELATIVE
-------------------------------------------------------------
  1. relevanz > 0 und mindestens MIN_GEDECKT gedeckte Woerter -- eine Stelle,
     die nur ein Allerweltswort mit der Frage teilt, ist kein Beleg FUER diese
     Frage, egal wie hoch der Abruf sie rankt. Hier scheitern fachfremde
     Fragen und blosse Hoeflichkeit (gemessen 3/3 bzw. 3/3 ohne Zuendung).
  2. wert >= BODEN -- gegen Zufallstreffer knapp ueber null.
  3. wert >= SCHWELLE_RELATIV * bester Wert -- die eigentliche Konkurrenz.

Damit ist "nichts wird ausgestrahlt" ein erreichbarer Zustand. Genau das
fehlt LIDAs `compete()` (argmax, auch bei Score 0) -- und ohne diesen
Zustand gibt es keine Zuendung, nur eine Umverteilung.
⚠️ Eine FESTE Latte auf `wert` hatten wir zuerst, und sie war falsch: `relevanz`
ist der Anteil der GANZEN Frage, den eine Stelle deckt, und eine praezise
gestellte Frage kann von ihrer richtigen Antwort gar nicht zur Haelfte gedeckt
werden. Gemessen: bei vier von acht Sonden zuendete nichts mehr, obwohl die
Antwort im Korpus stand. Die Latte bestrafte genau die genauesten Fragen.

DER RUECKKANAL (seit 2026-08-20)
-------------------------------
Bis hierher war die Auswahl gedaechtnislos: dieselbe Frage ergab immer dieselbe
Rangfolge, ganz gleich, ob eine ausgestrahlte Stelle jemals etwas genuetzt hat.
Damit war ein Zombie ohne Arbeitsraum von der vollen Anlage nicht zu
unterscheiden -- beide laufen deterministisch dieselbe Bahn. Ein Arbeitsraum,
dessen Inhalt die Zukunft nicht beruehrt, ist eine Anzeige, kein Kreislauf.

Jetzt gibt es zwei Rueckwege, und sie ziehen in verschiedene Richtungen:

  neuheit   daempft, was zuletzt schon dran war        (Abschlag, gegen Erstarrung)
  gelernt   hebt, was bei DIESEN Woertern schon getragen hat  (Bonus, fuer Passung)

DAS BELOHNUNGSSIGNAL IST NICHT ERFUNDEN, SONDERN GEMESSEN. Belohnt wird eine
Ausstrahlung genau dann, wenn Zero die Artikelkennung in seiner Antwort NENNT.
Das ist derselbe Nachweis, der schon die Sonden traegt: eine Verweigerung kann
keine Kennung nennen (belegt an 88 Antworten). Ein Modell, das nach seiner
eigenen Zufriedenheit gefragt wird, waere hier das falsche Messgeraet.

GRENZEN, ABSICHTLICH ENG GEZOGEN
  * Gelerntes kann eine Stelle INNERHALB der passenden Menge nach vorn holen,
    aber niemals eine unpassende hereinlassen: die harte Huerde `relevanz > 0`
    bleibt davor. Sonst wuerde ein einmal belohnter Artikel irgendwann auf
    jede Frage antworten -- der klassische Selbstlaeufer.
  * Gelernt wird nur an SELTENEN Woertern (idf >= IDF_LERN_MIN). An "lauf"
    (steckt in 43 % aller Zeilen) zu lernen hiesse, Allerweltssprache zu lernen.
  * Alles verfaellt (VERFALL je Buchung). Was nicht wieder bestaetigt wird,
    verschwindet -- ein Bonus ohne Verfall ist eine Behauptung ueber die
    Zukunft, die nie ueberprueft wird.
  * Geschrieben wird NUR bei `record_via_turnlifecycle=True`. Eine Messreihe
    darf sich ihr eigenes Signal nicht anfuettern.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

# ⭐ SALIENZ IST KEIN EIGENES SIGNAL -- gegengeprueft 2026-08-20, mit Zahlen:
# der Traeger (die Zeile, die die Antwort haelt) stand schon in der reinen
# Abrufreihenfolge in 7 von 8 Faellen auf Platz 1; mit der vollen Formel
# ebenfalls 7/8; mit relevanz ALLEIN 8/8. Salienz ist nichts als die
# Reihenfolge, die der Abruf ohnehin vergeben hat -- als Summand verduennt sie
# nur das einzige neue Signal. Schlimmer: bei 20 kuenstlich gemischten
# Abrufreihenfolgen je Sonde liess dieselbe Kandidatenmenge zwischen 1 und 4
# Stellen durch. Damit haette die ZUENDUNGSGROESSE an einer willkuerlichen
# Position gehangen. Der Rang bleibt -- aber nur als Stichentscheid bei
# Gleichstand, nicht als Anteil am Wert.
GEWICHT_SALIENZ = 0.0
# ⚠️ Die drei Gewichte muessen sich zu 1,0 summieren, sonst bedeutet die
# Schwelle nicht mehr, was sie sagt (siehe _gewichte). Im frischen Zustand --
# keine Ausstrahlungsgeschichte, keine Erfahrung -- faellt ohnehin alles an
# relevanz zurueck, dort gilt weiter genau die kalibrierte 0,25.
GEWICHT_RELEVANZ = 0.70
# Der Neuheits-Abschlag wirkt NUR, wenn es eine Ausstrahlungsgeschichte gibt.
# Ohne sie ist neuheit fuer jeden Kandidaten 1,0, also eine Konstante, also
# rangneutral -- gemessen in 100 % der Versuchszuege, weil die Apparaturen
# record_via_turnlifecycle=False setzen. Statt eine wirkungslose Konstante
# mitzuschleppen, wird das Gewicht dann auf relevanz umgelegt (siehe
# _gewichte()) -- die Formel sagt damit die Wahrheit ueber das, was rechnet.
GEWICHT_NEUHEIT = 0.10
# ⚠️⚠️ UMGEBAUT 2026-08-20 abends, nachdem die absolute Schwelle bei VIER von
# acht Sonden NICHTS mehr zuliess, obwohl die Antwort nachweislich im Korpus
# stand. Ursache: `relevanz` ist der Anteil der GESAMTEN Frage, den eine Stelle
# deckt. Eine lange, praezise Frage ("welches verzeichnis auf dem vps darf man
# nicht direkt editieren, weil der naechste push es ueberschreibt", sieben
# Inhaltswoerter) kann von einer richtigen Stelle gar nicht zu einem Viertel
# gedeckt werden -- die Stelle beantwortet die Frage, wiederholt sie aber nicht.
# Gemessen: bester Wert 0,197 bei einer Frage, deren Antwort dastand.
# Eine feste Latte bestraft damit genau die Fragen, die am genauesten gestellt
# sind. Das ist ein Messfehler, kein Vorsichtsprinzip.
#
# ⭐ DIE ZUENDUNG IST RELATIV, NICHT ABSOLUT -- und das ist naeher an dem, was
# GWT beschreibt: ein Inhalt wird bewusst, weil er die anderen SCHLAEGT, nicht
# weil er eine von aussen gesetzte Marke reisst. Drei Huerden, jede mit einem
# eigenen Zweck:
#   1. relevanz > 0 und MIN_GEDECKT gedeckte Woerter -- es muss ueberhaupt ein
#      Beleg FUER DIESE Frage sein. Das ist die Huerde, an der fachfremde
#      Fragen und blosse Hoeflichkeit scheitern (gemessen 3/3 bzw. 3/3 null),
#      und sie bleibt absolut.
#   2. wert >= BODEN -- gegen Zufallstreffer knapp ueber null.
#   3. wert >= RELATIV * bester Wert -- die eigentliche Konkurrenz. Wer weit
#      hinter dem Sieger liegt, faellt heraus, ganz gleich wie das Feld liegt.
# ⭐ ABGELESEN, nicht gewaehlt: Sweep 0,30..1,00 in Schritten von 0,05 ueber
# dieselben drei Fragesorten. Der Traeger kommt bei JEDEM Wert durch (8/8, kein
# Nullzug), fachfremd und Hoeflichkeit zuenden bei jedem Wert nichts (3/3) --
# die absolute Huerde erledigt beides allein. Der relative Abstand regelt
# ausschliesslich die BEGLEITUNG: 1,38 Stellen bei 0,30-0,40 · 1,25 bei
# 0,45-0,50 · 1,00 ab 0,55 (reiner Sieger, keine Koalition mehr).
# 0,50 heisst in einem Satz: "mindestens halb so gut wie der Sieger". Das ist
# eine Aussage, die man pruefen kann, und sie laesst eine kleine Koalition zu,
# ohne Fuellmaterial hereinzulassen.
SCHWELLE_RELATIV = 0.50
BODEN = 0.08
# ⭐ NICHT GERATEN, SONDERN ABGELESEN. Schwellensweep 0,10..0,40 in Schritten
# von 0,02 ueber drei Fragesorten (A: Beleg im Korpus, B: fachfremd,
# C: blosse Hoeflichkeit). Bis 0,28 kommt in A der Traeger 8/8 durch und kein
# Zug faellt auf null; ab 0,30 faellt der erste Traeger raus (7/8), ab 0,34
# nur noch 5/8. B faellt bereits ab 0,22 auf 0,33 angebotene Stellen (2/3 der
# Fragen strahlen nichts aus). Die Mitte des Plateaus ist 0,25 -- dort ist der
# Abstand zwischen "Beleg da" und "fachfremd" am groessten, ohne dass die
# Trennung an der zweiten Nachkommastelle haengt.
# ⚠️ NICHT MEHR DIE ZULASSUNG -- die entscheiden BODEN und SCHWELLE_RELATIV
# (siehe oben). Der Wert bleibt als abgelesene Kennzahl stehen, weil er die
# Kalibrierung des absoluten Sweeps festhaelt: bis 0,28 kam der Traeger 8/8
# durch, ab 0,30 fiel der erste heraus. Er beschreibt also, wo eine feste Latte
# haette liegen muessen -- und dass sie selbst dort nicht getaugt hat.
SCHWELLE_ABGELESEN_2026_08_20 = 0.25
# Eine EINZELNE gedeckte Wortuebereinstimmung ist keine Passung. Ohne diese
# Regel strahlte "danke, das war hilfreich" eine Stelle aus (ein gedecktes Wort
# von zweien = relevanz 0,5) -- eine Zuendung ohne Sachfrage, also genau das
# falsch-positive Feuern, das die Schwelle verhindern soll.
MIN_GEDECKT = 2

# ── Rueckkanal ───────────────────────────────────────────────────────────
GEWICHT_LERNEN = 0.20
ALPHA_HOCH = 0.30        # Schritt bei Belohnung, saettigend gegen 1,0
ALPHA_RUNTER = 0.15      # Schritt bei ausgebliebener Belohnung
VERFALL = 0.98           # je Buchung, auf ALLES -- nach LIDA (learning.py: 0.995,
                         # dort aber je Takt bei 8 Hz; hier ist ein Takt ein ZUG)
IDF_LERN_MIN = 0.40      # nur seltene Woerter tragen eine Lehre
LERN_MIN = 0.02          # darunter loeschen statt mitschleppen
NEUHEIT_K = 0.6
NEUHEIT_FENSTER = 50
ANGEBOT_MAX = 3          # so viele Stellen duerfen hoechstens ausgestrahlt werden

# Woerter, die in jeder Frage stehen koennen und nichts unterscheiden.
_STOPP = frozenset("""
aber alle allem allen aller alles also andere anderem anderen anderer anderes
auch auf aus bei beim bin bist bitte damit dann darf das dass dem den der des
deshalb dich die dies diese diesem diesen dieser dieses dir doch dort du durch
ein eine einem einen einer eines einfach er es etwa etwas euch fuer für gab
geben gibt hab habe haben hat hatte hier ich ihm ihn ihnen ihr ihre im in ist
kann kein keine koennen können mach machen man mehr mein mich mir mit muss
musst nach nicht noch nur ob oder ohne sehr sein seine sich sie sind so soll
sollen sondern ueber über um und uns unser unter viel vom von vor waere wäre
war waren was wann warum weil welche welchem welchen welcher welches wenn wer
werden wie wieder wir wird wo wurde wurden zu zum zur zwar
""".split())

_WORT = re.compile(r"[a-z0-9äöüß_-]{3,}")

# ⭐ UMLAUTE VEREINHEITLICHEN -- gemessen 2026-08-20, und es hat eine ganze
# Messreihe gekippt: das Gedaechtnis speicherte "Pruefrechner heisst
# quirlbaum-1" als "Prüfrechner heißt quirlbaum-1" (die Extraktion schreibt
# echte Umlaute), die Frage kam als "wie heisst mein Pruefrechner?" herein.
# Kein einziges Wort traf, die Stelle wurde nicht ausgestrahlt, und Zero
# antwortete aus dem Profil statt aus dem Gedaechtnis.
# Beide Schreibweisen sind im Bestand echt und beide bleiben es -- Menschen
# tippen mal so, mal so, und die Anlage schreibt selbst Umlaute. Also wird
# verglichen, nicht umerzogen.
_UMLAUTE = ((chr(228), "ae"), (chr(246), "oe"), (chr(252), "ue"), (chr(223), "ss"))


def _flach(t: str) -> str:
    """Umlautfreie Vergleichsform. Nur zum Vergleichen, nie zum Anzeigen."""
    t = (t or "").lower()
    for zeichen, ersatz in _UMLAUTE:
        t = t.replace(zeichen, ersatz)
    return t


def _worte(text: str) -> list[str]:
    """Inhaltswoerter einer Frage, klein, ohne Allerweltswoerter.

    Bindestrich-Zusammensetzungen zaehlen DOPPELT: das ganze Wort und seine
    Glieder. "leihmich-slug" faende sonst die Stelle nicht, die von
    "LEIHMICH_SLUGS" handelt -- gemessen genau dieser Fall.
    """
    raus, gesehen = [], set()
    for w in _WORT.findall(_flach(text)):
        for teil in [w] + [t for t in re.split(r"[-_]", w) if len(t) >= 3]:
            if teil not in _STOPP and teil not in gesehen:
                gesehen.add(teil)
                raus.append(teil)
    return raus


_KURZ = 4          # darunter zaehlt nur exakte Wortgleichheit
_STAMM = 6         # ab hier wird auf den Wortstamm verglichen (Beugung)
_INNEN = 5         # ab dieser Stammlaenge zaehlt auch ein Treffer MITTEN im Wort


def _deckt(wort: str, heu: str) -> bool:
    """Kommt `wort` in `heu` vor -- und zwar so, dass es etwas bedeutet?

    Gegengeprueft an 40 echten Korpuszeilen: freie Teilzeichenkette ist zu
    billig. "lauf" steckte in 17 von 40 Zeilen (43 %), "art" in 7, "ort" in 6 --
    eine thematisch voellig fremde Zeile erreichte gegen "welche art von zug
    ist das" die relevanz 0,50. Deshalb:

      * kurze Woerter (< _KURZ Zeichen) nur als ganzes Wort,
      * laengere zusaetzlich als WORTANFANG -- das faengt die deutsche
        Flexion und Komposition ("slug" in "LEIHMICH_SLUGS", "verzeichnis" in
        "Verzeichnisses"), ohne jedes Wort in jedem Wort zu finden.
    """
    # Drei Stufen, und die Grenzen sind nicht gefuehlt, sondern gemessen.
    if len(wort) < _KURZ:
        # "art", "ort", "lauf" -- solche Woerter stecken in jedem zweiten Satz
        # (gemessen: "lauf" in 17 von 40 echten Korpuszeilen). Nur als ganzes
        # Wort, sonst passt jede Stelle zu jeder Frage.
        return re.search(r"\b" + re.escape(wort) + r"\b", heu) is not None
    if len(wort) < _STAMM:
        # Mittellang: Wortanfang genuegt, Beugung noch nicht abschneiden.
        return re.search(r"(?:\b|[a-z0-9]*[_-])" + re.escape(wort), heu) is not None
    # ⭐ Lange Woerter: Stamm statt Wort (deutsche Beugung -- die Frage steht im
    # Plural, die Stelle im Singular) UND Treffer auch INNERHALB eines Wortes.
    # Deutsch schreibt Zusammensetzungen ohne Trennzeichen: "wurzeln" muss
    # "Domainwurzel" finden, und dort steht kein Wortanfang davor. Gemessen an
    # genau diesem Paar -- die Frage nach den eigenen Webserver-Wurzeln fand
    # ihre eigene Antwort nicht. Ab dieser Laenge ist zufaellige Enthaltung
    # unwahrscheinlich; unterhalb bleibt es beim Wortanfang.
    stamm = wort[:-2]
    if len(stamm) < _INNEN:
        return re.search(r"(?:\b|[a-z0-9]*[_-])" + re.escape(stamm), heu) is not None
    return stamm in heu


def relevanz(treffer: dict[str, Any], frage_worte: list[str],
             gewichte: dict | None = None) -> float:
    """Gewichtete Deckung der Fragewoerter in Titel/Ausschnitt/Art/Sphaere.

    `gewichte` ist die Seltenheit je Wort (IDF, siehe idf_gewichte). Ohne sie
    zaehlt jedes Wort gleich -- dann schlaegt ein Allerweltswort wie "lauf"
    genauso zu Buche wie "testpflicht", und das ist genau der gemessene
    Fehlbefund.
    """
    if not frage_worte:
        return 0.0
    heu = _flach(" ".join(str(treffer.get(f) or "")
                          for f in ("titel", "ausschnitt", "art", "sphaere")))
    if not heu.strip():
        return 0.0
    g = gewichte or {}
    summe = sum(g.get(w, 1.0) for w in frage_worte) or 1.0
    gedeckt = [w for w in frage_worte if _deckt(w, heu)]
    if len(frage_worte) >= MIN_GEDECKT and len(gedeckt) < MIN_GEDECKT:
        return 0.0
    return sum(g.get(w, 1.0) for w in gedeckt) / float(summe)


def neuheit(artikel_id: Any, haeufigkeiten: dict) -> float:
    """basis / (1 + k * wie oft zuletzt ausgestrahlt) -- nach LIDA."""
    n = int((haeufigkeiten or {}).get(str(artikel_id or ""), 0))
    return 1.0 / (1.0 + NEUHEIT_K * n)


def _gewichte(haeufigkeiten: dict | None,
              gelernte: dict | None = None) -> tuple[float, float, float]:
    """(relevanz, neuheit, gelernt) -- ungenutzte Anteile fallen an relevanz.

    Eine Konstante im Summanden ist keine Bewertung. Ist `haeufigkeiten` leer,
    hat JEDER Kandidat neuheit=1,0; das Gewicht wuerde dann nur den Absolutwert
    anheben und die Schwelle heimlich absenken (aus 0,32 waere faktisch 0,22
    geworden -- gemessen). Ist nichts gelernt, gilt dasselbe fuer den
    Lernanteil, nur mit 0 statt 1. Beides wird umgelegt statt mitgeschleppt,
    damit die Summe immer 1,0 ist und die Schwelle bedeutet, was sie sagt.
    """
    rel, neu, lern = GEWICHT_RELEVANZ, GEWICHT_NEUHEIT, GEWICHT_LERNEN
    if not haeufigkeiten:
        rel += neu; neu = 0.0
    if not gelernte:
        rel += lern; lern = 0.0
    return rel, neu, lern


def gelernt(artikel_id: Any, frage_worte: list, gelernte: dict | None) -> float:
    """Wie gut hat DIESE Stelle bei DIESEN Woertern bisher getragen? 0..1.

    Gemittelt ueber die Fragewoerter, fuer die es ueberhaupt eine Erfahrung
    gibt -- nicht ueber alle. Sonst verduennt jedes neue Wort das Gelernte,
    und eine lange Frage koennte nie von Erfahrung profitieren.
    """
    if not gelernte or not frage_worte:
        return 0.0
    aid = str(artikel_id or "")
    werte = [gelernte[(w, aid)] for w in frage_worte if (w, aid) in gelernte]
    return sum(werte) / len(werte) if werte else 0.0


def bewerten(korpus: list, frage: str, haeufigkeiten: dict | None = None,
             idf: dict | None = None, gelernte: dict | None = None) -> list[dict[str, Any]]:
    """Alle Korpustreffer mit Zahl versehen, absteigend sortiert.

    Liefert NEUE dicts -- der uebergebene Korpus bleibt unangetastet, damit
    andere Verbraucher derselben world-Referenz nichts Veraendertes sehen.
    """
    fw = _worte(frage)
    g_rel, g_neu, g_lern = _gewichte(haeufigkeiten, gelernte)
    raus: list[dict[str, Any]] = []
    echte = [t for t in (korpus or []) if isinstance(t, dict)]
    for i, t in enumerate(echte):
        sal = 1.0 / (1.0 + i)
        rel = relevanz(t, fw, idf)
        neu = neuheit(t.get("artikel_id"), haeufigkeiten or {})
        ler = gelernt(t.get("artikel_id"), fw, gelernte)
        wert = GEWICHT_SALIENZ * sal + g_rel * rel + g_neu * neu + g_lern * ler
        k = dict(t)
        k["gw_salienz"] = round(sal, 3)
        k["gw_relevanz"] = round(rel, 3)
        k["gw_neuheit"] = round(neu, 3)
        k["gw_gelernt"] = round(ler, 3)
        k["gw_wert"] = round(wert, 3)
        # Vorlaeufig: nur die absoluten Huerden. Die relative faellt erst,
        # wenn das ganze Feld bewertet ist -- eine Konkurrenz laesst sich nicht
        # Kandidat fuer Kandidat entscheiden.
        k["gw_zugelassen"] = bool(rel > 0.0 and wert >= BODEN)
        raus.append(k)
    # Bei Gleichstand entscheidet die Abrufreihenfolge -- als STICHENTSCHEID,
    # nicht als Anteil am Wert (siehe Kopf).
    for i, k in enumerate(raus):
        k["_i"] = i
    raus.sort(key=lambda k: (-k["gw_wert"], k["_i"]))
    for k in raus:
        k.pop("_i", None)
    for rang, k in enumerate(raus, 1):
        k["gw_rang"] = rang
    # Jetzt die Konkurrenz: gemessen am Besten, der die absoluten Huerden
    # genommen hat. Nimmt sie keiner, zuendet nichts -- und das ist dann eine
    # Aussage ueber die Frage, nicht ueber die Latte.
    bester = max((k["gw_wert"] for k in raus if k["gw_zugelassen"]), default=0.0)
    for k in raus:
        if k["gw_zugelassen"] and k["gw_wert"] < SCHWELLE_RELATIV * bester:
            k["gw_zugelassen"] = False
        k["gw_abstand"] = round(k["gw_wert"] / bester, 3) if bester else 0.0
    return raus


# Felder, die eine Kandidatenzeile im PRAEBEWUSSTEN VORRAT tragen darf.
# Alles andere -- vor allem `ausschnitt` -- ist INHALT und gehoert erst in den
# Arbeitsraum, nachdem gewaehlt wurde.
_KENNUNGSFELDER = ("artikel_id", "titel", "art", "sphaere", "quelle", "treffer_art",
                   "gw_rang", "gw_wert", "gw_relevanz", "gw_salienz", "gw_neuheit",
                   "gw_gelernt", "gw_zugelassen", "gw_quelle", "gw_abstand")


# ── EIN Arbeitsraum fuer alle Quellen ────────────────────────────────────
# ⭐⭐ DER GROESSTE GEMESSENE MANGEL, und er stand von Anfang an in den Zahlen:
# der Wettbewerb regelte NUR den Korpus. Gedaechtnis, Gespraechsverlauf,
# Kollisionen und Lesarten gingen unbedingt in den Kontext, das Profil
# (8480 Zeichen) und die Identitaet (5535) sogar an jeder Kappung vorbei.
# Gemessen am 20.08.: der erklaerte Engpass von 10.000 Zeichen begrenzte einen
# tatsaechlichen Kontext von 17.878 -- bei "Kappung 0" sah die Vorstufe immer
# noch 8790 Zeichen. Eine Kapazitaetsgrenze, die vier Fuenftel des Inhalts
# nicht anfasst, ist keine.
#
# Ein globaler Arbeitsraum heisst: ALLE Quellen bewerben sich um DIESELBEN
# wenigen Plaetze, nach demselben Mass, an derselben Schwelle. Was gewinnt,
# wird ausgestrahlt; was verliert, bleibt im praebewussten Vorrat abrufbar,
# aber ungesendet.
#
# AUSGENOMMEN bleiben genau zwei Dinge, und aus einem angebbaren Grund:
# `canonical_identity` und `anwesender_mensch` sind nicht INHALT, sondern
# RAHMEN -- wer spricht und mit wem. Ohne sie ist kein Zug deutbar, sie stehen
# bei jeder Frage gleich, und sie konkurrieren deshalb um nichts.
# ⭐⭐⭐ BUCHFUEHRUNG IST KEIN GEDAECHTNIS. Gemessen 2026-08-20 an einer echten
# Kopie: von 152 Eintraegen in `durable_memory` sind **116 `compression_receipt`**
# -- reine Pruefsummen ohne Inhalt, 76 %. Weil die Liste nach Zeit sortiert ist
# und je Zug mehrere Quittungen anfallen, waren **10 der 12 juengsten Eintraege**
# Hashes. Der Satz "Pruefrechner heisst quirlbaum-8", eine Minute alt, fiel aus
# jedem Deckel heraus.
# Folge, gemessen: bei "wie heisst mein Pruefrechner?" enthielt KEINER von 16
# Bewerbern das Kennwort. Nicht die Bewertung war zu schwach -- die richtige
# Stelle stand gar nicht zur Wahl.
# Das trifft nicht nur den Arbeitsraum: dieselbe Liste geht (gedeckelt) auch in
# den Kontext der Vorstufe. Drei Viertel des Gedaechtnisses, das die Anlage bei
# jeder Frage mitschleppt, sind Hashes.
_BUCHFUEHRUNG = ("compression_receipt", "checkpoint", "digest")
_HASH = re.compile(r"^[0-9a-f]{24,}$")


def _ist_buchfuehrung(m: dict) -> bool:
    """Quittung statt Erinnerung -- kann keine Frage beantworten.

    Zwei Kriterien, damit kuenftige Varianten nicht wieder durchrutschen: die
    bekannte Art, UND eine Wertform, die nichts als eine Pruefsumme sein kann.
    """
    if str(m.get("kind") or "").strip().lower() in _BUCHFUEHRUNG:
        return True
    wert = " ".join(str(m.get("value") or "").split())
    return bool(_HASH.match(wert.lower()))


QUELLEN_DECKEL = {"korpus": 6, "gedaechtnis": 8, "verlauf": 3,
                  "kollision": 3, "lesart": 4, "selbstbild": 12}
_KANDIDAT_TEXT_MAX = 600


def _kennung(praefix: str, text: str) -> str:
    """Stabile Kennung aus dem INHALT, nicht aus der Position.

    ⚠️ Vorher hiessen die Bewerber `gedaechtnis:0`, `verlauf:1` und so fort --
    nach ihrer Stelle in der Liste. Das hat zwei Folgen, und beide sind
    schlimm: dieselbe Kennung meint in zwei Zuegen etwas anderes, und der
    Lern-Rueckkanal sammelt seine Erfahrung deshalb an einer Nummer statt an
    einem Inhalt. Was er ueber `gedaechtnis:2` lernt, trifft im naechsten Zug
    einen fremden Eintrag. Eine Kennung, die wandert, ist keine Kennung.
    """
    import hashlib
    kern = " ".join(str(text or "").split()).lower()[:400]
    return f"{praefix}:{hashlib.sha1(kern.encode('utf-8')).hexdigest()[:8]}"


def _kurzform(x: Any, n: int = _KANDIDAT_TEXT_MAX) -> str:
    t = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, default=str)
    t = " ".join(str(t).split())
    return t[:n]


def kandidaten(world: dict[str, Any]) -> list[dict[str, Any]]:
    """Alle Quellen in EINER Bewerberliste, in derselben Form.

    Die Form ist die des Korpustreffers (`artikel_id`/`titel`/`ausschnitt`/
    `art`/`sphaere`), damit `relevanz` ueberall dasselbe rechnet und kein
    Bewerber wegen seiner Herkunft anders behandelt wird. `art` traegt die
    Quelle -- so bleibt im Protokoll sichtbar, WER den Platz gewonnen hat.
    """
    raus: list[dict[str, Any]] = []

    for t in (world.get("corpus") or [])[:QUELLEN_DECKEL["korpus"]]:
        if isinstance(t, dict) and t.get("artikel_id"):
            k = dict(t)
            # Form vereinheitlichen: `relevanz` liest genau diese Felder, und
            # ein Bewerber, dem eines fehlt, wuerde still schlechter bewertet
            # als einer aus derselben Quelle, dem es nicht fehlt.
            k.setdefault("titel", "")
            k.setdefault("ausschnitt", "")
            k.setdefault("art", "wissen")
            k.setdefault("sphaere", "")
            k["gw_quelle"] = "korpus"
            raus.append(k)

    # Erst sieben, DANN deckeln -- sonst frisst die Buchfuehrung den Deckel auf,
    # bevor die erste echte Erinnerung an die Reihe kommt.
    _echt = [m for m in (world.get("durable_memory") or [])
             if isinstance(m, dict) and not _ist_buchfuehrung(m)]
    for i, m in enumerate(_echt[:QUELLEN_DECKEL["gedaechtnis"]]):
        wert = _kurzform(m.get("value"))
        if not wert:
            continue
        raus.append({
            "artikel_id": _kennung("gedaechtnis", wert),
            "titel": f"{m.get('kind') or 'Notiz'} ueber {m.get('subject') or 'unbekannt'}",
            "ausschnitt": wert, "art": "gedaechtnis", "sphaere": "person",
            "gw_quelle": "gedaechtnis", "gw_roh": m})

    for i, z in enumerate((world.get("own_recent") or [])[:QUELLEN_DECKEL["verlauf"]]):
        text = _kurzform(z.get("content") if isinstance(z, dict) else z)
        if not text:
            continue
        raus.append({
            "artikel_id": _kennung("verlauf", text),
            "titel": "frueherer Zug in diesem Gespraech",
            "ausschnitt": text, "art": "verlauf", "sphaere": "gespraech",
            "gw_quelle": "verlauf"})

    for i, c in enumerate((world.get("cross_session_collision") or [])[:QUELLEN_DECKEL["kollision"]]):
        text = _kurzform(c)
        if not text:
            continue
        raus.append({
            "artikel_id": _kennung("kollision", text), "titel": "Kollision mit einer anderen Sitzung",
            "ausschnitt": text, "art": "kollision", "sphaere": "gespraech",
            "gw_quelle": "kollision"})

    for i, h in enumerate((world.get("hyperposition") or [])[:QUELLEN_DECKEL["lesart"]]):
        text = _kurzform(h)
        if not text:
            continue
        raus.append({
            "artikel_id": _kennung("lesart", text), "titel": "gleichzeitig gueltige Lesarten",
            "ausschnitt": text, "art": "lesart", "sphaere": "weltmodell",
            "gw_quelle": "lesart"})

    return raus


# ── Das Selbstbild als Bewerber ──────────────────────────────────────────
# ⭐⭐ GEMESSEN 2026-08-20: `canonical_identity` belegt 5541 Zeichen von rund
# 14.500 und steht bei JEDER Frage gleich da -- zusammen mit Profil (4308) und
# anwesendem Menschen (1099) sind das rund vier Fuenftel des Kontexts, die
# nichts mit der gestellten Frage zu tun haben. Der Korpus, das einzige
# Frageabhaengige, bekommt 1864.
#
# Ein globaler Arbeitsraum ohne diese Zahl anzugehen waere Kosmetik: die
# Kapazitaetsgrenze regelte dann weiter nur den kleinsten Posten.
#
# ABER: das Selbstbild ganz wegzunehmen waere falsch. Ein Teil davon IST
# Rahmen -- wer bin ich, was darf ich, mit wem spreche ich. Ohne das ist kein
# Zug deutbar. Deshalb wird geteilt statt gekuerzt:
#   * der KERN (die ersten Absaetze bis KERN_ZEICHEN) bleibt unbedingt stehen,
#   * jeder weitere Absatz wird ein Bewerber wie jeder andere und muss sich
#     ueber Passung zur Frage qualifizieren.
# Eine Frage nach Rechten holt den Absatz ueber Rechte; eine Frage nach einem
# Dateipfad holt ihn nicht. Das ist derselbe Mechanismus wie beim Korpus, und
# er braucht keine zweite Begruendung.
KERN_ZEICHEN = 700
_ABSATZ_MIN = 80          # kuerzere Stuecke sind Ueberschriften, keine Aussagen


def selbstbild_teilen(text: str, kern_zeichen: int = KERN_ZEICHEN):
    """(Kern, Bewerber) -- der Kern bleibt, der Rest konkurriert.

    Getrennt wird an Absatzgrenzen, nie mitten im Satz: ein abgeschnittenes
    Selbstbild ist schlimmer als ein kurzes (gemessen am Korpus, wo genau das
    die Antwort verschluckt hat).
    """
    text = str(text or "")
    if not text.strip():
        return text, []
    absaetze = [a.strip() for a in re.split(r"\n\s*\n", text) if a.strip()]
    kern, rest, laenge = [], [], 0
    for a in absaetze:
        if not kern or (laenge + len(a) <= kern_zeichen and not rest):
            kern.append(a); laenge += len(a)
        else:
            rest.append(a)
    bewerber = []
    for i, a in enumerate(rest):
        if len(a) < _ABSATZ_MIN:
            # zu kurz, um sich zu bewerben -- bleibt beim Kern, statt verloren
            # zu gehen. Ein Bewerber, der nie gewinnen kann, ist kein Bewerber.
            kern.append(a)
            continue
        kopf = " ".join(a.split())[:70]
        bewerber.append({
            "artikel_id": _kennung("selbstbild", a),
            "titel": f"Selbstbild: {kopf}",
            "ausschnitt": _kurzform(a, 900),
            "art": "selbstbild", "sphaere": "identitaet",
            "gw_quelle": "selbstbild"})
    return "\n\n".join(kern), bewerber


def volltexte(kand: list) -> dict[str, str]:
    """Kennung -> Text, fuer die Materialisierung NACH der Wahl."""
    return {str(k.get("artikel_id")): str(k.get("ausschnitt") or "")
            for k in (kand or []) if isinstance(k, dict) and k.get("artikel_id")}


def nur_kennung(bewertet: list) -> list[dict[str, Any]]:
    """Kandidaten ohne Inhalt -- der eigentliche Engpass.

    ⭐ GEMESSEN 2026-08-20, und es war der wichtigste Befund des Tages: mit
    erzwungen LEEREM Arbeitsraum antwortete die Anlage trotzdem richtig, MIT
    Quellenangabe. Der Grund ist keine Zauberei, sondern Bauart: die Vorstufe
    WAEHLT nicht nur, sie SCHREIBT auch den Auftrag an Zero -- und sie sah den
    vollen `ausschnitt` jedes Korpustreffers. Sie konnte den Inhalt also selbst
    weitererzaehlen, an der Auswahl vorbei. Ein Engpass, den der Waehler
    umgehen kann, ist keiner; jede Messung an `broadcast_ids` haette dann nur
    gezeigt, wie gut die Vorstufe erzaehlt.

    Deshalb sieht sie hier nur noch: Kennung, Titel, Art -- und die ZAHL, die
    der Wettbewerb vergeben hat. Genug, um zu waehlen. Zu wenig, um zu
    antworten. Der Volltext kommt ausschliesslich ueber die Materialisierung
    der gewaehlten Kennungen (siehe pipeline._mit_arbeitsraum) und liegt bis
    dahin ausserhalb des Arbeitsraums.

    Der Wert selbst ist auf dem VOLLEN Treffer gerechnet worden, bevor hier
    gekuerzt wird -- die Auswahl verliert also keine Grundlage, nur die
    Moeglichkeit, sie zu umgehen.
    """
    raus = []
    for k in (bewertet or []):
        if not isinstance(k, dict):
            continue
        raus.append({f: k[f] for f in _KENNUNGSFELDER if f in k})
    return raus


def zugelassene_ids(bewertet: list) -> list[str]:
    """Die Kennungen, die ausgestrahlt werden DUERFEN -- hoechstens ANGEBOT_MAX."""
    return [str(k.get("artikel_id")) for k in (bewertet or [])
            if isinstance(k, dict) and k.get("gw_zugelassen") and k.get("artikel_id")][:ANGEBOT_MAX]


def buchen(store, session_id, turn_id, bewertet: list, gewaehlt: list) -> None:
    """Wettbewerb und Ausstrahlung protokollieren. Darf einen Zug NIE kippen.

    Zwei Tabellen, weil es zwei verschiedene Fragen sind: `gw_wettbewerb`
    beantwortet "wie stand es zur Wahl", `gw_ausstrahlung` beantwortet "was
    ging tatsaechlich raus". Ohne die erste laesst sich nie pruefen, ob die
    zweite eine Auswahl war oder nur die immer gleiche Liste.
    """
    try:
        gew = {str(g) for g in (gewaehlt or [])}
        jetzt = time.time()
        store.db.executescript(
            "CREATE TABLE IF NOT EXISTS gw_wettbewerb("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,"
            "  turn_id TEXT, session_id TEXT, artikel_id TEXT, rang INTEGER,"
            "  salienz REAL, relevanz REAL, neuheit REAL, wert REAL,"
            "  zugelassen INTEGER, gewaehlt INTEGER);"
            "CREATE TABLE IF NOT EXISTS gw_ausstrahlung("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,"
            "  turn_id TEXT, session_id TEXT, artikel_id TEXT, wert REAL);"
            "CREATE INDEX IF NOT EXISTS gw_ausstrahlung_ts ON gw_ausstrahlung(ts);")
        for k in (bewertet or []):
            if not isinstance(k, dict):
                continue
            aid = str(k.get("artikel_id") or "")
            store.db.execute(
                "INSERT INTO gw_wettbewerb(ts,turn_id,session_id,artikel_id,rang,"
                "salienz,relevanz,neuheit,wert,zugelassen,gewaehlt) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (jetzt, turn_id, session_id, aid, k.get("gw_rang"),
                 k.get("gw_salienz"), k.get("gw_relevanz"), k.get("gw_neuheit"),
                 k.get("gw_wert"), int(bool(k.get("gw_zugelassen"))), int(aid in gew)))
            if aid in gew:
                store.db.execute(
                    "INSERT INTO gw_ausstrahlung(ts,turn_id,session_id,artikel_id,wert) "
                    "VALUES(?,?,?,?,?)", (jetzt, turn_id, session_id, aid, k.get("gw_wert")))
        store.db.commit()
    except Exception:
        pass


_IDF_CACHE: dict[str, float] = {}
_IDF_ZEITBUDGET_S = 0.35        # haerter Deckel; lieber gleiche Gewichte als ein zaeher Zug


def idf_gewichte(db, frage: str) -> dict[str, float]:
    """Seltenheit je Fragewort ueber den Artikelbestand (klassisches IDF).

    WARUM: ohne Gewichtung zaehlt "lauf" (steckt in 43 % aller gepruefen
    Korpuszeilen) genauso viel wie "testpflicht". Die Deckungszahl misst dann
    Allerweltssprache statt Passung.

    Ausfallsicher in jede Richtung: kein FTS, kein Budget, kein Ergebnis ->
    leeres dict, und `relevanz` zaehlt wieder ungewichtet. Ein Gewicht ist eine
    Verbesserung, nie eine Bedingung.
    """
    import time as _t
    worte = _worte(frage)
    if not worte:
        return {}
    raus: dict[str, float] = {}
    start = _t.perf_counter()
    gesamt = None
    for w in worte:
        if w in _IDF_CACHE:
            raus[w] = _IDF_CACHE[w]
            continue
        if _t.perf_counter() - start > _IDF_ZEITBUDGET_S:
            break
        try:
            if gesamt is None:
                gesamt = float(_verbindung(db).execute(
                    "SELECT COUNT(*) FROM fts_index_artikel").fetchone()[0]) or 1.0
            n = float(_verbindung(db).execute(
                "SELECT COUNT(*) FROM fts_index_artikel WHERE fts_index_artikel MATCH ?",
                (f'"{w}"*',)).fetchone()[0])
        except Exception:
            break
        import math as _m
        gew = _m.log((gesamt + 1.0) / (n + 1.0)) / _m.log(gesamt + 1.0)
        gew = max(0.05, min(1.0, gew))
        _IDF_CACHE[w] = gew
        raus[w] = gew
    return raus


def _verbindung(db):
    """Die sqlite-Verbindung, egal ob eine UnifiedDB oder eine rohe kommt.

    ⚠️ HIER LAG EIN STILLER AUSFALL, gefunden 2026-08-20 beim ersten
    Rueckkanal-Lauf: `UnifiedDB` hat KEIN `.execute`, nur `.db`. Die Lesefunktionen
    riefen `db.execute(...)`, bekamen einen AttributeError -- und ihr eigener
    Ausfallschutz machte daraus ein leeres Ergebnis. Kein Fehler, keine Meldung.
    Der Neuheits-Abschlag war damit seit dem Bau wirkungslos, und das Gelernte
    waere es geblieben. Genau die Sorte Defekt, die eine Anlage gebaut aussehen
    laesst, ohne dass irgendetwas rechnet.
    """
    return getattr(db, "db", db)


_LERN_TABELLE = (
    "CREATE TABLE IF NOT EXISTS gw_lernen("
    "  merkmal TEXT NOT NULL, artikel_id TEXT NOT NULL,"
    "  boost REAL NOT NULL DEFAULT 0, n INTEGER NOT NULL DEFAULT 0,"
    "  belohnt INTEGER NOT NULL DEFAULT 0, ts REAL NOT NULL,"
    "  PRIMARY KEY(merkmal, artikel_id));")


def gelernte_boosts(db, frage: str, idf: dict | None = None) -> dict:
    """Was bei den Woertern DIESER Frage bisher getragen hat.

    Liefert {(wort, artikel_id): boost}. Fehlt die Tabelle (frische Anlage,
    Sandkasten), ist die Antwort leer -- dann gibt es nichts zu erinnern, und
    `_gewichte` legt den Lernanteil auf relevanz um. Kein Bonus aus dem Nichts.
    """
    worte = [w for w in _worte(frage)
             if (idf or {}).get(w, 1.0) >= IDF_LERN_MIN]
    if not worte:
        return {}
    marken = ",".join("?" for _ in worte)
    try:
        rows = _verbindung(db).execute(
            f"SELECT merkmal, artikel_id, boost FROM gw_lernen "
            f"WHERE merkmal IN ({marken}) AND boost >= ?",
            worte + [LERN_MIN]).fetchall()
    except Exception:
        return {}
    raus = {}
    for r in rows:
        try:
            raus[(r["merkmal"], r["artikel_id"])] = float(r["boost"])
        except Exception:
            raus[(r[0], r[1])] = float(r[2])
    return raus


def lernen(store, frage: str, idf: dict | None, gewaehlt: list, antwort: str) -> dict:
    """Der Rueckkanal. Darf einen Zug NIE kippen.

    BELOHNUNG = Zero hat die Kennung in seiner Antwort GENANNT. Kein Modell
    wird nach seiner Zufriedenheit gefragt, kein Mensch muss klicken: die
    Quellenangabe ist der einzige Teil einer Antwort, den eine Verweigerung
    nicht faelschen kann. Wurde eine Stelle ausgestrahlt und nicht zitiert,
    hat sie fuer diese Art Frage nichts getragen -- das ist die Gegenprobe,
    und ohne sie waere jede Ausstrahlung eine Bestaetigung ihrer selbst.

    Geprueft wird gegen Zeros ROHE Antwort, nicht gegen die deutsche Fassung:
    der Uebersetzer koennte eine Kennung umformulieren oder weglassen, und dann
    haenge das Lernsignal an einer dritten Stufe.
    """
    ergebnis = {"belohnt": [], "leer": [], "worte": 0}
    try:
        worte = [w for w in _worte(frage) if (idf or {}).get(w, 1.0) >= IDF_LERN_MIN]
        ids = [str(a) for a in (gewaehlt or []) if str(a or "").strip()]
        if not worte or not ids:
            return ergebnis
        ergebnis["worte"] = len(worte)
        text = _flach(antwort or "")
        jetzt = time.time()
        store.db.executescript(_LERN_TABELLE)
        # Verfall auf ALLES -- auch auf das, was heute nicht drankam. Sonst
        # bliebe eine einmal gelernte Verbindung ewig stehen.
        store.db.execute("UPDATE gw_lernen SET boost = boost * ?", (VERFALL,))
        for aid in ids:
            belohnt = aid.lower() in text
            (ergebnis["belohnt"] if belohnt else ergebnis["leer"]).append(aid)
            for w in worte:
                row = store.db.execute(
                    "SELECT boost, n, belohnt FROM gw_lernen "
                    "WHERE merkmal=? AND artikel_id=?", (w, aid)).fetchone()
                try:
                    alt_b, alt_n, alt_bel = (float(row["boost"]), int(row["n"]),
                                             int(row["belohnt"])) if row else (0.0, 0, 0)
                except Exception:
                    alt_b, alt_n, alt_bel = (float(row[0]), int(row[1]), int(row[2])) if row else (0.0, 0, 0)
                if belohnt:
                    neu_b = alt_b + ALPHA_HOCH * (1.0 - alt_b)      # saettigt gegen 1
                else:
                    neu_b = alt_b - ALPHA_RUNTER * alt_b            # faellt gegen 0
                neu_b = max(0.0, min(1.0, neu_b))
                store.db.execute(
                    "INSERT INTO gw_lernen(merkmal,artikel_id,boost,n,belohnt,ts) "
                    "VALUES(?,?,?,?,?,?) ON CONFLICT(merkmal,artikel_id) DO UPDATE SET "
                    "boost=excluded.boost, n=excluded.n, belohnt=excluded.belohnt, ts=excluded.ts",
                    (w, aid, neu_b, alt_n + 1, alt_bel + int(belohnt), jetzt))
        store.db.execute("DELETE FROM gw_lernen WHERE boost < ?", (LERN_MIN,))
        store.db.commit()
    except Exception:
        pass
    return ergebnis


def haeufigkeiten(db, fenster: int = NEUHEIT_FENSTER) -> dict[str, int]:
    """Wie oft kam jede Stelle in den letzten `fenster` Ausstrahlungen vor.

    Fehlt die Tabelle (frische Anlage, Sandkasten), ist die Antwort leer --
    dann ist alles neu, und das ist auch richtig so.
    """
    try:
        rows = _verbindung(db).execute(
            "SELECT artikel_id FROM gw_ausstrahlung ORDER BY id DESC LIMIT ?",
            (int(fenster),)).fetchall()
    except Exception:
        return {}
    raus: dict[str, int] = {}
    for r in rows:
        a = str(r[0] if not isinstance(r, dict) else r.get("artikel_id") or "")
        if a:
            raus[a] = raus.get(a, 0) + 1
    return raus
