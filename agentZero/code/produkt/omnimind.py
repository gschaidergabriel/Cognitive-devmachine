"""OmniMind -- Such- und Lese-Oberflaeche ueber den ganzen Wiki-Korpus.

Baut NICHTS von der Vorstufe nach: die Suche steht auf `fts_index_artikel`
(demselben Volltextindex wie mcp_server.korpus_suchen), das Beziehungsnetz
kommt aus `vp_weg` (dem gelernten Abrufgraphen), Personen-/Zweig-Filter aus
`entityos_artikel_zuordnung`/`artikel_sphaere`. Alles read-only auf diesen
Tabellen.

⚠️ NO_INVENTION durchgaengig:
  - Suchausschnitte, Infobox, Hypothesen, verwandte Artikel -- alles direkt
    aus echten Zeilen. Wo eine Spalte leer ist, steht das ausdruecklich da
    ("keine Hypothesen erfasst"), nichts wird nachgezeichnet.
  - Generierte Zusaetze (Zusammenfassung, Skizze, abgeleitete Implikation)
    leben in EIGENEN om_*-Tabellen, die der Anreicherungsdienst
    (omnimind_anreicherung.py) fuellt -- nie in `artikel` selbst -- und
    tragen in jeder Antwort ein sichtbares "generiert"/"modell"-Feld. Wer
    das Feld wegliesse, koennte ein generiertes Stueck fuer eine gemessene
    Tatsache halten.

Eigene Tabellen, Vorsatz `om_` (wie `wk_` der Wikiarbeit und `wa_` der
Wache je ihren eigenen Vorsatz tragen) -- ein neues Silo waere falsch,
wildes Ueberschreiben von `artikel` waere falscher.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any

# ⚠️ MODULKOPF, nicht lokal in registriere_omnimind_wege(): diese Datei
# traegt `from __future__ import annotations`, also sind alle Annotationen
# Zeichenketten -- FastAPI loest `request: Request` ueber die MODULglobalen
# auf. Als lokaler Import in der Wegefunktion bliebe der Name unaufgeloest
# und jeder Weg antwortete mit 422 ("request" als Abfrageparameter erwartet)
# statt zu arbeiten -- exakt der Fehler, den postfach.py an derselben Stelle
# schon einmal gemessen und dort ebenfalls an den Modulkopf gezogen hat.
#
# ⚠️ TROTZDEM try/except: dieses Modul wird auch von omnimind_anreicherung.py
# importiert, das auf dem WIRT laeuft (systemd, nacktes python3, kein
# fastapi) -- siehe dortiger Modulkopf. Dort wird registriere_omnimind_wege()
# nie aufgerufen, also duerfen die drei Namen dort ruhig None bleiben.
try:
    from fastapi import Request
    from fastapi.responses import JSONResponse, Response
except ImportError:  # pragma: no cover -- greift nur auf dem Wirt ohne fastapi
    Request = Response = JSONResponse = None  # type: ignore[assignment,misc]

SCHEMA = """
CREATE TABLE IF NOT EXISTS om_projekt(
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    art TEXT NOT NULL,              -- 'feld' (aus artikel.projekt) | 'cluster' (Ko-Vorkommen/Graph)
    eltern_id TEXT,                 -- NULL = keine Elternbeziehung belegt
    konfidenz REAL NOT NULL,
    begruendung TEXT NOT NULL,
    anzahl_artikel INTEGER NOT NULL DEFAULT 0,
    aktualisiert_am TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS om_projekt_mitglied(
    artikel_id TEXT NOT NULL,
    projekt_id TEXT NOT NULL,
    konfidenz REAL NOT NULL,
    PRIMARY KEY(artikel_id, projekt_id)
);
CREATE INDEX IF NOT EXISTS idx_om_mitglied_projekt ON om_projekt_mitglied(projekt_id);
CREATE INDEX IF NOT EXISTS idx_om_mitglied_artikel ON om_projekt_mitglied(artikel_id);

CREATE TABLE IF NOT EXISTS om_projekt_kante(
    a_id TEXT NOT NULL,
    b_id TEXT NOT NULL,
    staerke REAL NOT NULL,
    beleg TEXT NOT NULL,
    aktualisiert_am TEXT NOT NULL,
    PRIMARY KEY(a_id, b_id)
);

CREATE TABLE IF NOT EXISTS om_hypothese_implikation(
    id INTEGER PRIMARY KEY,
    artikel_id TEXT NOT NULL,
    hypothese_id TEXT,
    hypothese_text TEXT NOT NULL,
    text TEXT NOT NULL,
    konfidenz REAL NOT NULL,
    modell TEXT NOT NULL,
    erzeugt_am TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_om_implikation_artikel ON om_hypothese_implikation(artikel_id);

CREATE TABLE IF NOT EXISTS om_zusammenfassung(
    artikel_id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    modell TEXT NOT NULL,
    erzeugt_am TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS om_skizze(
    artikel_id TEXT PRIMARY KEY,
    mermaid TEXT NOT NULL,
    quelle TEXT NOT NULL,           -- 'mechanisch:<feld>' oder 'modell:<name>'
    erzeugt_am TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS om_lauf(
    id INTEGER PRIMARY KEY,
    zeit TEXT NOT NULL,
    schritt TEXT NOT NULL,
    ok INTEGER NOT NULL,
    anzahl INTEGER NOT NULL DEFAULT 0,
    ms INTEGER NOT NULL DEFAULT 0,
    hinweis TEXT
);
"""


def sicherstellen(db) -> None:
    db.db.executescript(SCHEMA)


def _jetzt() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


# ⚠️ Die om_*-Tabellen legt der Anreicherungsdienst an (om.sicherstellen()
# laeuft dort bei jedem Lauf) -- in Produktion existieren sie also laengst,
# wenn eine Anfrage hier ankommt. Trotzdem lesen alle Stellen unten, die
# om_projekt/om_hypothese_implikation/om_zusammenfassung/om_skizze anfassen,
# ueber DIESEN Helfer statt direkt: ein frischer Container VOR dem ersten
# Anreicherungslauf (oder ein Test mit einer nackten DB) soll eine leere
# Antwort liefern, keinen 500er wegen "no such table". Import lokal, damit
# dieses Modul bei einem `db`-Platzhalter ohne .db (siehe Terminal-Auth-
# Tests, die create_terminal_app mit db=object() aufrufen) nicht schon beim
# Registrieren der Wege stolpert -- diese Funktion wird nur innerhalb einer
# echten Anfrage aufgerufen, nie beim App-Aufbau.
def _lesen_tolerant(db, sql: str, params=(), *, viele: bool = True):
    import sqlite3
    try:
        cur = db.db.execute(sql, params)
        return cur.fetchall() if viele else cur.fetchone()
    except sqlite3.OperationalError:
        return [] if viele else None


# ── Volltextsuche mit Filtern ───────────────────────────────────────────
#
# Zweistufig wie mcp_server.korpus_suchen: erst alle Suchworte (praezise),
# dann irgendeins (locker) -- eine genaue Frage soll nicht leer bleiben, nur
# weil ein Wort im Artikel anders steht. Die Filter (Person/Zweig/Art/Projekt/
# Zeitraum/Dateien) wirken in BEIDEN Staffeln als SQL-WHERE, nicht erst
# nachtraeglich in Python -- sonst waere "50 Treffer, 3 davon sichtbar" der
# Normalfall bei engen Filtern.

_STOPP = {"der","die","das","und","oder","mit","fuer","von","nicht","ein",
          "eine","ist","was","wie","auf","aus","zu","in","im","am","an","zur"}


def _worte(frage: str) -> list[str]:
    return [w for w in re.split(r"[^0-9A-Za-zÄÖÜäöüß]+", str(frage).lower())
            if len(w) > 2 and w not in _STOPP][:8]


def _projekt_nachkommen(db, projekt_id: str) -> list[str]:
    """id + alle Kinder/Enkel in om_projekt -- rekursiv, aber flach in Python
    (die Tabelle ist klein, hunderte Zeilen, kein Grund fuer eine WITH RECURSIVE)."""
    alle = {r["id"]: r["eltern_id"] for r in
            _lesen_tolerant(db, "SELECT id, eltern_id FROM om_projekt")}
    ziel = [projekt_id]
    wachsend = True
    while wachsend:
        wachsend = False
        for pid, eltern in alle.items():
            if eltern in ziel and pid not in ziel:
                ziel.append(pid)
                wachsend = True
    return ziel


def suche(db, frage: str, *, gehoert: str | None = None, sphaere: str | None = None,
          art: str | None = None, projekt_id: str | None = None,
          seit: str | None = None, bis: str | None = None,
          hat_dateien: bool | None = None, hat_bilder: bool | None = None,
          limit: int = 20, offset: int = 0) -> dict:
    worte = _worte(frage)
    if not worte:
        return {"frage": frage, "treffer": [], "gesamt": 0,
                "hinweis": "keine brauchbaren Suchworte (zu kurz oder nur Fuellwoerter)"}

    bedingungen, parameter = [], []
    if gehoert:
        bedingungen.append(
            "a.id IN (SELECT artikel_id FROM entityos_artikel_zuordnung WHERE gehoert=?)")
        parameter.append(gehoert)
    if sphaere:
        bedingungen.append(
            "a.id IN (SELECT artikel_id FROM artikel_sphaere WHERE sphaere=?)")
        parameter.append(sphaere)
    if art:
        bedingungen.append("a.art = ?")
        parameter.append(art)
    if projekt_id:
        nachkommen = _projekt_nachkommen(db, projekt_id)
        platzhalter = ",".join("?" * len(nachkommen))
        bedingungen.append(
            f"a.id IN (SELECT artikel_id FROM om_projekt_mitglied WHERE projekt_id IN ({platzhalter}))")
        parameter.extend(nachkommen)
    if seit:
        bedingungen.append("a.erzeugt_am >= ?")
        parameter.append(seit)
    if bis:
        bedingungen.append("a.erzeugt_am <= ?")
        parameter.append(bis)
    if hat_dateien:
        bedingungen.append("a.quelle IS NOT NULL AND a.quelle <> ''")
    if hat_bilder:
        bedingungen.append(
            "(lower(a.quelle) LIKE '%.png' OR lower(a.quelle) LIKE '%.jpg' "
            "OR lower(a.quelle) LIKE '%.jpeg' OR lower(a.quelle) LIKE '%.svg' "
            "OR lower(a.quelle) LIKE '%.gif' OR lower(a.quelle) LIKE '%.webp')")
    zusatz_where = (" AND " + " AND ".join(bedingungen)) if bedingungen else ""

    grenze = max(1, min(int(limit), 60))
    pool = grenze * 4 + offset  # groesserer Kandidatenpool, damit die Graph-Neusortierung etwas zu sortieren hat

    aus, gesehen = [], set()
    for modus, ausdruck in (("alle", " AND ".join(worte)), ("irgendeins", " OR ".join(worte))):
        if len(aus) >= pool:
            break
        sql = (
            "SELECT s.artikel_id, s.titel, s.text, a.art, a.projekt, a.status, "
            "a.epistemic_class, a.erzeugt_am, a.konfidenz, bm25(fts_index_artikel) AS rang "
            "FROM fts_index_artikel f JOIN artikel_suchtext s ON s.id = f.rowid "
            "JOIN artikel a ON a.id = s.artikel_id "
            f"WHERE fts_index_artikel MATCH ? {zusatz_where} "
            "ORDER BY rang LIMIT ?"
        )
        try:
            zeilen = db.db.execute(sql, (ausdruck, *parameter, pool * 2)).fetchall()
        except Exception as e:
            return {"frage": frage, "nicht_ermittelbar": f"{type(e).__name__}: {e}"}
        for r in zeilen:
            if r["artikel_id"] in gesehen or len(aus) >= pool:
                continue
            gesehen.add(r["artikel_id"])
            aus.append(dict(r) | {"gefunden": modus})

    if not aus:
        return {"frage": frage, "treffer": [], "gesamt": 0, "worte": worte,
                "hinweis": "nichts im Korpus gefunden -- nicht aus dem Titel geraten"}

    # ⭐ Rangfolge = FTS-Rang (bm25, kleiner ist besser) UND Graph-Naehe (Grad
    # in vp_weg, gewichtet mit guete). Ein Artikel, an dem die gelernte
    # Abrufkarte viel Verkehr traegt, ist erfahrungsgemaess der brauchbarere
    # Treffer -- reines bm25 sieht diese gelernte Information gar nicht.
    ids = [r["artikel_id"] for r in aus]
    platzhalter = ",".join("?" * len(ids))
    grad = {}
    if ids:
        for row in db.db.execute(
            f"SELECT von AS id, SUM(guete) AS g FROM vp_weg WHERE von IN ({platzhalter}) GROUP BY von",
            ids,
        ).fetchall():
            grad[row["id"]] = grad.get(row["id"], 0.0) + (row["g"] or 0.0)
        for row in db.db.execute(
            f"SELECT nach AS id, SUM(guete) AS g FROM vp_weg WHERE nach IN ({platzhalter}) GROUP BY nach",
            ids,
        ).fetchall():
            grad[row["id"]] = grad.get(row["id"], 0.0) + (row["g"] or 0.0)

    rang_werte = [r["rang"] for r in aus]
    r_min, r_max = min(rang_werte), max(rang_werte)
    g_max = max(grad.values()) if grad else 0.0

    def _score(r):
        # bm25 ist NEGATIV besser in sqlite fts5 je nach Build -- hier bereits
        # "kleiner=besser", also spiegeln wir auf 0..1 mit 1=bester Rang.
        spanne = (r_max - r_min) or 1.0
        rang_norm = 1.0 - ((r["rang"] - r_min) / spanne)
        graph_norm = (grad.get(r["artikel_id"], 0.0) / g_max) if g_max else 0.0
        return 0.75 * rang_norm + 0.25 * graph_norm

    aus.sort(key=_score, reverse=True)
    seite = aus[offset:offset + grenze]

    # Zugehoerigkeits-Chips fuer die sichtbaren Treffer -- eine Anfrage statt
    # N, damit eine Trefferseite kein N+1-Problem wird.
    zeigen = [r["artikel_id"] for r in seite]
    gehoert_je = {}
    sphaeren_je = {}
    if zeigen:
        ph = ",".join("?" * len(zeigen))
        for row in db.db.execute(
            f"SELECT artikel_id, gehoert, sicherheit FROM entityos_artikel_zuordnung "
            f"WHERE artikel_id IN ({ph})", zeigen).fetchall():
            gehoert_je[row["artikel_id"]] = {"wer": row["gehoert"], "sicherheit": row["sicherheit"]}
        for row in db.db.execute(
            f"SELECT artikel_id, sphaere FROM artikel_sphaere WHERE artikel_id IN ({ph})",
            zeigen).fetchall():
            sphaeren_je.setdefault(row["artikel_id"], []).append(row["sphaere"])

    def _ausriss(text, breite=260):
        text = text or ""
        low = text.lower()
        pos = -1
        for w in worte:
            pos = low.find(w)
            if pos >= 0:
                break
        if pos < 0:
            ausschnitt, start = text[:breite], 0
        else:
            start = max(0, pos - breite // 3)
            ausschnitt = text[start:start + breite]
        # Fundstellen markieren (Klartext-Marker <mark>, das Frontend rendert es).
        def _mark(m):
            return f"<mark>{m.group(0)}</mark>"
        muster = re.compile("|".join(re.escape(w) for w in worte), re.IGNORECASE)
        ausschnitt = muster.sub(_mark, ausschnitt)
        praefix = "…" if start > 0 else ""
        suffix = "…" if start + breite < len(text) else ""
        return praefix + ausschnitt + suffix

    treffer = []
    for r in seite:
        aid = r["artikel_id"]
        treffer.append({
            "id": aid, "titel": r["titel"], "art": r["art"], "projekt": r["projekt"],
            "status": r["status"], "epistemic_class": r["epistemic_class"],
            "erzeugt_am": r["erzeugt_am"], "konfidenz": r["konfidenz"],
            "ausriss": _ausriss(r["text"]),
            "gehoert": gehoert_je.get(aid), "sphaeren": sphaeren_je.get(aid, []),
            "graph_gewicht": round(grad.get(aid, 0.0), 3),
        })

    return {
        "frage": frage, "worte": worte, "treffer": treffer,
        "gesamt": len(aus), "offset": offset, "limit": grenze,
        "hinweis": "Ausschnitte aus dem echten Volltext, Rangfolge = bm25 + Graph-Naehe aus vp_weg.",
    }


# ── Ein Artikel, ganz: Infobox, Hypothesen, Implikationen, Dateien ─────

# Nur unter diesen Wurzeln liest der Bilderzug wirklich eine Datei -- beide
# sind im Behaelter read-only gemountet (compose.yaml). Ein `quelle`-Pfad,
# der woanders hinzeigt (z.B. in einen fremden Rechner-Pfad auf Gabriels
# eigenem PC), bleibt eine sichtbare TEXT-Angabe, wird aber NIE geoeffnet --
# derselbe Konstruktionsschutz wie bei _avatar_dateien in terminal_gateway.py.
BILD_ERLAUBTE_WURZELN = ("/var/lib/agentforge/projects", "/var/lib/clay")
_BILD_ENDUNGEN = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")


def bildpfad_falls_erlaubt(quelle: str | None) -> Path | None:
    if not quelle or not str(quelle).lower().endswith(_BILD_ENDUNGEN):
        return None
    try:
        p = Path(quelle).resolve()
    except Exception:
        return None
    if not any(str(p).startswith(w) for w in BILD_ERLAUBTE_WURZELN):
        return None
    return p


def _offene_fragen(roh: str | None) -> list[dict]:
    if not roh:
        return []
    try:
        werte = json.loads(roh)
    except Exception:
        return []
    return werte if isinstance(werte, list) else []


def _hypothese_aus_metadaten(art: str, metadaten: dict) -> dict | None:
    """Eigene Hypothese/Gegenhypothese eines art='hypothese'/'gegenhypothese'-
    Artikels -- die Felder liegen strukturiert in `metadaten` (claim_id,
    proposition, first_status, domains, ...), siehe mcp_server-Beispiele."""
    if art not in ("hypothese", "gegenhypothese"):
        return None
    if not isinstance(metadaten, dict):
        return None
    prop = metadaten.get("proposition")
    if not prop:
        return None
    return {
        "claim_id": metadaten.get("claim_id"),
        "art": art,
        "proposition": prop,
        "status": metadaten.get("first_status"),
        "scope": metadaten.get("scope"),
        "domains": metadaten.get("domains") or [],
        "experiment_ref": metadaten.get("experiment_ref"),
    }


def artikel_lesen(db, artikel_id: str) -> dict:
    aid = str(artikel_id or "").strip()
    if not aid:
        return {"fehler": "keine Artikelkennung"}
    r = db.db.execute(
        "SELECT a.id, a.titel, a.art, a.quelle, a.datum, a.herkunft, a.metadaten, "
        "a.offene_fragen, a.status, a.epistemic_class, a.tags, a.konfidenz, "
        "a.projekt, a.projekt_art, a.erzeugt_am, s.text "
        "FROM artikel a LEFT JOIN artikel_suchtext s ON s.artikel_id = a.id "
        "WHERE a.id = ?", (aid,)).fetchone()
    if r is None:
        return {"id": aid, "nicht_gefunden": True,
                "hinweis": "kein Artikel mit dieser Kennung"}

    try:
        metadaten = json.loads(r["metadaten"] or "{}")
        if not isinstance(metadaten, dict):
            metadaten = {}
    except Exception:
        metadaten = {}

    text = r["text"] or metadaten.get("text") or metadaten.get("inhalt") or ""

    sphaeren = [x["sphaere"] for x in db.db.execute(
        "SELECT sphaere FROM artikel_sphaere WHERE artikel_id=?", (aid,)).fetchall()]
    zuordnung = db.db.execute(
        "SELECT gehoert, grund, sicherheit FROM entityos_artikel_zuordnung WHERE artikel_id=?",
        (aid,)).fetchone()
    projekte = _lesen_tolerant(
        db, "SELECT p.id, p.name, p.art, p.eltern_id, m.konfidenz FROM om_projekt_mitglied m "
        "JOIN om_projekt p ON p.id = m.projekt_id WHERE m.artikel_id=?", (aid,))

    # ── Hypothesen-Box ──────────────────────────────────────────────────
    # 1) ist der Artikel SELBST eine Hypothese/Gegenhypothese -> ihre eigene
    #    Proposition. 2) `offene_fragen` -- das ist das echte Feld dafuer,
    #    auch wenn viele Eintraege dort nur mechanische Qualitaetsnotizen
    #    sind ("kein Titelfeld gefunden") statt inhaltlicher Fragen; beides
    #    wird gezeigt, nichts wird stillschweigend weggefiltert.
    # 3) verwandte Hypothesen-Artikel ueber vp_weg (art in hypothese/gegenhyp.).
    eigene_hyp = _hypothese_aus_metadaten(r["art"], metadaten)
    offene_fragen = _offene_fragen(r["offene_fragen"])
    verwandte_hyp = db.db.execute(
        "SELECT v.nach AS id, a2.titel, a2.art, v.guete FROM vp_weg v "
        "JOIN artikel a2 ON a2.id = v.nach WHERE v.von=? AND a2.art IN ('hypothese','gegenhypothese') "
        "UNION "
        "SELECT v.von AS id, a2.titel, a2.art, v.guete FROM vp_weg v "
        "JOIN artikel a2 ON a2.id = v.von WHERE v.nach=? AND a2.art IN ('hypothese','gegenhypothese') "
        "ORDER BY guete DESC LIMIT 8", (aid, aid)).fetchall()
    hat_hypothesen = bool(eigene_hyp) or bool(verwandte_hyp)

    implikationen = _lesen_tolerant(
        db, "SELECT hypothese_id, hypothese_text, text, konfidenz, modell, erzeugt_am "
        "FROM om_hypothese_implikation WHERE artikel_id=? ORDER BY konfidenz DESC", (aid,))

    zsf = _lesen_tolerant(
        db, "SELECT text, modell, erzeugt_am FROM om_zusammenfassung WHERE artikel_id=?", (aid,), viele=False)
    skizze = _lesen_tolerant(
        db, "SELECT mermaid, quelle, erzeugt_am FROM om_skizze WHERE artikel_id=?", (aid,), viele=False)

    bildpfad = bildpfad_falls_erlaubt(r["quelle"])

    return {
        "id": r["id"], "titel": r["titel"], "art": r["art"], "text": text,
        "zeichen": len(text),
        "infobox": {
            "art": r["art"], "quelle": r["quelle"], "datum": r["datum"],
            "herkunft": r["herkunft"], "status": r["status"],
            "epistemic_class": r["epistemic_class"],
            "tags": [t.strip() for t in (r["tags"] or "").split(",") if t.strip()],
            "konfidenz": r["konfidenz"], "erzeugt_am": r["erzeugt_am"],
            "sphaeren": sphaeren,
            "gehoert": dict(zuordnung) if zuordnung else None,
            "projekte": [dict(p) for p in projekte],
            "metadaten": metadaten,
        },
        "hypothesen": {
            "vorhanden": hat_hypothesen,
            "eigene": eigene_hyp,
            "offene_fragen": offene_fragen,
            "verwandte_hypothesen": [dict(h) for h in verwandte_hyp],
            "hinweis": (None if hat_hypothesen else "keine Hypothesen erfasst"),
        },
        "implikationen": {
            "eintraege": [dict(i) for i in implikationen],
            "hinweis": ("abgeleitet vom Anreicherungsdienst aus den echten Hypothesen dieses "
                        "Eintrags -- generiert, keine gemessene Tatsache" if implikationen
                        else ("keine Implikationen -- dieser Eintrag traegt keine Hypothese, "
                              "aus der etwas abgeleitet werden koennte" if not hat_hypothesen
                              else "noch keine Implikationen erzeugt")),
        },
        "bild": ({"quelle": r["quelle"], "pfad": str(bildpfad),
                  "url": f"/api/omnimind/bild/{aid}"} if bildpfad else None),
        "zusammenfassung": (dict(zsf) | {"generiert": True} if zsf else None),
        "skizze": (dict(skizze) if skizze else None),
        "hinweis": ("Der volle Artikeltext. Steht hier nichts, ist der Artikel ein reiner "
                    "Zeiger -- z.B. auf eine Datei." if not text else None),
    }


# ── Verwandte Artikel (vp_weg) ──────────────────────────────────────────

def verwandte(db, artikel_id: str, limit: int = 12) -> dict:
    aid = str(artikel_id or "").strip()
    grenze = max(1, min(int(limit), 40))
    zeilen = db.db.execute(
        "SELECT v.nach AS id, a2.titel, a2.art, a2.projekt, v.art AS kantenart, "
        "v.guete, v.tunnel, 'raus' AS richtung FROM vp_weg v "
        "JOIN artikel a2 ON a2.id = v.nach WHERE v.von=? "
        "UNION ALL "
        "SELECT v.von AS id, a2.titel, a2.art, a2.projekt, v.art AS kantenart, "
        "v.guete, v.tunnel, 'rein' AS richtung FROM vp_weg v "
        "JOIN artikel a2 ON a2.id = v.von WHERE v.nach=? "
        "ORDER BY guete DESC LIMIT ?", (aid, aid, grenze)).fetchall()
    return {"id": aid, "verwandte": [dict(z) for z in zeilen], "anzahl": len(zeilen),
            "hinweis": "Kanten aus vp_weg, dem gelernten Abrufgraphen -- guete 0..1, "
                       "tunnel markiert eine ungewoehnliche, weite Verbindung."}


# ── Das Wissensnetz -- fuer den Filter-Seiteneffekt UND den eigenen Graph-Modus
#
# ⭐ 18.456 Artikel auf einmal sind kein Bild, sondern ein Wollknaeuel. Diese
# Funktion liefert deshalb IMMER eine begrenzte, ehrlich gekennzeichnete
# Teilmenge: entweder die gefilterte Menge (Querverbindungsnetz) oder die
# Nachbarschaft eines Mittelpunkts (Graph-Modus, Level-of-Detail). Ein
# `abgeschnitten`-Feld sagt, wenn mehr da waere, als gezeigt wird -- NIE so
# tun, als sei das ganze Netz auf dem Bildschirm.

_NETZ_KNOTEN_DECKEL = 160


def _knoten_anreichern(db, ids: list[str]) -> dict[str, dict]:
    if not ids:
        return {}
    ph = ",".join("?" * len(ids))
    basis = {r["id"]: dict(r) for r in db.db.execute(
        f"SELECT a.id, a.titel, a.art, a.projekt, a.quelle, substr(s.text,1,180) AS ausriss "
        f"FROM artikel a LEFT JOIN artikel_suchtext s ON s.artikel_id=a.id "
        f"WHERE a.id IN ({ph})", ids).fetchall()}
    for r in db.db.execute(
        f"SELECT artikel_id, sphaere FROM artikel_sphaere WHERE artikel_id IN ({ph})", ids).fetchall():
        basis.setdefault(r["artikel_id"], {}).setdefault("sphaeren", []).append(r["sphaere"])
    for r in db.db.execute(
        f"SELECT artikel_id, gehoert FROM entityos_artikel_zuordnung WHERE artikel_id IN ({ph})",
        ids).fetchall():
        basis.setdefault(r["artikel_id"], {})["gehoert"] = r["gehoert"]
    knoten = {}
    for aid, r in basis.items():
        bild = bildpfad_falls_erlaubt(r.get("quelle"))
        knoten[aid] = {
            "id": aid, "titel": r.get("titel") or aid, "art": r.get("art"),
            "projekt": r.get("projekt"), "sphaeren": r.get("sphaeren", []),
            "gehoert": r.get("gehoert"), "ausriss": r.get("ausriss") or "",
            "bild_url": (f"/api/omnimind/bild/{aid}" if bild else None),
        }
    return knoten


def netz(db, *, gehoert: str | None = None, sphaere: str | None = None,
          projekt_id: str | None = None, art: str | None = None,
          mittelpunkt: str | None = None, limit_knoten: int = 80) -> dict:
    grenze = max(4, min(int(limit_knoten), _NETZ_KNOTEN_DECKEL))

    if mittelpunkt:
        # Graph-Modus: von einem Knoten aus in die Breite, staerkste Kanten
        # zuerst -- eine gierige BFS ueber guete, kein Zufallsschnitt.
        gesehen = {mittelpunkt}
        rand = [mittelpunkt]
        kanten = []
        while rand and len(gesehen) < grenze:
            ph = ",".join("?" * len(rand))
            zeilen = db.db.execute(
                f"SELECT von, nach, art, guete, tunnel FROM vp_weg "
                f"WHERE von IN ({ph}) OR nach IN ({ph}) ORDER BY guete DESC LIMIT ?",
                (*rand, *rand, grenze * 3)).fetchall()
            naechster_rand = []
            for z in zeilen:
                kanten.append(dict(z))
                for ende in (z["von"], z["nach"]):
                    if ende not in gesehen and len(gesehen) < grenze:
                        gesehen.add(ende)
                        naechster_rand.append(ende)
            if not naechster_rand:
                break
            rand = naechster_rand
        ids = list(gesehen)
        knoten = _knoten_anreichern(db, ids)
        # Randkanten (zu Knoten ausserhalb der gezeigten Menge) zaehlen wir,
        # zeigen sie aber nicht -- das ist die ehrliche Abkuerzung.
        gesamt_kanten = db.db.execute(
            "SELECT COUNT(*) n FROM vp_weg WHERE von IN (%s) OR nach IN (%s)" %
            (",".join("?" * len(ids)), ",".join("?" * len(ids))), (*ids, *ids)).fetchone()["n"]
        eigene_kanten = [k for k in kanten if k["von"] in gesehen and k["nach"] in gesehen]
        return {
            "modus": "nachbarschaft", "mittelpunkt": mittelpunkt,
            "knoten": list(knoten.values()), "kanten": eigene_kanten,
            "abgeschnitten": gesamt_kanten > len(eigene_kanten) or len(ids) >= grenze,
            "hinweis": (f"Nachbarschaft von '{mittelpunkt}', staerkste Kanten zuerst "
                        f"({len(knoten)} von moeglicherweise mehr Knoten gezeigt -- Zoom/Klick "
                        f"oeffnet weiter)."),
        }

    # Querverbindungsnetz einer gefilterten Menge.
    bedingungen, parameter = [], []
    if gehoert:
        bedingungen.append("a.id IN (SELECT artikel_id FROM entityos_artikel_zuordnung WHERE gehoert=?)")
        parameter.append(gehoert)
    if sphaere:
        bedingungen.append("a.id IN (SELECT artikel_id FROM artikel_sphaere WHERE sphaere=?)")
        parameter.append(sphaere)
    if art:
        bedingungen.append("a.art = ?")
        parameter.append(art)
    if projekt_id:
        nachkommen = _projekt_nachkommen(db, projekt_id)
        ph2 = ",".join("?" * len(nachkommen))
        bedingungen.append(
            f"a.id IN (SELECT artikel_id FROM om_projekt_mitglied WHERE projekt_id IN ({ph2}))")
        parameter.extend(nachkommen)
    if not bedingungen:
        return {"modus": "gefiltert", "knoten": [], "kanten": [], "abgeschnitten": False,
                "hinweis": "kein Filter gesetzt -- das volle Netz waere ein Wollknaeuel, "
                           "erst filtern"}

    where = " AND ".join(bedingungen)
    gesamt = db.db.execute(f"SELECT COUNT(*) n FROM artikel a WHERE {where}", parameter).fetchone()["n"]
    ids = [r["id"] for r in db.db.execute(
        f"SELECT a.id FROM artikel a WHERE {where} "
        f"ORDER BY (SELECT COUNT(*) FROM vp_weg v WHERE v.von=a.id OR v.nach=a.id) DESC "
        f"LIMIT ?", (*parameter, grenze)).fetchall()]
    knoten = _knoten_anreichern(db, ids)
    ph = ",".join("?" * len(ids)) if ids else "''"
    primaer = db.db.execute(
        f"SELECT von, nach, art, guete, tunnel FROM vp_weg "
        f"WHERE von IN ({ph}) AND nach IN ({ph}) ORDER BY guete DESC", (*ids, *ids)).fetchall() if ids else []
    # Ein paar Kontextkanten nach aussen, gedaempft -- zeigt, dass die
    # gefilterte Menge nicht isoliert ist, ohne das ganze Netz zu laden.
    kontext = db.db.execute(
        f"SELECT von, nach, art, guete, tunnel FROM vp_weg "
        f"WHERE (von IN ({ph}) AND nach NOT IN ({ph})) OR (nach IN ({ph}) AND von NOT IN ({ph})) "
        f"ORDER BY guete DESC LIMIT 30", (*ids, *ids, *ids, *ids)).fetchall() if ids else []
    kontext_ids = {k["von"] for k in kontext} | {k["nach"] for k in kontext}
    kontext_ids -= set(ids)
    kontext_knoten = _knoten_anreichern(db, list(kontext_ids))
    for k in kontext_knoten.values():
        k["kontext"] = True

    return {
        "modus": "gefiltert", "gesamt_treffer": gesamt,
        "knoten": list(knoten.values()) + list(kontext_knoten.values()),
        "kanten": [dict(k) | {"kontext": False} for k in primaer]
                  + [dict(k) | {"kontext": True} for k in kontext],
        "abgeschnitten": gesamt > len(ids),
        "hinweis": (f"{len(ids)} von {gesamt} gefilterten Artikeln gezeigt (nach Grad in vp_weg "
                    f"sortiert), plus {len(kontext_knoten)} Nachbarn zur Einordnung." if gesamt > len(ids)
                    else f"alle {len(ids)} gefilterten Artikel gezeigt."),
    }


# ── Projekt-Hierarchie -- lesend, gefuellt vom Anreicherungsdienst ─────

def projekt_hierarchie(db) -> dict:
    zeilen = _lesen_tolerant(
        db, "SELECT id, name, art, eltern_id, konfidenz, begruendung, anzahl_artikel, aktualisiert_am "
        "FROM om_projekt ORDER BY anzahl_artikel DESC")
    knoten = {r["id"]: dict(r) | {"kinder": []} for r in zeilen}
    wurzeln = []
    for r in knoten.values():
        eltern = r.get("eltern_id")
        if eltern and eltern in knoten:
            knoten[eltern]["kinder"].append(r)
        else:
            wurzeln.append(r)
    kanten = [dict(r) for r in _lesen_tolerant(
        db, "SELECT a_id, b_id, staerke, beleg FROM om_projekt_kante ORDER BY staerke DESC")]
    return {"projekte": wurzeln, "anzahl": len(knoten), "querverbindungen": kanten,
            "hinweis": ("leer, solange der Anreicherungsdienst noch nicht gelaufen ist"
                        if not knoten else None)}


def filter_werte(db) -> dict:
    """Was die Filter-Chips im Frontend anbieten -- gemessen, nicht geraten."""
    gehoert = [dict(r) for r in db.db.execute(
        "SELECT gehoert AS wert, COUNT(*) n FROM entityos_artikel_zuordnung "
        "GROUP BY gehoert ORDER BY n DESC").fetchall()]
    sphaeren = [dict(r) for r in db.db.execute(
        "SELECT sphaere AS wert, COUNT(*) n FROM artikel_sphaere GROUP BY sphaere "
        "ORDER BY n DESC").fetchall()]
    arten = [dict(r) for r in db.db.execute(
        "SELECT art AS wert, COUNT(*) n FROM artikel GROUP BY art ORDER BY n DESC LIMIT 40").fetchall()]
    return {"gehoert": gehoert, "sphaeren": sphaeren, "arten": arten}


# ── FastAPI-Wege ─────────────────────────────────────────────────────────
#
# Gleicher Zusammenbau wie registriere_postfach_wege: die Clerk-Einzelheiten
# bleiben im Gateway, hier kommt nur `pruefe_zugriff(request) -> user_id`
# (wirft PermissionError/AuthenticationError) und `antwort_auf_fehler`.
# Additiv -- diese Funktion wird aus terminal_gateway.py mit EINEM Aufruf
# eingehaengt, nichts hier fasst die bestehenden Wege an.

def registriere_omnimind_wege(app, *, db, pruefe_zugriff, antwort_auf_fehler) -> None:
    # ⚠️ BEWUSST KEIN sicherstellen(db) hier: registriere_omnimind_wege laeuft
    # waehrend create_terminal_app() -- also fuer JEDEN Test, der eine App
    # baut, auch fuer einen Platzhalter wie db=object() (siehe
    # test_terminal_ws_auth_*.py, die mit Terminal-Auth nichts mit OmniMind
    # zu tun haben). db.db waere dort nicht vorhanden. Die om_*-Tabellen legt
    # der Anreicherungsdienst an; alle Lesezugriffe unten gehen ueber
    # _lesen_tolerant() und vertragen eine DB ganz ohne diese Tabellen.

    async def _sperre(request: Request) -> None:
        await pruefe_zugriff(request)

    @app.get("/api/omnimind/suche")
    async def omnimind_suche(request: Request):
        try:
            await _sperre(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)
        q = request.query_params
        ergebnis = await asyncio.to_thread(
            suche, db, q.get("q", ""),
            gehoert=q.get("gehoert") or None, sphaere=q.get("sphaere") or None,
            art=q.get("art") or None, projekt_id=q.get("projekt") or None,
            seit=q.get("seit") or None, bis=q.get("bis") or None,
            hat_dateien=(q.get("hat_dateien") == "1"), hat_bilder=(q.get("hat_bilder") == "1"),
            limit=int(q.get("limit", 20) or 20), offset=int(q.get("offset", 0) or 0),
        )
        return JSONResponse(ergebnis)

    @app.get("/api/omnimind/artikel/{artikel_id}")
    async def omnimind_artikel(artikel_id: str, request: Request):
        try:
            await _sperre(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)
        return JSONResponse(await asyncio.to_thread(artikel_lesen, db, artikel_id))

    @app.get("/api/omnimind/artikel/{artikel_id}/verwandte")
    async def omnimind_verwandte(artikel_id: str, request: Request):
        try:
            await _sperre(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)
        limit = int(request.query_params.get("limit", 12) or 12)
        return JSONResponse(await asyncio.to_thread(verwandte, db, artikel_id, limit))

    @app.get("/api/omnimind/bild/{artikel_id}")
    async def omnimind_bild(artikel_id: str, request: Request):
        # Derselbe Bauplan wie /api/avatar/{wer}: der Pfad kommt NIE aus der
        # Anfrage, sondern ausschliesslich aus der DB-Zeile zu dieser
        # Artikelkennung, und nur, wenn er unter einer erlaubten Wurzel liegt.
        try:
            await _sperre(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)
        r = db.db.execute("SELECT quelle FROM artikel WHERE id=?", (artikel_id,)).fetchone()
        pfad = bildpfad_falls_erlaubt(r["quelle"]) if r else None
        if pfad is None or not pfad.is_file():
            return JSONResponse({"error": "kein_bild"}, status_code=404)
        try:
            daten = await asyncio.to_thread(pfad.read_bytes)
        except OSError:
            return JSONResponse({"error": "nicht_lesbar"}, status_code=404)
        endung = pfad.suffix.lower().lstrip(".")
        typ = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
               "gif": "image/gif", "svg": "image/svg+xml", "webp": "image/webp"}.get(endung, "application/octet-stream")
        return Response(content=daten, media_type=typ, headers={"Cache-Control": "no-cache"})

    @app.get("/api/omnimind/netz")
    async def omnimind_netz(request: Request):
        try:
            await _sperre(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)
        q = request.query_params
        ergebnis = await asyncio.to_thread(
            netz, db, gehoert=q.get("gehoert") or None, sphaere=q.get("sphaere") or None,
            projekt_id=q.get("projekt") or None, art=q.get("art") or None,
            mittelpunkt=q.get("mittelpunkt") or None,
            limit_knoten=int(q.get("limit", 80) or 80),
        )
        return JSONResponse(ergebnis)

    @app.get("/api/omnimind/projekte")
    async def omnimind_projekte(request: Request):
        try:
            await _sperre(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)
        return JSONResponse(await asyncio.to_thread(projekt_hierarchie, db))

    @app.get("/api/omnimind/filter")
    async def omnimind_filter(request: Request):
        try:
            await _sperre(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)
        return JSONResponse(await asyncio.to_thread(filter_werte, db))
