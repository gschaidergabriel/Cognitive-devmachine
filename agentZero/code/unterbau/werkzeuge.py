#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""werkzeuge.py -- ClayVerse greift nach aussen. Ein Werkzeugkasten, eine Form.

Aufrufe
  werkzeuge.py suche      --frage "..."  [--tiefe kurz|lang] [--treffer N]
  werkzeuge.py literatur  --frage "..."  [--treffer N] [--ab-jahr J]
  werkzeuge.py sandkasten --code datei.py [--zeit S]
  werkzeuge.py stand      [--tage N]
Ueberall zusaetzlich: --json, --konto, --auswaerts (Stufe 1 uebergehen),
--schwelle N (ab wie vielen eigenen Treffern der Bestand genuegt).

------------------------------------------------------------------------
RANGFOLGE -- als Code, nicht als Rat
------------------------------------------------------------------------
  1. der eigene Bestand   wiki.db / ClayGraph. Kostet nichts. IMMER zuerst.
  2. freie Werkzeuge      Tavily, Exa, OpenAlex, E2B. Kostet freies Kontingent.
  3. Claude Code          kostet Gabriels Kontingent. ZULETZT.

Stufe 1 laeuft bei `suche` und `literatur` VOR jedem Griff nach aussen und
laesst sich nicht versehentlich ueberspringen -- nur mit ausdruecklichem
--auswaerts. Genuegen die eigenen Treffer (>= --schwelle, Vorgabe 3), gibt
das Werkzeug SIE zurueck und geht gar nicht erst hinaus; der gesparte Griff
wird gezaehlt. `werkzeuge.py stand` zeigt diese Zahl -- sie ist der Beleg,
dass die Regel wirkt.
Stufe 3 kann dieses Werkzeug nicht ausloesen. Es meldet nur, wenn 1 und 2
nichts hergaben -- dann erst darf der Aufrufer Claude bemuehen.

