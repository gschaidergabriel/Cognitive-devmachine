#!/usr/bin/env python3
"""OmniMind-Anreicherung -- ein fortlaufender, sparsamer Takt am Wiki-Korpus.

Im Stil der clayverse-*-Werkzeuge (wikiarbeit.py, verdichtung.py): mechanisch
zuerst, Modellaufruf nur wo Mechanik nicht reicht, IMMER ein Vorschlag in
einer eigenen Tabelle -- nie ein Ueberschreiben von `artikel`. Jeder Schritt
bucht sich selbst ab (om_lauf) und bricht NIE den ganzen Lauf ab, wenn ein
einzelner Anbieter gerade nicht mitspielt.

⚠️ NUR FREIE, GESUNDE ZUGAENGE:
  - Mistral: MISTRAL2_API_KEY / MISTRAL3_API_KEY -- NIE MISTRAL_API_KEY
    (Schluessel 1 hat kein Abo, HTTP 402, gemessen).
  - Gemini: GEMINI_API_KEY, GEMINI2_API_KEY als Rueckfall.
  - Groq: GROQ3_API_KEY ueber werkzeug/wikiarbeit.rufen() -- derselbe
    HTTP-Weg, den die dauerhafte Wikiarbeit benutzt. Diese Anreicherung ist
    ein SEHR kleiner Nebenverbraucher (siehe GROQ_DECKEL_JE_LAUF unten,
    einstellig gegen deren 14.400/Tag) und faehrt NICHT ueber deren eigenes
    Kontingentbuch (kontingent.py, Konto "clayverse") -- ein zweiter,
    unabhaengig gedeckelter Verbraucher auf demselben Schluessel ist hier
    einfacher zu pruefen als ein geteiltes Buch zweier Dienste.

⚠️ NO_INVENTION: jede Implikation/Zusammenfassung/Skizze traegt IMMER, wie
sie entstand (mechanisch:<feld> oder modell:<name>) -- niemals ununterscheidbar
von gemessenem Bestand. Die Projekt-Hierarchie stuetzt sich auf echte Felder
(artikel.projekt) und echtes Ko-Vorkommen (Titel/Tags, vp_weg) -- eine
Vermutung ohne Beleg wird NICHT geschrieben, ein Modellurteil bekommt nie
mehr als 0.6 Konfidenz, weil es selbst eine Ableitung ist, kein Messwert.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

# Python setzt sys.path[0] beim Skriptaufruf automatisch auf den EIGENEN
# Ordner (clayverse/) -- nicht auf dessen Elternordner, wo das Paket
# `clayverse` als Ganzes liegt. Deshalb hier immer explizit der Elternordner,
# nicht bloss "falls noch nicht drin" (der eigene Ordner IST schon drin und
# haette die Bedingung sonst still verhindert).
_ELTERNORDNER = str(Path(__file__).resolve().parent.parent)
if _ELTERNORDNER not in sys.path:
    sys.path.insert(0, _ELTERNORDNER)

from clayverse import omnimind as om  # noqa: E402
from clayverse.mistral_prestage.transport import (  # noqa: E402
    TransportError, gemini_chat_json, mistral_chat_json_rotating,
)

# ⚠️ BEWUSST KEIN `clayverse.mistral_prestage.secrets` (braucht python-dotenv,
# das im Container-Image steckt, aber NICHT im nackten Host-Python -- und
# dieser Dienst laeuft wie paketarbeiter.py/wikiarbeit.py AUF DEM WIRT, per
# `python3 -c "..."` ohne venv). Derselbe handgeschriebene .env-Leser wie
# wikiarbeit.umgebung(): reine stdlib, ein try/except, nie ein Schluessel
# in argv oder einer Fehlermeldung.
FREIE_ZUGAENGE_PFAD = "/etc/clayverse/freie-zugaenge.env"


def load_free_api_keys(pfad: str = FREIE_ZUGAENGE_PFAD) -> dict[str, str]:
    werte: dict[str, str] = {}
    try:
        with open(pfad, encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if zeile and not zeile.startswith("#") and "=" in zeile:
                    k, v = zeile.split("=", 1)
                    if v.strip():
                        werte[k.strip()] = v.strip()
    except OSError:
        pass
    return werte

# ── Deckel je Lauf -- klein, weil der Timer oft genug wiederkommt ────────
IMPLIKATIONEN_JE_LAUF = 6
ZUSAMMENFASSUNGEN_JE_LAUF = 6
LLM_PROJEKT_PRUEFUNGEN_JE_LAUF = 4
GROQ_DECKEL_JE_LAUF = 4          # gegen die 14.400/Tag der Dauerarbeit ein Rundungsfehler
MISTRAL_MODELL = "mistral-small-latest"     # gleiches Modell wie die Vorstufe (geprueft, schnell)
GEMINI_MODELL = "gemini-3.5-flash-lite"     # gleiches Modell wie judge.py (freies Tageskontingent gemessen)


def _jetzt_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def _protokoll(db, schritt: str, ok: bool, anzahl: int, ms: float, hinweis: str = "") -> None:
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO om_lauf(zeit,schritt,ok,anzahl,ms,hinweis) VALUES(?,?,?,?,?,?)",
            (_jetzt_iso(), schritt, 1 if ok else 0, anzahl, int(ms), hinweis[:500] if hinweis else None))


# ── 1) Projekt-Cluster -- Feld zuerst, Ko-Vorkommen danach, Modell nur am Rand

# Deutsche Fuellwoerter/generische Systembegriffe, die als "Projektname" nur
# Rauschen waeren, obwohl sie das Titelmuster erfuellen (Grossbuchstabe am
# Wortanfang, wiederkehrend). Mechanisch ausgeschlossen, nicht erraten.
_KANDIDAT_SPERRLISTE = {
    "die", "der", "das", "wie", "was", "fuer", "und", "eine", "einen", "artikel",
    "bericht", "notiz", "update", "readme", "architecture", "manual", "license",
    "dockerfile", "quittung", "baunotiz", "hypothese", "gegenhypothese",
}
#
# ⚠️ GEMESSEN 2026-08-21, ERSTER LAUF: ein einzelnes grossgeschriebenes Wort
# ab 5 Zeichen (die urspruengliche zweite Alternative) traf auf einem
# 18.456-Artikel-Fachkorpus vor allem Fachvokabular ("Secondary", "Receipt",
# "Entity", "Semantic", "Fusion", "Search", ...) -- 858 "Kandidaten", davon
# praktisch keiner ein echter Projektname. NUR CamelCase (mind. zwei innere
# Grossbuchstaben, wie SeiMensch, HerzRad, ClayVerse) ist trennscharf genug:
# Fachvokabular in diesem Korpus wird nicht CamelCase geschrieben, gepraegte
# Produkt-/Systemnamen schon. Reduziert auf eine handhabbare, echte Menge.
_KANDIDAT_MUSTER = re.compile(r"\b([A-ZÄÖÜ][a-zäöüß]+(?:[A-Z][a-zäöüß]+)+)\b")


def _kandidaten_aus_titeln(db, mindest_vorkommen: int = 4) -> dict[str, int]:
    zaehler: dict[str, int] = {}
    for r in db.db.execute("SELECT titel FROM artikel WHERE titel IS NOT NULL"):
        titel = r["titel"] or ""
        for treffer in set(_KANDIDAT_MUSTER.findall(titel)):
            if treffer.lower() in _KANDIDAT_SPERRLISTE:
                continue
            zaehler[treffer] = zaehler.get(treffer, 0) + 1
    return {k: v for k, v in zaehler.items() if v >= mindest_vorkommen}


def _artikel_ids_fuer_namen(db, name: str) -> set[str]:
    muster = f"%{name}%"
    zeilen = db.db.execute(
        "SELECT id FROM artikel WHERE titel LIKE ? OR tags LIKE ?", (muster, muster)).fetchall()
    return {r["id"] for r in zeilen}


def _llm_projekt_pruefung(x_name, y_name, x_beispiele, y_beispiele, schnitt, y_gesamt) -> dict | None:
    """Fragt EIN freies Modell nach einer unsicheren Ober-/Unterprojekt-Vermutung.

    Bekommt NUR echte Belege (Beispieltitel, Zahlen) -- keine Anweisung, sich
    etwas auszudenken. Rueckgabe None heisst: kein Zugang verfuegbar oder
    Anfrage gescheitert -- der Aufrufer verwirft die Vermutung dann einfach,
    statt geraten zu antworten.
    """
    zugaenge = load_free_api_keys()
    system = ("Du pruefst NUR anhand der gegebenen Belege, ob zwei Projektnamen aus einer "
              "Wissensbasis zusammengehoeren und welcher der umfassendere ist. Erfinde NICHTS "
              "ausserhalb der Belege. Antworte ausschliesslich als JSON.")
    user = json.dumps({
        "frage": f"Ist '{y_name}' Teil von / untergeordnet zu '{x_name}', oder umgekehrt, oder "
                 f"unabhaengig?",
        "beleg_ko_vorkommen": f"{schnitt} von {y_gesamt} Artikeln zu '{y_name}' erwaehnen auch "
                               f"'{x_name}' in Titel oder Tags.",
        "beispieltitel_x": x_beispiele[:5], "beispieltitel_y": y_beispiele[:5],
        "antwortformat": {"zusammenhang": "true|false",
                           "ueber_unter": "x_ueber_y|y_ueber_x|gleichrangig|unklar",
                           "begruendung": "ein Satz, nur aus den Belegen"},
    }, ensure_ascii=False)

    keys = [zugaenge.get("MISTRAL2_API_KEY"), zugaenge.get("MISTRAL3_API_KEY")]
    keys = [k for k in keys if k]
    if keys:
        try:
            ergebnis = mistral_chat_json_rotating(
                keys=keys, model=MISTRAL_MODELL, system=system, user=user, max_tokens=300)
            return {"payload": ergebnis["payload"], "modell": f"mistral:{MISTRAL_MODELL}"}
        except TransportError:
            pass
    gemini_key = zugaenge.get("GEMINI_API_KEY") or zugaenge.get("GEMINI2_API_KEY")
    if gemini_key:
        try:
            ergebnis = gemini_chat_json(
                api_key=gemini_key, model=GEMINI_MODELL, system=system, user=user, max_tokens=300)
            return {"payload": ergebnis["payload"], "modell": f"gemini:{GEMINI_MODELL}"}
        except TransportError:
            pass
    return None


def projekt_cluster(db) -> dict:
    t0 = time.time()
    om.sicherstellen(db)
    jetzt = _jetzt_iso()

    # ── Feld-Cluster: die harte Wahrheit aus artikel.projekt ────────────
    feld_zeilen = db.db.execute(
        "SELECT projekt, COUNT(*) n FROM artikel WHERE projekt IS NOT NULL AND projekt<>'' "
        "GROUP BY projekt").fetchall()
    feld_ids: dict[str, set[str]] = {}
    for r in feld_zeilen:
        feld_ids[r["projekt"]] = {x["id"] for x in db.db.execute(
            "SELECT id FROM artikel WHERE projekt=?", (r["projekt"],)).fetchall()}

    # ── Titel-Kandidaten: wiederkehrende Eigennamen, die KEIN Feld sind ──
    kandidaten = _kandidaten_aus_titeln(db)
    kandidat_ids: dict[str, set[str]] = {}
    for name in list(kandidaten):
        if name in feld_ids:
            continue  # deckt sich mit einem Feldwert -- kein zweiter Knoten dafuer
        ids = _artikel_ids_fuer_namen(db, name)
        if len(ids) >= 2:
            kandidat_ids[name] = ids

    alle_namen = {**{f"feld:{k}": v for k, v in feld_ids.items()},
                  **{f"titel:{k}": v for k, v in kandidat_ids.items()}}

    # ── Ko-Vorkommen zwischen ALLEN Paaren -- der Kandidatenpool ist klein
    # (Feldwerte + wiederkehrende Titelnamen, typischerweise < 150), also ist
    # der volle O(n^2)-Vergleich kein Problem.
    namen_liste = list(alle_namen.items())
    kanten_eltern: list[tuple[str, str, float, str]] = []   # (kind, eltern, konfidenz, beleg)
    kanten_geschwister: list[tuple[str, str, float, str]] = []
    unsicher: list[tuple[str, str, float, int, int]] = []   # fuer die LLM-Nachpruefung

    for i, (xid, xset) in enumerate(namen_liste):
        for yid, yset in namen_liste[i + 1:]:
            if not xset or not yset:
                continue
            schnitt = len(xset & yset)
            if schnitt == 0:
                continue
            c_x_ueber_y = schnitt / len(yset)   # Anteil von Y, der auch X traegt
            c_y_ueber_x = schnitt / len(xset)
            grosse, kleine = (xid, yid) if len(xset) >= len(yset) else (yid, xid)
            c_gross = c_x_ueber_y if grosse == xid else c_y_ueber_x
            c_klein = c_y_ueber_x if grosse == xid else c_x_ueber_y
            beleg = (f"Ko-Vorkommen: {schnitt} von {min(len(xset), len(yset))} Artikeln zu "
                     f"'{kleine.split(':',1)[1]}' erwaehnen auch '{grosse.split(':',1)[1]}' "
                     f"(Titel/Tags), Schwelle 0.5")
            if c_gross >= 0.5 and len(alle_namen[grosse]) > len(alle_namen[kleine]):
                konfidenz = round(min(0.95, c_gross * 0.9), 3)
                kanten_eltern.append((kleine, grosse, konfidenz, beleg))
            elif c_gross >= 0.5 and c_klein >= 0.5:
                konfidenz = round(min(0.9, (c_gross + c_klein) / 2 * 0.9), 3)
                kanten_geschwister.append((xid, yid, konfidenz, beleg))
            elif 0.2 <= c_gross < 0.5:
                unsicher.append((grosse, kleine, c_gross, schnitt, len(alle_namen[kleine])))

    # Modellgestuetzte Nachpruefung, nur fuer die unsichersten Paare, gedeckelt.
    unsicher.sort(key=lambda z: -z[2])
    llm_bestaetigt = 0
    for grosse, kleine, c_gross, schnitt, y_gesamt in unsicher[:LLM_PROJEKT_PRUEFUNGEN_JE_LAUF]:
        x_name, y_name = grosse.split(":", 1)[1], kleine.split(":", 1)[1]
        x_beisp = [db.db.execute("SELECT titel FROM artikel WHERE id=?", (i,)).fetchone()["titel"]
                   for i in list(alle_namen[grosse])[:5]]
        y_beisp = [db.db.execute("SELECT titel FROM artikel WHERE id=?", (i,)).fetchone()["titel"]
                   for i in list(alle_namen[kleine])[:5]]
        antwort = _llm_projekt_pruefung(x_name, y_name, x_beisp, y_beisp, schnitt, y_gesamt)
        if not antwort:
            continue
        payload = antwort["payload"] if isinstance(antwort["payload"], dict) else {}
        if payload.get("zusammenhang") in (True, "true", "True"):
            richtung = payload.get("ueber_unter")
            begr = (f"modellgestuetzt ({antwort['modell']}): {payload.get('begruendung', '')} "
                    f"-- Beleg: Ko-Vorkommen {schnitt}/{y_gesamt}")
            konfidenz = 0.55  # gedeckelt: ein Modellurteil ist eine Ableitung, kein Messwert
            if richtung == "x_ueber_y":
                kanten_eltern.append((kleine, grosse, konfidenz, begr))
            elif richtung == "y_ueber_x":
                kanten_eltern.append((grosse, kleine, konfidenz, begr))
            else:
                kanten_geschwister.append((grosse, kleine, konfidenz, begr))
            llm_bestaetigt += 1

    # ── Schreiben ─────────────────────────────────────────────────────
    eltern_von: dict[str, tuple[str, float, str]] = {}
    for kind, eltern, konfidenz, beleg in kanten_eltern:
        bisher = eltern_von.get(kind)
        if bisher is None or konfidenz > bisher[1]:
            eltern_von[kind] = (eltern, konfidenz, beleg)

    with db.tx() as sql:
        for pid, ids in alle_namen.items():
            art, name = pid.split(":", 1)
            eltern_id, konfidenz, begruendung = None, (1.0 if art == "feld" else 0.5), (
                "aus Feld artikel.projekt" if art == "feld"
                else f"wiederkehrende Erwaehnung im Titel/Tags (n={len(ids)})")
            if pid in eltern_von:
                eltern_id, konfidenz, begruendung = eltern_von[pid]
            sql.execute(
                "INSERT INTO om_projekt(id,name,art,eltern_id,konfidenz,begruendung,"
                "anzahl_artikel,aktualisiert_am) VALUES(?,?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET eltern_id=excluded.eltern_id, "
                "konfidenz=excluded.konfidenz, begruendung=excluded.begruendung, "
                "anzahl_artikel=excluded.anzahl_artikel, aktualisiert_am=excluded.aktualisiert_am",
                (pid, name, ("feld" if art == "feld" else "cluster"), eltern_id, konfidenz,
                 begruendung, len(ids), jetzt))
            for aid in ids:
                sql.execute(
                    "INSERT INTO om_projekt_mitglied(artikel_id,projekt_id,konfidenz) VALUES(?,?,?) "
                    "ON CONFLICT(artikel_id,projekt_id) DO UPDATE SET konfidenz=excluded.konfidenz",
                    (aid, pid, konfidenz))
        for a_id, b_id, staerke, beleg in kanten_geschwister:
            lo, hi = sorted((a_id, b_id))
            sql.execute(
                "INSERT INTO om_projekt_kante(a_id,b_id,staerke,beleg,aktualisiert_am) "
                "VALUES(?,?,?,?,?) ON CONFLICT(a_id,b_id) DO UPDATE SET staerke=excluded.staerke,"
                " beleg=excluded.beleg, aktualisiert_am=excluded.aktualisiert_am",
                (lo, hi, staerke, beleg, jetzt))

    ergebnis = {
        "feld_cluster": len(feld_ids), "titel_cluster": len(kandidat_ids),
        "eltern_kanten": len(eltern_von), "geschwister_kanten": len(kanten_geschwister),
        "unsichere_paare": len(unsicher), "llm_geprueft": min(len(unsicher), LLM_PROJEKT_PRUEFUNGEN_JE_LAUF),
        "llm_bestaetigt": llm_bestaetigt,
    }
    _protokoll(db, "projekt_cluster", True, len(alle_namen), (time.time() - t0) * 1000, json.dumps(ergebnis, ensure_ascii=False))
    return ergebnis


# ── 2) Implikationen aus echten Hypothesen ableiten (Mistral) ───────────

def _hypothesen_ohne_implikation(db, limit: int):
    zeilen = db.db.execute(
        "SELECT a.id, a.art, a.metadaten FROM artikel a "
        "WHERE a.art IN ('hypothese','gegenhypothese') "
        "AND a.id NOT IN (SELECT DISTINCT artikel_id FROM om_hypothese_implikation) "
        "LIMIT ?", (limit * 3,)).fetchall()
    aus = []
    for r in zeilen:
        try:
            md = json.loads(r["metadaten"] or "{}")
        except Exception:
            md = {}
        prop = md.get("proposition") if isinstance(md, dict) else None
        if prop:
            aus.append({"id": r["id"], "claim_id": md.get("claim_id"), "proposition": prop,
                        "status": md.get("first_status"), "domains": md.get("domains") or []})
        if len(aus) >= limit:
            break
    return aus


def implikationen_ableiten(db) -> dict:
    t0 = time.time()
    om.sicherstellen(db)
    kandidaten = _hypothesen_ohne_implikation(db, IMPLIKATIONEN_JE_LAUF)
    if not kandidaten:
        _protokoll(db, "implikationen", True, 0, (time.time() - t0) * 1000, "nichts Offenes")
        return {"bearbeitet": 0, "erzeugt": 0, "hinweis": "keine Hypothese ohne Implikation offen"}

    zugaenge = load_free_api_keys()
    keys = [zugaenge.get("MISTRAL2_API_KEY"), zugaenge.get("MISTRAL3_API_KEY")]
    keys = [k for k in keys if k]
    if not keys:
        _protokoll(db, "implikationen", False, 0, (time.time() - t0) * 1000, "kein Mistral2/3-Schluessel")
        return {"bearbeitet": 0, "erzeugt": 0, "hinweis": "kein freier Mistral2/3-Zugang verfuegbar"}

    system = ("Du leitest aus EINER gegebenen Forschungshypothese die logisch daraus folgenden "
              "Implikationen ab -- nur was zwingend oder plausibel aus dieser Aussage folgt, "
              "nichts Neues dazuerfinden. 1-3 Implikationen, jede mit eigener Konfidenz 0..1 "
              "(wie sicher die Ableitung ist, NICHT wie sicher die Hypothese selbst ist). "
              "Antworte ausschliesslich als JSON.")
    erzeugt = 0
    for k in kandidaten:
        user = json.dumps({
            "hypothese": k["proposition"], "status": k["status"], "domains": k["domains"],
            "antwortformat": {"implikationen": [{"text": "...", "konfidenz": 0.0}]},
        }, ensure_ascii=False)
        try:
            ergebnis = mistral_chat_json_rotating(
                keys=keys, model=MISTRAL_MODELL, system=system, user=user, max_tokens=500)
        except TransportError as e:
            _protokoll(db, "implikationen", False, erzeugt, (time.time() - t0) * 1000, f"{type(e).__name__}: {e}")
            continue
        payload = ergebnis["payload"] if isinstance(ergebnis["payload"], dict) else {}
        eintraege = payload.get("implikationen")
        if not isinstance(eintraege, list):
            continue
        jetzt = _jetzt_iso()
        with db.tx() as sql:
            for e in eintraege[:3]:
                if not isinstance(e, dict) or not e.get("text"):
                    continue
                try:
                    konf = max(0.0, min(1.0, float(e.get("konfidenz", 0.4))))
                except (TypeError, ValueError):
                    konf = 0.4
                sql.execute(
                    "INSERT INTO om_hypothese_implikation(artikel_id,hypothese_id,hypothese_text,"
                    "text,konfidenz,modell,erzeugt_am) VALUES(?,?,?,?,?,?,?)",
                    (k["id"], k["claim_id"], k["proposition"], str(e["text"])[:2000], konf,
                     f"mistral:{MISTRAL_MODELL}", jetzt))
                erzeugt += 1

    _protokoll(db, "implikationen", True, erzeugt, (time.time() - t0) * 1000,
               f"{len(kandidaten)} Hypothesen bearbeitet")
    return {"bearbeitet": len(kandidaten), "erzeugt": erzeugt}


# ── 3) Zusammenfassungen fuer lange Artikel (Gemini) ─────────────────────

def zusammenfassungen_erzeugen(db) -> dict:
    t0 = time.time()
    om.sicherstellen(db)
    zeilen = db.db.execute(
        "SELECT s.artikel_id, s.titel, s.text FROM artikel_suchtext s "
        "WHERE length(s.text) > 600 "
        "AND s.artikel_id NOT IN (SELECT artikel_id FROM om_zusammenfassung) "
        "ORDER BY length(s.text) DESC LIMIT ?", (ZUSAMMENFASSUNGEN_JE_LAUF,)).fetchall()
    if not zeilen:
        _protokoll(db, "zusammenfassungen", True, 0, (time.time() - t0) * 1000, "nichts Offenes")
        return {"bearbeitet": 0, "erzeugt": 0}

    zugaenge = load_free_api_keys()
    key = zugaenge.get("GEMINI_API_KEY") or zugaenge.get("GEMINI2_API_KEY")
    if not key:
        _protokoll(db, "zusammenfassungen", False, 0, (time.time() - t0) * 1000, "kein Gemini-Schluessel")
        return {"bearbeitet": 0, "erzeugt": 0, "hinweis": "kein freier Gemini-Zugang verfuegbar"}

    system = ("Fasse den gegebenen Text in 2-4 Saetzen zusammen. NUR was im Text steht -- "
              "keine Ergaenzung, keine Bewertung, keine Vermutung ueber das, was fehlt. "
              "Deutsch. Antworte ausschliesslich als JSON.")
    erzeugt = 0
    for r in zeilen:
        user = json.dumps({"titel": r["titel"], "text": (r["text"] or "")[:8000],
                           "antwortformat": {"zusammenfassung": "..."}}, ensure_ascii=False)
        try:
            ergebnis = gemini_chat_json(api_key=key, model=GEMINI_MODELL, system=system,
                                        user=user, max_tokens=400)
        except TransportError as e:
            _protokoll(db, "zusammenfassungen", False, erzeugt, (time.time() - t0) * 1000,
                       f"{type(e).__name__}: {e}")
            continue
        payload = ergebnis["payload"] if isinstance(ergebnis["payload"], dict) else {}
        text = payload.get("zusammenfassung")
        if not text:
            continue
        with db.tx() as sql:
            sql.execute(
                "INSERT INTO om_zusammenfassung(artikel_id,text,modell,erzeugt_am) VALUES(?,?,?,?) "
                "ON CONFLICT(artikel_id) DO UPDATE SET text=excluded.text, modell=excluded.modell,"
                " erzeugt_am=excluded.erzeugt_am",
                (r["artikel_id"], str(text)[:2000], f"gemini:{GEMINI_MODELL}", _jetzt_iso()))
        erzeugt += 1

    _protokoll(db, "zusammenfassungen", True, erzeugt, (time.time() - t0) * 1000,
               f"{len(zeilen)} Artikel bearbeitet")
    return {"bearbeitet": len(zeilen), "erzeugt": erzeugt}


# ── 4) Skizzen -- rein mechanisch aus strukturierten Feldern (kein Modell) ─
#
# ⭐ Fuer Hypothese/Gegenhypothese-Artikel liegen claim_id/status/domains
# bereits strukturiert in metadaten -- ein Mermaid-Graph daraus ist keine
# Erfindung, sondern eine andere Schreibweise derselben Felder. Kein
# Modellaufruf noetig, kein Budget verbraucht, und NICHTS kann hier
# "dazuerfinden", weil kein Freitext generiert wird.

def _mermaid_fuer_hypothese(row_id: str, art: str, md: dict) -> str:
    status = (md.get("first_status") or "?").replace('"', "'")
    domains = ", ".join(md.get("domains") or []) or "-"
    knoten_art = "Hypothese" if art == "hypothese" else "Gegenhypothese"
    return (
        "flowchart TD\n"
        f'  H["{knoten_art}\\n{row_id}"] --> S["Status: {status}"]\n'
        f'  H --> D["Domains: {domains}"]\n'
    )


def skizzen_erzeugen(db, limit: int = 40) -> dict:
    t0 = time.time()
    om.sicherstellen(db)
    zeilen = db.db.execute(
        "SELECT id, art, metadaten FROM artikel WHERE art IN ('hypothese','gegenhypothese') "
        "AND id NOT IN (SELECT artikel_id FROM om_skizze) LIMIT ?", (limit,)).fetchall()
    erzeugt = 0
    jetzt = _jetzt_iso()
    with db.tx() as sql:
        for r in zeilen:
            try:
                md = json.loads(r["metadaten"] or "{}")
            except Exception:
                md = {}
            if not isinstance(md, dict) or not md.get("proposition"):
                continue
            mermaid = _mermaid_fuer_hypothese(r["id"], r["art"], md)
            sql.execute(
                "INSERT INTO om_skizze(artikel_id,mermaid,quelle,erzeugt_am) VALUES(?,?,?,?) "
                "ON CONFLICT(artikel_id) DO UPDATE SET mermaid=excluded.mermaid, "
                "quelle=excluded.quelle, erzeugt_am=excluded.erzeugt_am",
                (r["id"], mermaid, "mechanisch:metadaten(claim_id,status,domains)", jetzt))
            erzeugt += 1
    _protokoll(db, "skizzen", True, erzeugt, (time.time() - t0) * 1000, f"{len(zeilen)} Kandidaten")
    return {"bearbeitet": len(zeilen), "erzeugt": erzeugt}


# ── Der ganze Lauf ────────────────────────────────────────────────────


# ── Kanonische Hierarchie: vom Eigner definiert, keine Vermutung ─────────
#
# Gabriel (21.08.): die rein autonome Clusterung findet manche Zugehoerigkeit
# NICHT (gemessen: Project-Frankenstein 0 Kanten zu SeiMensch; iar.frank.ink
# liegt als eigene sphaere, nicht als Unterknoten). Deshalb hier eine ZWEITE,
# eigenstaendige Wahrheitsquelle: eine vom Eigner erklaerte Karte -- das ist
# KEIN Verstoss gegen NO_INVENTION, weil der Eigner die Zugehoerigkeit
# DEFINIERT, nicht raet. Autonome Funde ergaenzen das (art='feld'/'cluster',
# eigene Konfidenz<1.0); diese Karte traegt IMMER Konfidenz 1.0 und
# begruendung "vom Eigner definiert".
#
# SeiMensch ist das Dach ueber ZWEI Zweigen (Gabriel, 21.08., zweite Praezisierung):
#   1. die gemeinnuetzige Webseite (Herzrad, LeihMich, iar.frank.ink, ...)
#   2. der KI-/Forschungs-/Infrastrukturzweig (EntityOS, ClayVerse, Frank, ...)
#
# Erweiterbar: neue Zeilen unten anhaengen, `alias_projekt`/`alias_cluster`
# reparentieren VORHANDENE autonome Knoten (ihre eigene Konfidenz/Herkunft
# bleibt an der Stelle stehen -- nur die Elternbeziehung wird eigner-autoritativ),
# `muster`/`kontext_muster` suchen zusaetzlich MECHANISCH nach echten Artikeln,
# die noch unter keinem Feld/Cluster erfasst sind.
KANON_BAUM = {
    "kanon:seimensch": {
        "name": "SeiMensch", "eltern": None, "muster": ["seimensch", "seimensch.net"],
    },
    "kanon:seimensch-web": {
        "name": "Gemeinnützig / Web", "eltern": "kanon:seimensch", "muster": [],
    },
    "kanon:herzrad": {
        "name": "Herzrad", "eltern": "kanon:seimensch-web",
        "muster": ["herzrad", "herzrad.at"], "alias_cluster": [],
    },
    "kanon:leihmich": {
        "name": "LeihMich", "eltern": "kanon:seimensch-web",
        "muster": ["leihmich", "leihmich.org"],
    },
    "kanon:iar-frank-ink": {
        "name": "iar.frank.ink (Institute for Agentic Research)", "eltern": "kanon:seimensch-web",
        "muster": ["iar.frank.ink"], "alias_projekt": ["iar"],
    },
    "kanon:seimensch-projekte": {
        "name": "SeiMensch-Projekte", "eltern": "kanon:seimensch-web",
        "muster": ["/projekte/"], "kontext_muster": ["seimensch"],
    },
    "kanon:harte-baesse": {
        "name": "Harte Bässe", "eltern": "kanon:seimensch-web",
        "muster": ["harte-baesse", "harte bässe", "harte baesse"],
    },
    "kanon:workshop": {
        "name": "Workshop", "eltern": "kanon:seimensch-web",
        "muster": ["/workshop/", "resilienz-training"], "kontext_muster": ["seimensch"],
    },
    "kanon:unterstuetzer": {
        "name": "Unterstützer", "eltern": "kanon:seimensch-web",
        "muster": ["/unterstuetzer/"], "kontext_muster": ["seimensch"],
    },
    "kanon:seimensch-ki": {
        "name": "KI / Forschung", "eltern": "kanon:seimensch", "muster": [],
    },
    "kanon:entityos": {
        "name": "EntityOS", "eltern": "kanon:seimensch-ki", "alias_projekt": ["EntityOS"],
    },
    "kanon:clayverse": {
        "name": "ClayVerse", "eltern": "kanon:seimensch-ki", "alias_cluster": ["titel:ClayVerse"],
    },
    "kanon:claycode": {
        "name": "ClayCode", "eltern": "kanon:seimensch-ki", "alias_cluster": ["titel:ClayCode"],
    },
    "kanon:claygraph": {
        "name": "ClayGraph", "eltern": "kanon:seimensch-ki", "alias_cluster": ["titel:ClayGraph"],
    },
    "kanon:unifieddb": {
        "name": "UnifiedDB", "eltern": "kanon:seimensch-ki", "alias_projekt": ["unifieddb"],
    },
    "kanon:retina": {
        "name": "Retina / Digital Retina", "eltern": "kanon:seimensch-ki",
        "alias_projekt": ["digital-retina", "retina"],
    },
    "kanon:frank": {
        "name": "Forschungsentität / Frank", "eltern": "kanon:seimensch-ki",
        "alias_projekt": ["Project-Frankenstein", "frank-demo"],
    },
    "kanon:clay-institut": {
        "name": "Clay-Forschungsentität (Institut)", "eltern": "kanon:seimensch-ki",
        "alias_projekt": ["clay-global-research-entity", "clay", "clayverse-bau",
                          "clayverse-strom", "kartographie", "daemonweave"],
    },
    "kanon:omnimind": {
        "name": "OmniMind", "eltern": "kanon:seimensch-ki",
        "muster": ["omnimind"],
    },
    "kanon:synteq": {
        "name": "SynthEq (Synthetic Equilibrium)", "eltern": "kanon:seimensch-ki",
        "muster": ["syntheq", "synthetic equilibrium", "synthetic-equilibrium"],
    },
    "kanon:tavern": {
        "name": "tAvern", "eltern": "kanon:seimensch-ki",
        "muster": ["tavern", "swarm-werkzeug"],
    },
}


def _kanon_treffer_ids(db, muster: list, kontext_muster: list | None = None) -> set:
    """Mechanische LIKE-Suche ueber titel/tags/quelle -- echte Artikel-IDs,
    nichts geraten. `kontext_muster` ist ein UND-Zusatzfilter (z.B. "seimensch"),
    damit generische Woerter ("workshop", "projekte") nicht querbeet im
    18k-Artikel-Forschungskorpus zuschlagen."""
    if not muster:
        return set()
    ids = set()
    for m in muster:
        bed = "(titel LIKE ? OR tags LIKE ? OR quelle LIKE ?)"
        par = [f"%{m}%", f"%{m}%", f"%{m}%"]
        if kontext_muster:
            teil = " OR ".join(["titel LIKE ? OR tags LIKE ? OR quelle LIKE ?"] * len(kontext_muster))
            for km in kontext_muster:
                par += [f"%{km}%", f"%{km}%", f"%{km}%"]
            bed = f"({bed}) AND ({teil})"
        for r in db.db.execute(f"SELECT id FROM artikel WHERE {bed}", par).fetchall():
            ids.add(r["id"])
    return ids


def kanon_anwenden(db) -> dict:
    """Traegt KANON_BAUM in om_projekt ein -- IMMER NACH projekt_cluster()
    aufgerufen (dessen eigenes Upsert wuerde eine vorherige Reparentierung
    sonst wieder ueberschreiben). Reparentiert vorhandene feld:/titel:-Knoten
    eigner-autoritativ und legt fuer Marken ohne eigenen Cluster einen neuen,
    mechanisch befuellten Knoten an."""
    import time as _t
    t0 = _t.time()
    jetzt = _jetzt_iso()
    neue_knoten, reparentiert, eigene_mitglieder, umbenannt = 0, 0, 0, 0
    begr = "vom Eigner definiert (Gabriel, 2026-08-21): Teil der SeiMensch-Gesamtkarte"
    with db.tx() as sql:
        for kid, spec in KANON_BAUM.items():
            alias_ids = ([f"feld:{a}" for a in spec.get("alias_projekt") or []]
                         + list(spec.get("alias_cluster") or []))
            # ⭐ GENAU EIN Alias und kein eigenes Muster: ein Wrapper-Knoten
            # daneben waere ein zweiter Knoten mit praktisch demselben Namen
            # (z.B. "EntityOS" als Kanon-Huelle UEBER "feld:EntityOS") --
            # genau der Haarball-Fehler, den Gabriel ausdruecklich nicht will.
            # Stattdessen wird der EINE vorhandene Knoten direkt umbenannt
            # und eigner-autoritativ reparentiert, kein zweiter Knoten.
            if len(alias_ids) == 1 and not (spec.get("muster") or []):
                alias_id = alias_ids[0]
                getroffen = sql.execute(
                    "UPDATE om_projekt SET name=?, eltern_id=?, konfidenz=1.0, "
                    "begruendung=?, aktualisiert_am=? WHERE id=?",
                    (spec["name"], spec["eltern"], begr, jetzt, alias_id)).rowcount
                if getroffen:
                    reparentiert += 1
                    umbenannt += 1
                continue

            sql.execute(
                "INSERT INTO om_projekt(id,name,art,eltern_id,konfidenz,begruendung,"
                "anzahl_artikel,aktualisiert_am) VALUES(?,?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name, eltern_id=excluded.eltern_id,"
                " konfidenz=excluded.konfidenz, begruendung=excluded.begruendung,"
                " aktualisiert_am=excluded.aktualisiert_am",
                (kid, spec["name"], "eigner", spec["eltern"], 1.0, begr, 0, jetzt))
            neue_knoten += 1
            eigene_ids = _kanon_treffer_ids(db, spec.get("muster") or [], spec.get("kontext_muster"))
            for aid in eigene_ids:
                sql.execute(
                    "INSERT INTO om_projekt_mitglied(artikel_id,projekt_id,konfidenz) VALUES(?,?,?) "
                    "ON CONFLICT(artikel_id,projekt_id) DO UPDATE SET konfidenz=excluded.konfidenz",
                    (aid, kid, 0.85 if spec.get("kontext_muster") else 0.92))
                eigene_mitglieder += 1
            for alias_id in alias_ids:
                getroffen = sql.execute(
                    "UPDATE om_projekt SET eltern_id=?, aktualisiert_am=? WHERE id=?",
                    (kid, jetzt, alias_id)).rowcount
                if getroffen:
                    reparentiert += 1
        # anzahl_artikel je Kanon-Knoten NACHTRAEGLICH aus om_projekt_mitglied
        # zaehlen -- reparentierte Kinder zaehlen eigene Bestaende, keine
        # Duplizierung noetig, das Frontend summiert die Kinder selbst.
        for kid in KANON_BAUM:
            n = sql.execute(
                "SELECT COUNT(*) n FROM om_projekt_mitglied WHERE projekt_id=?", (kid,)).fetchone()[0]
            sql.execute("UPDATE om_projekt SET anzahl_artikel=? WHERE id=?", (n, kid))
    ergebnis = {"knoten": neue_knoten, "reparentiert": reparentiert, "eigene_mitglieder": eigene_mitglieder, "umbenannt": umbenannt}
    _protokoll(db, "kanon_anwenden", True, neue_knoten, (_t.time() - t0) * 1000, str(ergebnis))
    return ergebnis


def lauf(db) -> dict:
    ergebnis = {}
    # kanon_anwenden() IMMER direkt nach projekt_cluster(): dessen Upsert
    # setzt eltern_id aus der autonomen Rechnung neu (auch NULL) und wuerde
    # eine vorherige Reparentierung sonst bei jedem Lauf wieder loeschen.
    for name, fn in (("projekt_cluster", projekt_cluster),
                      ("kanon_anwenden", kanon_anwenden),
                      ("implikationen", implikationen_ableiten),
                      ("zusammenfassungen", zusammenfassungen_erzeugen),
                      ("skizzen", skizzen_erzeugen)):
        t0 = time.time()
        try:
            ergebnis[name] = fn(db)
        except Exception as e:  # ein Schritt scheitert nie den ganzen Lauf
            ergebnis[name] = {"fehler": f"{type(e).__name__}: {e}"}
            _protokoll(db, name, False, 0, (time.time() - t0) * 1000, f"{type(e).__name__}: {e}")
    return ergebnis


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="/var/lib/clay/wiki.db")
    ap.add_argument("--schritt", choices=["alle", "projekt_cluster", "kanon_anwenden",
                                          "implikationen", "zusammenfassungen", "skizzen"],
                    default="alle")
    a = ap.parse_args()

    from clayverse.store import UnifiedDB
    db = UnifiedDB(a.db)
    try:
        if a.schritt == "alle":
            ergebnis = lauf(db)
        else:
            funktion = {"projekt_cluster": projekt_cluster, "kanon_anwenden": kanon_anwenden,
                        "implikationen": implikationen_ableiten,
                        "zusammenfassungen": zusammenfassungen_erzeugen,
                        "skizzen": skizzen_erzeugen}[a.schritt]
            ergebnis = {a.schritt: funktion(db)}
        print(json.dumps(ergebnis, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
