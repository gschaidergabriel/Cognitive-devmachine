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

DIE SCHWELLE IST HART UND ZWEITEILIG
------------------------------------
Zugelassen ist nur, wer BEIDE Huerden nimmt:
  * relevanz > 0 -- eine Stelle, die kein einziges Wort mit der Frage teilt,
    ist kein Beleg FUER diese Frage, egal wie hoch der Abruf sie rankt.
  * wert >= SCHWELLE.
Damit ist "nichts wird ausgestrahlt" ein erreichbarer Zustand. Genau das
fehlt LIDAs `compete()` (argmax, auch bei Score 0) -- und ohne diesen
Zustand gibt es keine Zuendung, nur eine Umverteilung.

WAS DIESES MODUL NICHT TUT
--------------------------
Es lernt nicht. Der Rueckkanal (Erfolg einer Ausstrahlung veraendert
kuenftige Gewichte) ist bewusst NICHT hier -- er wuerde waehrend einer
Messreihe aus den Versuchszuegen selbst ein Signal wachsen lassen. Was
geschrieben wird, ist eine Buchung (`gw_ausstrahlung`), keine Rueckkopplung.
"""
from __future__ import annotations

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
GEWICHT_RELEVANZ = 0.90
# Der Neuheits-Abschlag wirkt NUR, wenn es eine Ausstrahlungsgeschichte gibt.
# Ohne sie ist neuheit fuer jeden Kandidaten 1,0, also eine Konstante, also
# rangneutral -- gemessen in 100 % der Versuchszuege, weil die Apparaturen
# record_via_turnlifecycle=False setzen. Statt eine wirkungslose Konstante
# mitzuschleppen, wird das Gewicht dann auf relevanz umgelegt (siehe
# _gewichte()) -- die Formel sagt damit die Wahrheit ueber das, was rechnet.
GEWICHT_NEUHEIT = 0.10
# ⭐ NICHT GERATEN, SONDERN ABGELESEN. Schwellensweep 0,10..0,40 in Schritten
# von 0,02 ueber drei Fragesorten (A: Beleg im Korpus, B: fachfremd,
# C: blosse Hoeflichkeit). Bis 0,28 kommt in A der Traeger 8/8 durch und kein
# Zug faellt auf null; ab 0,30 faellt der erste Traeger raus (7/8), ab 0,34
# nur noch 5/8. B faellt bereits ab 0,22 auf 0,33 angebotene Stellen (2/3 der
# Fragen strahlen nichts aus). Die Mitte des Plateaus ist 0,25 -- dort ist der
# Abstand zwischen "Beleg da" und "fachfremd" am groessten, ohne dass die
# Trennung an der zweiten Nachkommastelle haengt.
SCHWELLE = 0.25
# Eine EINZELNE gedeckte Wortuebereinstimmung ist keine Passung. Ohne diese
# Regel strahlte "danke, das war hilfreich" eine Stelle aus (ein gedecktes Wort
# von zweien = relevanz 0,5) -- eine Zuendung ohne Sachfrage, also genau das
# falsch-positive Feuern, das die Schwelle verhindern soll.
MIN_GEDECKT = 2
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


def _worte(text: str) -> list[str]:
    """Inhaltswoerter einer Frage, klein, ohne Allerweltswoerter.

    Bindestrich-Zusammensetzungen zaehlen DOPPELT: das ganze Wort und seine
    Glieder. "leihmich-slug" faende sonst die Stelle nicht, die von
    "LEIHMICH_SLUGS" handelt -- gemessen genau dieser Fall.
    """
    raus, gesehen = [], set()
    for w in _WORT.findall((text or "").lower()):
        for teil in [w] + [t for t in re.split(r"[-_]", w) if len(t) >= 3]:
            if teil not in _STOPP and teil not in gesehen:
                gesehen.add(teil)
                raus.append(teil)
    return raus


_KURZ = 4          # darunter zaehlt nur exakte Wortgleichheit


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
    if len(wort) < _KURZ:
        return re.search(r"\b" + re.escape(wort) + r"\b", heu) is not None
    return re.search(r"(?:\b|[a-z0-9]*[_-])" + re.escape(wort), heu) is not None


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
    heu = " ".join(str(treffer.get(f) or "") for f in ("titel", "ausschnitt", "art", "sphaere")).lower()
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


def _gewichte(haeufigkeiten: dict | None) -> tuple[float, float]:
    """(relevanz, neuheit) -- ohne Ausstrahlungsgeschichte traegt relevanz alles.

    Eine Konstante im Summanden ist keine Bewertung. Wenn `haeufigkeiten` leer
    ist, hat JEDER Kandidat neuheit=1,0; das Gewicht wuerde dann nur den
    Absolutwert anheben und die Schwelle heimlich absenken (aus 0,32 wuerde
    faktisch 0,22). Also wird es umgelegt statt mitgeschleppt.
    """
    if haeufigkeiten:
        return GEWICHT_RELEVANZ, GEWICHT_NEUHEIT
    return GEWICHT_RELEVANZ + GEWICHT_NEUHEIT, 0.0


def bewerten(korpus: list, frage: str, haeufigkeiten: dict | None = None,
             idf: dict | None = None) -> list[dict[str, Any]]:
    """Alle Korpustreffer mit Zahl versehen, absteigend sortiert.

    Liefert NEUE dicts -- der uebergebene Korpus bleibt unangetastet, damit
    andere Verbraucher derselben world-Referenz nichts Veraendertes sehen.
    """
    fw = _worte(frage)
    g_rel, g_neu = _gewichte(haeufigkeiten)
    raus: list[dict[str, Any]] = []
    echte = [t for t in (korpus or []) if isinstance(t, dict)]
    for i, t in enumerate(echte):
        sal = 1.0 / (1.0 + i)
        rel = relevanz(t, fw, idf)
        neu = neuheit(t.get("artikel_id"), haeufigkeiten or {})
        wert = GEWICHT_SALIENZ * sal + g_rel * rel + g_neu * neu
        k = dict(t)
        k["gw_salienz"] = round(sal, 3)
        k["gw_relevanz"] = round(rel, 3)
        k["gw_neuheit"] = round(neu, 3)
        k["gw_wert"] = round(wert, 3)
        k["gw_zugelassen"] = bool(rel > 0.0 and wert >= SCHWELLE)
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
    return raus


# Felder, die eine Kandidatenzeile im PRAEBEWUSSTEN VORRAT tragen darf.
# Alles andere -- vor allem `ausschnitt` -- ist INHALT und gehoert erst in den
# Arbeitsraum, nachdem gewaehlt wurde.
_KENNUNGSFELDER = ("artikel_id", "titel", "art", "sphaere", "quelle", "treffer_art",
                   "gw_rang", "gw_wert", "gw_relevanz", "gw_salienz", "gw_neuheit",
                   "gw_zugelassen")


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
                gesamt = float(db.execute(
                    "SELECT COUNT(*) FROM fts_index_artikel").fetchone()[0]) or 1.0
            n = float(db.execute(
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


def haeufigkeiten(db, fenster: int = NEUHEIT_FENSTER) -> dict[str, int]:
    """Wie oft kam jede Stelle in den letzten `fenster` Ausstrahlungen vor.

    Fehlt die Tabelle (frische Anlage, Sandkasten), ist die Antwort leer --
    dann ist alles neu, und das ist auch richtig so.
    """
    try:
        rows = db.execute(
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