------------------------------------------------------------------------
WELCHES WERKZEUG FUER WELCHE FRAGE
------------------------------------------------------------------------
  Frage                                     Werkzeug        warum
  ----------------------------------------  --------------  --------------
  steht schon bei uns (Projekt, Person,     KEINS           Stufe 1 fangt
  frueherer Befund, eigene Messung)         (eigener        das ab. Draussen
                                            Bestand)        fragen, was
                                                            drinnen liegt,
                                                            ist Verschwendung.
  wissenschaftliche Behauptung, die einen   literatur       OpenAlex liefert
  Beleg braucht (Studie, Wirksamkeit,       (OpenAlex)      DOI, Jahr,
  Zitierbarkeit)                                            Zitationen --
                                                            zitierfaehig.
  aktuelle Tatsache, Doku, Preis, Version,  suche           Tavily ist auf
  API-Form, Nachricht                       (Tavily)        LLM-Antworten
                                                            gebaut, kurze
                                                            Auszuege.
  Tavily faellt aus, oder die Frage ist     suche           Exa sucht
  begrifflich statt woertlich ("etwas wie   (Exa, Rueck-    bedeutungsnah
  X")                                       fall)           statt woertlich.
  Rechnung, Datenumformung, Codeprobe --    sandkasten      laeuft fremd,
  etwas AUSFUEHREN statt nachlesen          (E2B)           nicht auf
                                                            unserem Wirt.
  Meinung, Wertung, Formulierung, Plan      KEINS           dafuer ist kein
                                                            Suchdienst da.

  RapidAPI ist hier bewusst NICHT eingebaut: gemessen 2026-08-15 antwortet
  jede geprobte API 403 "You are not subscribed to this API". Der Schluessel
  ist gueltig, aber ohne Abonnement je API im RapidAPI-Konto nutzlos.

------------------------------------------------------------------------
BELEG, NICHT WAHRHEIT
------------------------------------------------------------------------
Was von draussen kommt, ist ein Beleg. Es geht NIE nach `artikel`, sondern
nach `anreicherung` mit gesetzter quelle_url. Diese Datei schreibt von sich
aus gar nichts ins Wiki -- sie liefert quelle_url mit, damit der Aufrufer es
richtig ablegen kann.

Jeder Lauf steht in `bahn_lauf` mit art='werkzeug' -- Puls, Wache und
Hauptbuch schauen an DIESER einen Stelle nach, es gibt keinen zweiten Ort.

Nur stdlib. Schluesselwerte werden nie ausgegeben und nie geloggt.
"""

import argparse
import base64
import json
import os
import re
import sqlite3
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

# Modulgrenze: der LESE-Zweig oeffnet die Datenbank nicht mehr selbst.
# udb ist die Vordertuer fuer den nur-lesenden Fall; der Schreib-Zweig
# bleibt lokal, weil udb.verbindung() strukturell nur liest.
sys.path.insert(0, "/opt/unifieddb")
import udb

DB_PATH = "/var/lib/clay/wiki.db"
ENV_PFAD = "/etc/clayverse/freie-zugaenge.env"
KONTINGENT = "/opt/clayverse/werkzeug/kontingent.py"
KONTO_VORGABE = "clayverse"          # steht so im Katalog; NICHT clayverse_grundlast
# Eigene Kennung. Eine nackte python-urllib-Kennung hat uns am 2026-08-15
# schon eine Bahn gekostet (Cloudflare 403, code 1010).
UA = "ClayVerse/1.0 (+https://frank.ink; mailto:genuinos@gmail.com)"
MAILTO = "genuinos@gmail.com"

HINWEIS = ("Belege, keine Wahrheit. Uebernahme ins Wiki nur ueber "
           "`anreicherung` mit quelle_url -- nie direkt nach `artikel`.")


# ------------------------------------------------------------- Schluessel --

def schluessel(name):
    """Liest EINEN Wert aus der Tresordatei. Gibt ihn zurueck, gibt ihn nie
    aus. Fehlt er, ist das ein klarer Abbruch statt eines stillen 401."""
    if not os.path.exists(ENV_PFAD):
        raise SystemExit(f"Tresordatei fehlt: {ENV_PFAD}")
    for zeile in open(ENV_PFAD, encoding="utf-8"):
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        k, v = zeile.split("=", 1)
        if k.strip() == name:
            v = v.strip().strip('"').strip("'")
            if not v:
                raise SystemExit(f"{name} steht in {ENV_PFAD}, ist aber leer.")
            return v
    raise SystemExit(f"{name} steht nicht in {ENV_PFAD}.")


# ------------------------------------------------------------------ Netz --

def hole(url, daten=None, kopf=None, methode=None, frist=45):
    """Ein HTTP-Aufruf, immer mit eigener Kennung. Gibt (status, leib, ms)."""
    k = {"User-Agent": UA}
    k.update(kopf or {})
    if daten is not None and not isinstance(daten, bytes):
        daten = json.dumps(daten).encode("utf-8")
        k.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=daten, headers=k, method=methode)
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=frist) as a:
            return a.status, a.read(), (time.time() - t0) * 1000
    except urllib.error.HTTPError as e:
        return e.code, e.read(), (time.time() - t0) * 1000
    except Exception as e:                                    # Netz, DNS, TLS
        return 0, str(e).encode("utf-8"), (time.time() - t0) * 1000


def kuerze(text, saetze=3, zeichen=420):
    """Titel und URL bleiben ganz, der Text wird auf 2-3 Saetze gestutzt.
    ClayVerse bezahlt jedes Token, das es liest."""
    if not text:
        return ""
    t = " ".join(str(text).split())
    teile = re.split(r"(?<=[.!?])\s+", t)
    aus = " ".join(teile[:saetze])
    if len(aus) > zeichen:
        aus = aus[:zeichen].rsplit(" ", 1)[0] + " …"
    return aus


# -------------------------------------------------------------- Datenbank --

def db(schreibend=False):
    if schreibend:
        con = sqlite3.connect(DB_PATH, timeout=20)
    else:
        con = udb.verbindung()
    con.row_factory = sqlite3.Row
    return con


def bahn_schreiben(bahn, ziel, dauer_ms, http, ergebnis, pruefung, antwort):
    """Ein Lauf, eine Zeile, art='werkzeug'. Spalten ausdruecklich benannt --
    INSERT OR REPLACE mit Teilspalten hat hier schon dreimal Daten geloescht,
    darum hier ein reines INSERT mit vollstaendiger Liste."""
    try:
        con = db(schreibend=True)
        con.execute(
            "INSERT INTO bahn_lauf "
            "(zeit, art, bahn, modell, ziel_id, dauer_ms, http, "
            " token_ein, token_aus, ergebnis, pruefung, antwort) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), "werkzeug", bahn, None,
             ziel, dauer_ms, http, None, None, ergebnis, pruefung,
             json.dumps(antwort, ensure_ascii=False)[:4000]))
        con.commit()
        con.close()
    except Exception as e:
        # Buchfuehrung darf das Werkzeug nie zum Absturz bringen, aber sie
        # darf auch nicht stumm verschwinden.
        print(f"[warnung] bahn_lauf nicht geschrieben: {e}", file=sys.stderr)


# ------------------------------------------------- Stufe 1: eigener Bestand --

def _fts_ausdruck(frage, verbinder):
    """Aus freier Frage einen FTS5-Ausdruck bauen. Jedes Wort einzeln
    gequotet -- sonst wirft FTS5 bei Bindestrich, Doppelpunkt oder 'AND'
    im Fragetext einen Syntaxfehler."""
    woerter = [w for w in re.findall(r"[\wÀ-ɏ]+", frage, re.UNICODE)
               if len(w) > 2]
    if not woerter:
        return None
    return f" {verbinder} ".join('"' + w.replace('"', '') + '"'
                                 for w in woerter[:12])


def eigener_bestand(frage, limit=5):
    """Was haben WIR schon dazu? Erst alle Woerter (streng), sonst
    irgendeines (weit). Gibt (treffer, streng)."""
    con = db()
    try:
        for verbinder, streng in (("AND", True), ("OR", False)):
            m = _fts_ausdruck(frage, verbinder)
            if not m:
                return [], False
            try:
                zeilen = con.execute(
                    "SELECT s.artikel_id AS aid, s.titel AS titel, "
                    "       snippet(fts_index_artikel, 1, '', '', ' … ', 20) "
                    "         AS auszug, "
                    "       bm25(fts_index_artikel) AS rang "
                    "FROM fts_index_artikel "
                    "JOIN artikel_suchtext s ON s.id = fts_index_artikel.rowid "
                    "LEFT JOIN artikel a ON a.id = s.artikel_id "
                    "WHERE fts_index_artikel MATCH ? "
                    "  AND COALESCE(a.verfallen, 0) = 0 "
                    "ORDER BY rang LIMIT ?",
                    (m, limit)).fetchall()
            except sqlite3.OperationalError as e:
                print(f"[warnung] eigene Suche: {e}", file=sys.stderr)
                return [], False
            if zeilen:
                return ([{"titel": z["titel"] or z["aid"],
                          "url": f"wiki://artikel/{z['aid']}",
                          "auszug": kuerze(z["auszug"], 3, 320),
                          "rang": round(z["rang"], 3)} for z in zeilen],
                        streng)
        return [], False
    finally:
        con.close()


def stufe1(frage, schwelle, auswaerts, werkzeug, limit=5):
    """Das Tor. Gibt (fertig, ergebnis_oder_bestandsinfo).
    fertig=True heisst: der eigene Bestand genuegt, es geht NICHT hinaus."""
    t0 = time.time()
    treffer, streng = eigener_bestand(frage, max(limit, 5))
    dauer = (time.time() - t0) * 1000
    info = {"treffer": len(treffer), "streng": streng, "dauer_ms": round(dauer, 1)}

    if auswaerts:
        info["genutzt"] = False
        info["grund"] = "--auswaerts ausdruecklich gesetzt"
        return False, info, treffer

    genuegt = streng and len(treffer) >= schwelle
    if genuegt:
        erg = {"werkzeug": werkzeug, "frage": frage, "stufe": 1,
               "quelle": "eigener_bestand", "gespart": True,
               "eigener_bestand": dict(info, genutzt=True),
               "treffer": treffer[:limit], "dauer_ms": round(dauer, 1),
               "hinweis": ("Aus dem eigenen Bestand beantwortet -- kein "
                           "Griff nach draussen, kein Kontingent verbraucht.")}
        bahn_schreiben("eigener_bestand", frage[:200], dauer, None,
                       "angenommen", "Stufe 1 genuegt -- Aussenaufruf gespart",
                       {"werkzeug": werkzeug, "treffer": len(treffer)})
        return True, info, erg

    info["genutzt"] = False
    info["grund"] = (f"nur {len(treffer)} eigene Treffer "
                     f"({'streng' if streng else 'weit'}), "
                     f"Schwelle ist {schwelle}")
    return False, info, treffer


# ------------------------------------------------------------ Kontingent ---

def darf(konto, zugang, menge):
    """Fragt kontingent.py. Kein Aussenaufruf ohne diese Frage."""
    p = subprocess.run(
        [sys.executable, KONTINGENT, "darf", "--konto", konto,
         "--zugang", zugang, "--menge", str(menge), "--json"],
        capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise SystemExit(f"kontingent.py darf ist gescheitert "
                         f"({zugang}): {(p.stderr or p.stdout).strip()[:400]}")
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"kontingent.py darf gab kein JSON: "
                         f"{p.stdout.strip()[:300]}")
    return d


def buchen(konto, zugang, menge, einheit, zweck):
    p = subprocess.run(
        [sys.executable, KONTINGENT, "buchen", "--konto", konto,
         "--zugang", zugang, "--menge", str(menge),
         "--einheit", einheit, "--zweck", zweck[:180]],
        capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        print(f"[warnung] buchen gescheitert ({zugang}): "
              f"{(p.stderr or p.stdout).strip()[:300]}", file=sys.stderr)
        return False
    return True


def tor(konto, zugang, menge, einheit, zweck):
    """darf -> (Aufruf) -> buchen. Gibt eine Buchungsfunktion zurueck, die
    der Aufrufer NACH dem geglueckten Aufruf ruft."""
    d = darf(konto, zugang, menge)
    if d.get("erlaubt", 0) < menge:
        raise SystemExit(
            f"Kontingent sagt nein: {zugang} erlaubt nur "
            f"{d.get('erlaubt')} von {menge} ({d.get('grund')}). "
            f"Nicht ausgefuehrt.")
    return lambda: buchen(konto, zugang, menge, einheit, zweck)


# ------------------------------------------------------- Stufe 2: draussen --

def tavily(frage, treffer, tiefe):
    tief = "advanced" if tiefe == "lang" else "basic"
    st, leib, ms = hole(
        "https://api.tavily.com/search",
        {"query": frage, "max_results": treffer, "search_depth": tief,
         "include_answer": tiefe == "lang"},
        {"Authorization": "Bearer " + schluessel("TAVILY_API_KEY")})
    if st != 200:
        return None, st, ms, leib[:300].decode("utf-8", "replace")
    d = json.loads(leib)
    aus = [{"titel": r.get("title") or r.get("url"),
            "url": r.get("url"),
            "auszug": kuerze(r.get("content"))}
           for r in d.get("results", [])[:treffer]]
    return {"treffer": aus, "kurzantwort": kuerze(d.get("answer"), 3, 500)}, \
           st, ms, None


def exa(frage, treffer):
    st, leib, ms = hole(
        "https://api.exa.ai/search",
        {"query": frage, "numResults": treffer,
         "contents": {"text": {"maxCharacters": 700}}},
        {"x-api-key": schluessel("EXA_API_KEY")})
    if st != 200:
        return None, st, ms, leib[:300].decode("utf-8", "replace")
    d = json.loads(leib)
    aus = [{"titel": r.get("title") or r.get("url"),
            "url": r.get("url"),
            "auszug": kuerze(r.get("text"))}
           for r in d.get("results", [])[:treffer]]
    return {"treffer": aus, "kurzantwort": ""}, st, ms, None


def openalex(frage, treffer, ab_jahr):
    """Der Schluessel ist hier KEINE Formsache: gemessen bringt er
    10.000 statt 1.000 Credits am Tag. Ohne Schluessel wird trotzdem
    gearbeitet (polite pool mit mailto), nur zehnmal knapper."""
    from urllib.parse import quote
    try:
        k = schluessel("OPENALEX_API_KEY")
        zusatz = "&api_key=" + quote(k)
        mit_key = True
    except SystemExit:
        zusatz = "&mailto=" + quote(MAILTO)
        mit_key = False
    filt = f"&filter=publication_year:>{ab_jahr - 1}" if ab_jahr else ""
    url = (f"https://api.openalex.org/works?search={quote(frage)}"
           f"&per-page={treffer}{filt}"
           f"&select=id,doi,title,publication_year,cited_by_count,"
           f"authorships,primary_location,abstract_inverted_index{zusatz}")
    st, leib, ms = hole(url, None, {})
    if st != 200:
        return None, st, ms, leib[:300].decode("utf-8", "replace"), mit_key
    d = json.loads(leib)
    aus = []
    for w in d.get("results", [])[:treffer]:
        # Der Kurzfassungstext liegt invertiert vor (Wort -> Positionen).
        kf = ""
        inv = w.get("abstract_inverted_index") or {}
        if inv:
            paare = [(p, wort) for wort, pos in inv.items() for p in pos]
            paare.sort()
            kf = " ".join(wort for _, wort in paare[:120])
        autoren = [a.get("author", {}).get("display_name")
                   for a in (w.get("authorships") or [])[:3]]
        autoren = [a for a in autoren if a]
        ort = (w.get("primary_location") or {}).get("source") or {}
        aus.append({
            "titel": w.get("title") or "(ohne Titel)",
            "url": w.get("doi") or w.get("id"),
            "jahr": w.get("publication_year"),
            "zitiert": w.get("cited_by_count"),
            "autoren": ", ".join(autoren) + (" u.a." if len(
                w.get("authorships") or []) > 3 else ""),
            "wo": ort.get("display_name"),
            "auszug": kuerze(kf)})
    return ({"treffer": aus, "gesamt": (d.get("meta") or {}).get("count")},
            st, ms, None, mit_key)


# ----------------------------------------------------- Stufe 2: Sandkasten --

def _rahmen_lesen(leib):
    """Connect-Streaming: [1 Byte Flags][4 Byte Laenge][Rumpf]. Der Weg ohne
    SDK -- gemessen 2026-08-15, HTTP 200."""
    aus, i = [], 0
    while i + 5 <= len(leib):
        flags, laenge = struct.unpack(">BI", leib[i:i + 5])
        rumpf = leib[i + 5:i + 5 + laenge]
        i += 5 + laenge
        try:
            aus.append((flags, json.loads(rumpf.decode("utf-8"))))
        except Exception:
            aus.append((flags, {"roh": rumpf[:200].decode("utf-8", "replace")}))
    return aus


def sandkasten_lauf(code, frist_s):
    """Sandkasten erzeugen, Code ausfuehren, Sandkasten IMMER wieder
    loeschen. Der Code geht base64-verpackt hinueber -- so kann kein
    Anfuehrungszeichen im Code die Kommandozeile drueben zerreissen."""
    k = schluessel("E2B_API_KEY")
    st, leib, ms = hole("https://api.e2b.app/sandboxes",
                        {"templateID": "base", "timeout": max(frist_s + 60, 120)},
                        {"X-API-KEY": k})
    if st not in (200, 201):
        return None, st, ms, leib[:300].decode("utf-8", "replace")
    sb = json.loads(leib)["sandboxID"]
    gesamt_ms = ms
    try:
        b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")
        befehl = ("echo " + b64 + " | base64 -d > /home/user/lauf.py && "
                  "python3 /home/user/lauf.py")
        nutz = json.dumps({"process": {
            "cmd": "/bin/bash", "args": ["-lc", befehl],
            "cwd": "/home/user"}}).encode("utf-8")
        st2, leib2, ms2 = hole(
            "https://sandbox.e2b.app/process.Process/Start",
            struct.pack(">BI", 0, len(nutz)) + nutz,
            {"Content-Type": "application/connect+json",
             "Connect-Protocol-Version": "1",
             "E2b-Sandbox-Id": sb, "E2b-Sandbox-Port": "49983",
             "X-API-KEY": k},
            frist=frist_s + 30)
        gesamt_ms += ms2
        if st2 != 200:
            return None, st2, gesamt_ms, leib2[:300].decode("utf-8", "replace")
        aus, fehler, code_ende = [], [], None
        for _flags, e in _rahmen_lesen(leib2):
            ev = (e.get("event") or {})
            d = ev.get("data") or {}
            if d.get("stdout"):
                aus.append(base64.b64decode(d["stdout"]).decode("utf-8", "replace"))
            if d.get("stderr"):
                fehler.append(base64.b64decode(d["stderr"]).decode("utf-8", "replace"))
            if ev.get("end"):
                code_ende = ev["end"].get("status")
        return ({"ausgabe": "".join(aus)[-4000:],
                 "fehlerausgabe": "".join(fehler)[-2000:],
                 "ende": code_ende, "sandkasten": sb},
                st2, gesamt_ms, None)
    finally:
        hole(f"https://api.e2b.app/sandboxes/{sb}", None,
             {"X-API-KEY": k}, "DELETE", frist=20)


# ------------------------------------------------------------- Befehle -----

def cmd_suche(a):
    fertig, info, x = stufe1(a.frage, a.schwelle, a.auswaerts, "suche", a.treffer)
    if fertig:
        return x
    eigene = x

    zweck = "suche: " + a.frage[:120]
    einloesen = tor(a.konto, "tavily", 2 if a.tiefe == "lang" else 1,
                   "credits", zweck)
    d, st, ms, fehler = tavily(a.frage, a.treffer, a.tiefe)
    quelle, rueckfall = "tavily", None
    if d is not None:
        einloesen()
    else:
        rueckfall = f"tavily http={st}: {fehler}"
        bahn_schreiben("tavily", a.frage[:200], ms, st, "fehler", fehler,
                       {"werkzeug": "suche"})
        # Rueckfall auf Exa -- eigenes Tor, eigene Buchung.
        einloesen2 = tor(a.konto, "exa", 1, "credits", zweck)
        d, st, ms2, fehler2 = exa(a.frage, a.treffer)
        ms += ms2
        quelle = "exa"
        if d is None:
            bahn_schreiben("exa", a.frage[:200], ms2, st, "fehler", fehler2,
                           {"werkzeug": "suche"})
            raise SystemExit(
                f"Stufe 1 und Stufe 2 haben nichts geliefert "
                f"(tavily: {rueckfall} / exa http={st}: {fehler2}). "
                f"Erst JETZT waere Claude (Stufe 3) an der Reihe.")
        einloesen2()

    erg = {"werkzeug": "suche", "frage": a.frage, "stufe": 2, "quelle": quelle,
           "gespart": False, "eigener_bestand": info,
           "eigene_treffer": eigene[:3],
           "kurzantwort": d.get("kurzantwort", ""),
           "treffer": d["treffer"], "dauer_ms": round(ms, 1),
           "hinweis": HINWEIS}
    if rueckfall:
        erg["rueckfall"] = rueckfall
    bahn_schreiben(quelle, a.frage[:200], ms, st, "angenommen", None,
                   {"werkzeug": "suche", "treffer": len(d["treffer"]),
                    "eigene_treffer": info["treffer"]})
    return erg


def cmd_literatur(a):
    fertig, info, x = stufe1(a.frage, a.schwelle, a.auswaerts, "literatur",
                             a.treffer)
    if fertig:
        return x
    eigene = x

    # Eine Werksuche kostet gemessen 10 Credits (0,001 USD).
    einloesen = tor(a.konto, "openalex", 10, "credits",
                   "literatur: " + a.frage[:120])
    d, st, ms, fehler, mit_key = openalex(a.frage, a.treffer, a.ab_jahr)
    if d is None:
        bahn_schreiben("openalex", a.frage[:200], ms, st, "fehler", fehler,
                       {"werkzeug": "literatur"})
        raise SystemExit(f"OpenAlex http={st}: {fehler}")
    einloesen()
    erg = {"werkzeug": "literatur", "frage": a.frage, "stufe": 2,
           "quelle": "openalex", "gespart": False, "eigener_bestand": info,
           "eigene_treffer": eigene[:3],
           "mit_schluessel": mit_key,
           "gesamt_werke": d.get("gesamt"),
           "treffer": d["treffer"], "dauer_ms": round(ms, 1),
           "hinweis": HINWEIS}
    bahn_schreiben("openalex", a.frage[:200], ms, st, "angenommen", None,
                   {"werkzeug": "literatur", "treffer": len(d["treffer"]),
                    "eigene_treffer": info["treffer"]})
    return erg


def cmd_sandkasten(a):
    if not os.path.exists(a.code):
        raise SystemExit(f"Codedatei fehlt: {a.code}")
    code = open(a.code, encoding="utf-8").read()
    einloesen = tor(a.konto, "e2b", 1, "sandkaesten",
                   "sandkasten: " + os.path.basename(a.code))
    d, st, ms, fehler = sandkasten_lauf(code, a.zeit)
    if d is None:
        bahn_schreiben("e2b", os.path.basename(a.code), ms, st, "fehler",
                       fehler, {"werkzeug": "sandkasten"})
        raise SystemExit(f"E2B http={st}: {fehler}")
    einloesen()
    erg = {"werkzeug": "sandkasten", "datei": a.code, "stufe": 2,
           "quelle": "e2b", "gespart": False,
           "ausgabe": d["ausgabe"], "fehlerausgabe": d["fehlerausgabe"],
           "ende": d["ende"], "dauer_ms": round(ms, 1),
           "hinweis": "Fremder Rechner, nicht unser Wirt. " + HINWEIS}
    bahn_schreiben("e2b", os.path.basename(a.code), ms, st, "angenommen", None,
                   {"werkzeug": "sandkasten", "ende": d["ende"]})
    return erg


def cmd_stand(a):
    """Der Beleg, dass die Rangfolge wirkt: wie oft hat Stufe 1 einen Griff
    nach draussen erspart."""
    seit = (datetime.now(timezone.utc) - timedelta(days=a.tage)).isoformat()
    con = db()
    zeilen = con.execute(
        "SELECT bahn, ergebnis, COUNT(*) n, ROUND(AVG(dauer_ms),1) ms "
        "FROM bahn_lauf WHERE art='werkzeug' AND zeit >= ? "
        "GROUP BY bahn, ergebnis ORDER BY bahn, ergebnis", (seit,)).fetchall()
    con.close()
    je = {}
    for z in zeilen:
        je.setdefault(z["bahn"], {})[z["ergebnis"]] = {"n": z["n"], "ms": z["ms"]}
    gespart = je.get("eigener_bestand", {}).get("angenommen", {}).get("n", 0)
    draussen = sum(v.get("angenommen", {}).get("n", 0)
                   for k, v in je.items() if k != "eigener_bestand")
    ges = gespart + draussen
    return {"werkzeug": "stand", "tage": a.tage, "je_bahn": je,
            "gesparte_aussenaufrufe": gespart,
            "aussenaufrufe": draussen,
            "sparquote_prozent": round(100.0 * gespart / ges, 1) if ges else None,
            "hinweis": ("gesparte_aussenaufrufe = Laeufe, die der eigene "
                        "Bestand allein beantwortet hat.")}


# -------------------------------------------------------------- Ausgabe ----

def zeigen(e):
    w = e.get("werkzeug")
    if w == "stand":
        print(f"\nWerkzeug-Stand der letzten {e['tage']} Tage")
        for bahn, arten in sorted(e["je_bahn"].items()):
            teile = ", ".join(f"{k}={v['n']} (Ø {v['ms']} ms)"
                              for k, v in sorted(arten.items()))
            print(f"  {bahn:<18} {teile}")
        print(f"\n  gesparte Aussenaufrufe : {e['gesparte_aussenaufrufe']}")
        print(f"  tatsaechlich draussen   : {e['aussenaufrufe']}")
        q = e["sparquote_prozent"]
        print(f"  Sparquote               : "
              f"{str(q) + ' %' if q is not None else 'noch keine Laeufe'}\n")
        return
    if w == "sandkasten":
        print(f"\n[{e['quelle']}] {e['datei']}  ({e['dauer_ms']} ms, "
              f"{e['ende']})")
        print("--- Ausgabe ---")
        print(e["ausgabe"].rstrip() or "(leer)")
        if e["fehlerausgabe"].strip():
            print("--- Fehlerausgabe ---")
            print(e["fehlerausgabe"].rstrip())
        print()
        return

    b = e.get("eigener_bestand", {})
    print(f"\nFrage: {e['frage']}")
    print(f"Eigener Bestand: wir haben dazu schon {b.get('treffer', 0)} "
          f"Artikel ({b.get('dauer_ms', 0)} ms)"
          + ("  -> genutzt, kein Aussenaufruf" if e.get("gespart")
             else f"  -> {b.get('grund', '')}"))
    if e.get("rueckfall"):
        print(f"Rueckfall: {e['rueckfall']}")
    print(f"Quelle: {e['quelle']}  ({e['dauer_ms']} ms)")
    if e.get("kurzantwort"):
        print(f"Kurzantwort: {e['kurzantwort']}")
    if e.get("gesamt_werke") is not None:
        print(f"OpenAlex kennt insgesamt {e['gesamt_werke']} Werke dazu"
              + ("" if e.get("mit_schluessel") else
                 "  [OHNE unseren Schluessel -- polite pool, 10x knapper]"))
    print()
    for i, t in enumerate(e.get("treffer", []), 1):
        kopf = f"{i}. {t['titel']}"
        if t.get("jahr"):
            kopf += f"  ({t['jahr']}, {t.get('zitiert', 0)}x zitiert)"
        print(kopf)
        if t.get("autoren"):
            print(f"   {t['autoren']}" + (f" — {t['wo']}" if t.get("wo") else ""))
        print(f"   {t['url']}")
        if t.get("auszug"):
            print(f"   {t['auszug']}")
        print()
    if e.get("eigene_treffer"):
        print("Eigene Treffer (schwaecher als die Schwelle, trotzdem hier):")
        for t in e["eigene_treffer"]:
            print(f"   - {t['titel']}  {t['url']}")
        print()
    print(e.get("hinweis", ""))
    print()


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    u = p.add_subparsers(dest="befehl", required=True)

    def gemeinsam(s, mit_stufe1=True):
        s.add_argument("--konto", default=KONTO_VORGABE)
        s.add_argument("--json", dest="als_json", action="store_true")
        if mit_stufe1:
            s.add_argument("--auswaerts", action="store_true",
                           help="Stufe 1 uebergehen und sofort nach draussen "
                                "-- nur mit gutem Grund")
            s.add_argument("--schwelle", type=int, default=3,
                           help="ab wie vielen eigenen Treffern der Bestand "
                                "genuegt (Vorgabe 3)")

    s = u.add_parser("suche", help="aktuelle Tatsachen, Doku (Tavily, Rueckfall Exa)")
    s.add_argument("--frage", required=True)
    s.add_argument("--tiefe", choices=("kurz", "lang"), default="kurz")
    s.add_argument("--treffer", type=int, default=5)
    gemeinsam(s)
    s.set_defaults(fn=cmd_suche)

    s = u.add_parser("literatur", help="wissenschaftliche Belege (OpenAlex)")
    s.add_argument("--frage", required=True)
    s.add_argument("--treffer", type=int, default=5)
    s.add_argument("--ab-jahr", dest="ab_jahr", type=int, default=None)
    gemeinsam(s)
    s.set_defaults(fn=cmd_literatur)

    s = u.add_parser("sandkasten", help="Code fremd ausfuehren (E2B)")
    s.add_argument("--code", required=True)
    s.add_argument("--zeit", type=int, default=60, help="Frist in Sekunden")
    gemeinsam(s, mit_stufe1=False)
    s.set_defaults(fn=cmd_sandkasten)

    s = u.add_parser("stand", help="was die Werkzeuge getan und gespart haben")
    s.add_argument("--tage", type=int, default=30)
    gemeinsam(s, mit_stufe1=False)
    s.set_defaults(fn=cmd_stand)

    a = p.parse_args()
    e = a.fn(a)
    if a.als_json:
        print(json.dumps(e, ensure_ascii=False, indent=2))
    else:
        zeigen(e)


if __name__ == "__main__":
    main()
