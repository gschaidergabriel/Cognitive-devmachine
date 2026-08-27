#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""weltmodell.py — Weltmodell auf Basis von Hyperposition.

Grundlage sind die im Wiki belegten GESETZE (stabil) und die
Architektur-Kandidaten H1..H6 (Status OPEN, also NICHT entschieden).

GESETZE (im Wiki nachgelesen, nicht erfunden):
  G1  gleichzeitig gueltige Alternativen bleiben erhalten, ohne destruktiven
      Kollaps.  Beleg: C-CURRENT-001 (Status CURRENT, aber scope
      "RAE-8.8/G3 sandbox" = synthetische Grenze) und
      KMP-CLAY-HYPERPOSITION-SEMANTICS (MEASURED_RESULT_SUMMARY, konf 0.9,
      claim_status_hint CURRENT_WITH_SYNTHETIC_BOUNDARY).
  G2  "one semantic relation != one propagation edge != one invalidation edge
      != one process link != one authority path".  Beleg: TP-HYP-H5-CGMT,
      Feld core_laws.  Topologien sind GETRENNT.
  G3  UNKNOWN dependency closure broadens/escalates.  Beleg: TP-HYP-H5-CGMT
      core_laws und H5 FINAL_REPORT Abschnitt T3
      (KNOWN_VALID | KNOWN_INVALID | UNKNOWN).
  G4  higher-order identity may remain persistent while active coupling is
      sparse and contextual.  Beleg: TP-HYP-H5-CGMT core_laws.
  G5  fact/observation/activation/proposal/form/authority/effect sind
      NICHT austauschbare Ausfalldomaenen; "visible tags alone are not a
      trusted boundary".  Beleg: hyperposition-h4-clay-semantic-firebreaks.
  G6  "causal credit is a distinct topology", "recoverable topology is not
      harmless topology", "atomic switch is not cognitive validation",
      "effect expressibility is not effect authority".  Beleg:
      hyperposition-h6-causal-attribution-reversible-topology.

OFFENE KANDIDATEN — jede Zeile, die darauf ruht, traegt offen=1:
  H1 hyperposition-h1-monotonicity-gated-runtime          Status OPEN
  H2 hyperposition-h2-three-topology-scoped-delta         Status OPEN
  H3 hyperposition-h3-epoch-pinned-adaptive-topology      Status OPEN
     (liefert den TopologyBasis-Zeugen = unser basis_json)
  H4 hyperposition-h4-clay-semantic-firebreaks            Status OPEN
     (liefert das Cast-Gitter der Feuerschneisen)
  H5 TP-HYP-H5-CGMT                                       Status OPEN
     (liefert T1..T6 und das kontext-gesteuerte Auflesen)
  H6 hyperposition-h6-...-reversible-topology             Status OPEN
     (liefert T7 CAUSAL_CREDIT)
  KMP-G11-IDENTITY-AXES                                   OPEN_REFINEMENT
     (Identitaetsachse muss deklariert werden)

Die Tabellen wm_* stehen NEBEN `artikel`. `artikel` wird nicht angefasst,
nicht migriert, nicht umgeschrieben. Der alte Weg bleibt unveraendert.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

DB = os.environ.get("WM_DB", "/var/lib/clay/wiki.db")
BUSY_MS = 30000
VERSUCHE = 8


# ---------------------------------------------------------------- Verbindung

def jetzt():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def verbinden(schreibend=True):
    if schreibend:
        c = sqlite3.connect(DB, timeout=BUSY_MS / 1000.0)
    else:
        c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True,
                            timeout=BUSY_MS / 1000.0)
    c.execute("PRAGMA busy_timeout=%d" % BUSY_MS)
    c.row_factory = sqlite3.Row
    return c


def mit_wiederholung(fn, *a, **kw):
    """Viele Schreiber auf derselben WAL-Datei -> zurueckweichen und erneut."""
    letzte = None
    for i in range(VERSUCHE):
        try:
            return fn(*a, **kw)
        except sqlite3.OperationalError as e:
            if "locked" not in str(e) and "busy" not in str(e):
                raise
            letzte = e
            time.sleep(0.25 * (2 ** i))
    raise letzte


# ------------------------------------------------------------------ Konstanten

# Die sieben Ausfalldomaenen aus H4 (GESETZ 5). Namen wie im FINAL_REPORT.
DOMAENEN = ["FACT_EXACT", "OBSERVATION", "ACTIVATION_PRIOR", "PROPOSAL",
            "FORM", "AUTHORITY_CAP", "EFFECT_INTENT"]

# Die sieben Topologien. T1..T6 aus H5 FINAL_REPORT, T7 aus H6.
# Zuordnung Hausname -> H5/H6-Nummer:
TOPOLOGIEN = {
    "T_SEMANTIK":     ("T1", "Semantic relation topology (H5)"),
    "T_AUSBREITUNG":  ("T2", "Active propagation topology (H5)"),
    "T_ENTWERTUNG":   ("T3", "Dependency/invalidation topology (H5)"),
    "T_PROZESS":      ("T4", "Selection/workspace topology (H5)"),
    "T_ORT":          ("T5", "Physical topology (H5)"),
    "T_AUTORITAET":   ("T6", "Authority topology (H5)"),
    "T_KAUSALKREDIT": ("T7", "CAUSAL_CREDIT ITEM|PATH|ASSEMBLY|ROUTE|UNKNOWN (H6)"),
    "T_UNBESTIMMT":   ("--", "Zuordnung unbekannt -> verbreitert (GESETZ 3)"),
}

# Cast-Gitter aus H4 FINAL_REPORT Abschnitt 5.B, woertlich uebernommen.
# erlaubt: 0 = verboten, 1 = erlaubt unter Bedingung.
# Alles was hier NICHT steht, wird abgelehnt. Ablehnung ist der Normalfall.
CAST_REGELN = [
    # von,              nach,             erlaubt, bedingung,                            beleg
    ("ACTIVATION_PRIOR", "FACT_EXACT", 1, "exakt_anker_pruefung",
     "H4 5.B: 'ACTIVATION_PRIOR -> FACT_EXACT  exact-anchor validation required'"),
    ("OBSERVATION", "FACT_EXACT", 1, "herkunft_und_pruefpolitik",
     "H4 5.B: 'OBSERVATION -> FACT_EXACT  provenance + validation policy required'"),
    ("PROPOSAL", "EFFECT_INTENT", 1, "geschlossenheit_und_faehigkeit",
     "H4 5.B: 'PROPOSAL -> EFFECT_INTENT  compositional closure + current capability required'"),
    ("FORM", "EFFECT_INTENT", 1, "vertrauter_uebersetzer",
     "H4 5.B: 'FORM -> executable/materialized state  trusted compiler/runtime transition required'"),
    # Ausdrueckliche Verbote (nicht nur Vorgabe-Ablehnung):
    ("FORM", "AUTHORITY_CAP", 0, None, "H4 5.B: 'TEXT/data -> AUTHORITY_CAP  forbidden'"),
    ("PROPOSAL", "AUTHORITY_CAP", 0, None,
     "H4 FINAL_REPORT: 'it cannot silently convert ... PROPOSAL -> AUTHORITY'"),
    ("PROPOSAL", "FACT_EXACT", 0, None,
     "H4 H-HYP4-005 + Hausregel: ein Modellvorschlag wird nie Tatsache ohne Beleg; "
     "der einzige Weg nach FACT_EXACT fuehrt ueber OBSERVATION"),
    ("ACTIVATION_PRIOR", "AUTHORITY_CAP", 0, None,
     "H4: Aktivierung mintet keine Autoritaet (H5 T6: 'never mint authority')"),
    ("OBSERVATION", "AUTHORITY_CAP", 0, None, "H4 5.B: data -> AUTHORITY_CAP forbidden"),
    ("EFFECT_INTENT", "AUTHORITY_CAP", 0, None, "H5 T6: Autoritaet bleibt extern vermittelt"),
]

# kante.art -> Topologien. MEHRFACHZUGEHOERIGKEIT IST DER NORMALFALL (GESETZ 2):
# eine Kante darf zu mehreren Topologien gehoeren, das ist kein Konflikt.
# Die Zuordnung ist aus den DATEN abgeleitet, nicht aus den Namen. Belege je
# Art: verbundene artikel.art, Anteil gleiches Verzeichnis (gl.Verz), ob
# Ketten entstehen (Knoten kommt als von UND nach vor), Symmetrie.
ART_TOPOLOGIE = {
    # --- physische Lage: Anteil gleiches Verzeichnis = 100 %
    "geschwister_verzeichnis": [("T_ORT",
        "12239/12239 im selben Verzeichnis; quelldatei->quelldatei")],
    "geschwister_datei": [("T_ORT",
        "1556/1556 im selben Verzeichnis")],
    "wirt": [("T_ORT",
        "vorfall->wirt, 57/57; benennt die Maschine = Platzierung")],
    # --- Bedeutung
    "gleicher_inhalt": [("T_SEMANTIK",
        "Inhaltsgleichheit; verbindet gleiche artikel.art (hypothese->hypothese 1365)")],
    "related_claim_ids": [("T_SEMANTIK",
        "begriff->hypothese 32/32, 0/32 gleiches Verzeichnis, keine Ketten "
        "-> reine Bedeutungsrelation, keine Lage, keine Abfolge")],
    "topic_packets": [("T_SEMANTIK",
        "->begriff 6/6, 0/6 gleiches Verzeichnis -> Zuordnung zu einem Thema")],
    "sprachpaar": [("T_SEMANTIK",
        "iar_seite->iar_seite 21/21, 0/21 gleiches Verzeichnis -> dieselbe "
        "Aussage in anderer Sprache")],
    "eltern_hypothese": [("T_SEMANTIK",
        "hypothese->hypothese 8/8 Ableitung"), ("T_ORT",
        "8/8 im selben Verzeichnis")],
    # --- Entwertung: Ketten (Knoten als von UND nach) sind die Signatur
    "nachfolge_version": [("T_ENTWERTUNG",
        "1342 Knoten kommen als von UND nach vor = Versionsketten"),
        ("T_SEMANTIK", "Abstammung ist auch eine Bedeutungsrelation")],
    "predecessor_packet_ids": [("T_ENTWERTUNG",
        "begriff->begriff 53/55, 16 Knoten in Ketten - dieselbe Signatur wie "
        "nachfolge_version"), ("T_SEMANTIK", "Abstammung")],
    "widerspricht": [("T_ENTWERTUNG",
        "gegenhypothese->hypothese 20/20")],
    "attacks": [("T_ENTWERTUNG",
        "gegenhypothese->hypothese 20/20, deckungsgleich mit widerspricht")],
    # --- Ausbreitung
    "stuetzt": [("T_AUSBREITUNG",
        "forschungsergebnis->gegenhypothese; Geltung wandert weiter")],
    # --- Kausalkredit (H6 T7): wer hat wozu beigetragen
    "evidence": [("T_KAUSALKREDIT", "Beleg = Zurechnung")],
    "evidence_refs": [("T_KAUSALKREDIT", "Beleg = Zurechnung")],
    "source_refs": [("T_KAUSALKREDIT",
        "begriff->bereich_trigger_runs 144; nur 27/423 gleiches Verzeichnis, "
        "also KEINE Lage, sondern Herkunftszeiger")],
    "experiment_refs": [("T_KAUSALKREDIT",
        "zeigt auf das stuetzende Experiment"), ("T_ORT", "5/5 gleiches Verzeichnis")],
    "experiment_ref": [("T_KAUSALKREDIT",
        "zeigt auf das stuetzende Experiment")],
    "lauf_referenz": [("T_KAUSALKREDIT",
        "bereich_atomic/hypothese -> forschungsergebnis 91/91: welcher Lauf "
        "hat welches Ergebnis erzeugt"), ("T_ORT",
        "89/91 im selben Verzeichnis")],
    # --- Prozess
    "artifacts": [("T_PROZESS",
        "bereich_trigger_runs -> erzeugtes Artefakt = Prozessglied"),
        ("T_KAUSALKREDIT", "was hat der Lauf hervorgebracht")],
    # --- bleibt unbestimmt: Datenlage zu duenn
    "packet_referenz": [("T_UNBESTIMMT",
        "n=3, drei verschiedene Typpaare, kein Muster ableitbar")],
}


def basis(operation, quelle, semantik_epoche=None, aktivierungs_epoche=None,
          rahmen=None):
    """TopologyBasis-Zeuge nach H3 (Kandidat OFFEN).

    H3: "A TopologyBasis witness binds semantic epoch, activation epoch,
    CognitiveFrame and operation/projection semantics for replay and causal
    attribution."  Das Format ist damit ein OFFENER Kandidat, kein Standard.
    """
    return json.dumps({
        "semantik_epoche": semantik_epoche,
        "aktivierungs_epoche": aktivierungs_epoche,
        "rahmen": rahmen,
        "operation": operation,
        "quelle": quelle,
        "basis_kandidat": "H3",
        "basis_offen": 1,
    }, ensure_ascii=False, sort_keys=True)


def kanon(d):
    return json.dumps(d or {}, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def lesart_kennung(artikel_id, achse, wert, kontext, quelle):
    roh = "\x1f".join([artikel_id, achse, str(wert), kanon(kontext), quelle])
    return hashlib.sha1(roh.encode("utf-8")).hexdigest()[:24]


# --------------------------------------------------------------------- Schema

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS wm_lesart (
        lesart_id    TEXT PRIMARY KEY,
        artikel_id   TEXT NOT NULL,
        achse        TEXT NOT NULL,
        wert         TEXT,
        kontext_json TEXT NOT NULL DEFAULT '{}',
        domaene      TEXT NOT NULL DEFAULT 'FACT_EXACT',
        basis_json   TEXT NOT NULL,
        quelle       TEXT NOT NULL,
        konfidenz    REAL,
        erzeugt_am   TEXT NOT NULL,
        gueltig_von  TEXT NOT NULL,
        gueltig_bis  TEXT,
        kandidat     TEXT NOT NULL,
        offen        INTEGER NOT NULL DEFAULT 1,
        offen_grund  TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS wm_lesart_ix1 ON wm_lesart(artikel_id, gueltig_bis)",
    "CREATE INDEX IF NOT EXISTS wm_lesart_ix2 ON wm_lesart(artikel_id, achse, gueltig_bis)",
    "CREATE INDEX IF NOT EXISTS wm_lesart_ix3 ON wm_lesart(achse, gueltig_bis)",

    """CREATE TABLE IF NOT EXISTS wm_topologie (
        von          TEXT NOT NULL,
        nach         TEXT NOT NULL,
        topologie    TEXT NOT NULL,
        herkunft_art TEXT NOT NULL DEFAULT '',
        gewicht      REAL NOT NULL DEFAULT 1.0,
        basis_json   TEXT NOT NULL,
        quelle       TEXT,
        erzeugt_am   TEXT NOT NULL,
        gueltig_von  TEXT NOT NULL,
        gueltig_bis  TEXT,
        kandidat     TEXT NOT NULL,
        offen        INTEGER NOT NULL DEFAULT 1,
        offen_grund  TEXT,
        PRIMARY KEY (von, nach, topologie, herkunft_art)
    )""",
    "CREATE INDEX IF NOT EXISTS wm_topologie_ix1 ON wm_topologie(von, topologie, gueltig_bis)",
    "CREATE INDEX IF NOT EXISTS wm_topologie_ix2 ON wm_topologie(topologie)",
    "CREATE INDEX IF NOT EXISTS wm_topologie_ix3 ON wm_topologie(nach, topologie, gueltig_bis)",

    """CREATE TABLE IF NOT EXISTS wm_cast_regel (
        von_domaene  TEXT NOT NULL,
        nach_domaene TEXT NOT NULL,
        erlaubt      INTEGER NOT NULL,
        bedingung    TEXT,
        beleg        TEXT NOT NULL,
        kandidat     TEXT NOT NULL,
        offen        INTEGER NOT NULL DEFAULT 1,
        erzeugt_am   TEXT NOT NULL,
        PRIMARY KEY (von_domaene, nach_domaene)
    )""",

    """CREATE TABLE IF NOT EXISTS wm_guss_log (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit         TEXT NOT NULL,
        von_domaene  TEXT NOT NULL,
        nach_domaene TEXT NOT NULL,
        ergebnis     TEXT NOT NULL,
        grund        TEXT NOT NULL,
        bedingung    TEXT,
        beleg        TEXT,
        gegenstand   TEXT,
        kandidat     TEXT NOT NULL,
        offen        INTEGER NOT NULL DEFAULT 1
    )""",
    "CREATE INDEX IF NOT EXISTS wm_guss_log_ix1 ON wm_guss_log(ergebnis, zeit)",

    """CREATE TABLE IF NOT EXISTS wm_topologie_name (
        topologie  TEXT PRIMARY KEY,
        h_nummer   TEXT NOT NULL,
        bedeutung  TEXT NOT NULL,
        kandidat   TEXT NOT NULL,
        offen      INTEGER NOT NULL DEFAULT 1
    )""",
]


def cmd_init(args):
    c = verbinden()
    def tun():
        with c:
            for s in SCHEMA:
                c.execute(s)
            n = jetzt()
            for t, (hn, bed) in TOPOLOGIEN.items():
                kand = "H6" if t == "T_KAUSALKREDIT" else ("gesetz:G3" if t == "T_UNBESTIMMT" else "H5")
                c.execute("""INSERT INTO wm_topologie_name
                             (topologie,h_nummer,bedeutung,kandidat,offen)
                             VALUES (?,?,?,?,?)
                             ON CONFLICT(topologie) DO UPDATE SET
                               h_nummer=excluded.h_nummer,
                               bedeutung=excluded.bedeutung,
                               kandidat=excluded.kandidat,
                               offen=excluded.offen""",
                          (t, hn, bed, kand, 0 if t == "T_UNBESTIMMT" else 1))
            for vd, nd, erl, bedg, beleg in CAST_REGELN:
                c.execute("""INSERT INTO wm_cast_regel
                             (von_domaene,nach_domaene,erlaubt,bedingung,beleg,
                              kandidat,offen,erzeugt_am)
                             VALUES (?,?,?,?,?,?,?,?)
                             ON CONFLICT(von_domaene,nach_domaene) DO UPDATE SET
                               erlaubt=excluded.erlaubt,
                               bedingung=excluded.bedingung,
                               beleg=excluded.beleg,
                               kandidat=excluded.kandidat,
                               offen=excluded.offen,
                               erzeugt_am=excluded.erzeugt_am""",
                          (vd, nd, erl, bedg, beleg, "H4", 1, n))
    mit_wiederholung(tun)
    print("wm_* angelegt. Cast-Regeln: %d. Topologien: %d." %
          (len(CAST_REGELN), len(TOPOLOGIEN)))
    print("ALLE Cast-Regeln ruhen auf H4 (Status OPEN) -> offen=1.")


# ---------------------------------------------------------- 3. Feuerschneisen

class GussVerweigert(Exception):
    pass


# Arten, die nach der datengestuetzten Zuordnung Beleg tragen (T_KAUSALKREDIT
# oder T_AUSBREITUNG). Nur diese zaehlen als Nachweis.
BELEG_ARTEN = ("evidence", "evidence_refs", "stuetzt")


def beleg_pruefen(c, artikel_id):
    """Mechanische Pruefung: gibt es zu diesem Artikel eine Beleg-Kante auf
    einen Artikel, der WIRKLICH EXISTIERT?  Kein Aufrufer kann das behaupten.

    H4: "Runtime/compiler-enforced transitions, not textual conventions".
    """
    if not artikel_id:
        return False, "kein Gegenstand angegeben — nicht pruefbar, also abgelehnt"
    fragen = ",".join("?" * len(BELEG_ARTEN))
    raus = c.execute(
        "SELECT COUNT(*) FROM kante k WHERE k.von=? AND k.art IN (%s) "
        "AND EXISTS(SELECT 1 FROM artikel a WHERE a.id=k.nach)" % fragen,
        (artikel_id,) + BELEG_ARTEN).fetchone()[0]
    rein = c.execute(
        "SELECT COUNT(*) FROM kante k WHERE k.nach=? AND k.art IN (%s) "
        "AND EXISTS(SELECT 1 FROM artikel a WHERE a.id=k.von)" % fragen,
        (artikel_id,) + BELEG_ARTEN).fetchone()[0]
    if raus or rein:
        return True, ("Beleg-Kanten gefunden: %d ausgehend, %d eingehend "
                      "(Arten %s), Gegenstelle existiert"
                      % (raus, rein, "/".join(BELEG_ARTEN)))
    return False, ("keine Beleg-Kante (%s) mit existierender Gegenstelle "
                   "gefunden" % "/".join(BELEG_ARTEN))


# Welche Bedingung laesst sich mechanisch pruefen? Was hier fehlt, wird
# ABGELEHNT — nicht durchgewunken.
PRUEFER = {
    ("OBSERVATION", "FACT_EXACT"): beleg_pruefen,
    ("ACTIVATION_PRIOR", "FACT_EXACT"): beleg_pruefen,
}


def giessen(c, von_domaene, nach_domaene, artikel_id=None,
            gegenstand=None, protokoll=True):
    """GESETZ 5: Guss zwischen Ausfalldomaenen. Ablehnung ist der Normalfall.

    Es gibt KEINEN Parameter, mit dem der Aufrufer die Bedingung behaupten
    kann. Ein Parameter, den der Aufrufer selbst setzt, ist keine Grenze.
    Geprueft wird gegen die Daten oder gar nicht — und "gar nicht" heisst
    ABGELEHNT.
    """
    n = jetzt()
    if von_domaene not in DOMAENEN or nach_domaene not in DOMAENEN:
        erg, grund, bedg, beleg = ("VERWEIGERT",
                                   "unbekannte Domaene — GESETZ 3: unbekannt verbreitert, "
                                   "wird nicht stillschweigend durchgelassen", None, None)
    elif von_domaene == nach_domaene:
        erg, grund, bedg, beleg = ("ERLAUBT", "Identitaet, kein Domaenenwechsel", None, None)
    else:
        r = c.execute("""SELECT erlaubt,bedingung,beleg FROM wm_cast_regel
                         WHERE von_domaene=? AND nach_domaene=?""",
                      (von_domaene, nach_domaene)).fetchone()
        if r is None:
            erg = "VERWEIGERT"
            grund = "keine vertraute Regel eingetragen — Vorgabe ist Ablehnung"
            bedg = beleg = None
        elif r["erlaubt"] == 0:
            erg = "VERWEIGERT"
            grund = "ausdruecklich verboten"
            bedg, beleg = r["bedingung"], r["beleg"]
        else:
            bedg, beleg = r["bedingung"], r["beleg"]
            pruefer = PRUEFER.get((von_domaene, nach_domaene))
            if pruefer is None:
                erg = "VERWEIGERT"
                grund = ("Bedingung '%s' ist nicht mechanisch pruefbar — "
                         "also abgelehnt. Lieber zu viel sperren als nichts."
                         % bedg)
            else:
                ok, warum = pruefer(c, artikel_id)
                erg = "ERLAUBT" if ok else "VERWEIGERT"
                grund = "%s: %s" % (bedg, warum)

    if protokoll:
        def tun():
            with c:
                c.execute("""INSERT INTO wm_guss_log
                             (zeit,von_domaene,nach_domaene,ergebnis,grund,
                              bedingung,beleg,gegenstand,kandidat,offen)
                             VALUES (?,?,?,?,?,?,?,?,?,?)""",
                          (n, von_domaene, nach_domaene, erg, grund, bedg,
                           beleg, gegenstand, "H4", 1))
        mit_wiederholung(tun)

    return {"erlaubt": erg == "ERLAUBT", "ergebnis": erg, "grund": grund,
            "bedingung": bedg, "beleg": beleg,
            "kandidat": "H4", "offen": 1,
            "offen_hinweis": "H4 ist OPEN. Diese Schneise ist ein Kandidat, kein Ergebnis."}


def cmd_giessen(args):
    c = verbinden()
    r = giessen(c, args.von, args.nach, artikel_id=args.artikel_id,
                gegenstand=args.gegenstand)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r["erlaubt"] else 1


# ------------------------------------------- 2. UNBESTIMMT verbreitert (G3)

def nachbarschaft(c, knoten, topologie=None, richtung="beide"):
    """GESETZ 3: eine Kante mit unbestimmter Topologie gehoert POTENZIELL zu
    jeder — nicht zu keiner. Unwissen darf die Welt nicht kleiner machen.

    Liefert getrennt: 'sicher' (Topologie steht fest) und 'moeglich'
    (T_UNBESTIMMT, koennte dazugehoeren).
    """
    wo = {"aus": "von=?", "ein": "nach=?", "beide": "(von=? OR nach=?)"}[richtung]
    par = (knoten,) if richtung != "beide" else (knoten, knoten)
    sicher, moeglich = [], []
    for r in c.execute(
            "SELECT von,nach,topologie,herkunft_art,gewicht FROM wm_topologie "
            "WHERE %s AND gueltig_bis IS NULL" % wo, par):
        anderer = r["nach"] if r["von"] == knoten else r["von"]
        e = {"knoten": anderer, "topologie": r["topologie"],
             "herkunft_art": r["herkunft_art"], "gewicht": r["gewicht"]}
        if r["topologie"] == "T_UNBESTIMMT":
            e["hinweis"] = "koennte zu %s gehoeren — Topologie unbestimmt" % (
                topologie or "jeder Topologie")
            moeglich.append(e)
        elif topologie is None or r["topologie"] == topologie:
            sicher.append(e)
    return {"knoten": knoten, "topologie": topologie or "ALLE",
            "sicher": sicher, "moeglich": moeglich,
            "gesetz": "G3: UNBESTIMMT verbreitert, es wird nicht weggelassen",
            "kandidat": "H5", "offen": 1}


def cmd_nachbarn(args):
    c = verbinden(schreibend=False)
    r = nachbarschaft(c, args.knoten, args.topologie)
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_verbreiterung(args):
    """Um wie viel waechst die Nachbarschaft durch GESETZ 3? Gemengen-SQL,
    ueber ALLE Knoten, keine Stichprobe."""
    c = verbinden(schreibend=False)
    # Nachbarschaftsgrad je (Knoten,Topologie) — jede Kante zaehlt an beiden Enden.
    c.execute("""CREATE TEMP TABLE grad AS
        SELECT knoten, topologie, COUNT(*) g FROM (
            SELECT von knoten, topologie FROM wm_topologie WHERE gueltig_bis IS NULL
            UNION ALL
            SELECT nach, topologie FROM wm_topologie WHERE gueltig_bis IS NULL)
        GROUP BY 1,2""")
    unb = {r[0]: r[1] for r in c.execute(
        "SELECT knoten,g FROM grad WHERE topologie='T_UNBESTIMMT'")}
    knoten_ges = c.execute("SELECT COUNT(DISTINCT knoten) FROM grad").fetchone()[0]
    print("Knoten mit mindestens einer Kante : %d" % knoten_ges)
    print("Knoten mit UNBESTIMMTER Kante     : %d  (%.2f %%)"
          % (len(unb), 100.0 * len(unb) / max(1, knoten_ges)))
    print("\n%-16s %9s %9s %9s %8s %10s" %
          ("TOPOLOGIE", "sicher", "moeglich", "gesamt", "Faktor", "betroffen"))
    for t in ["T_SEMANTIK", "T_AUSBREITUNG", "T_ENTWERTUNG", "T_PROZESS",
              "T_ORT", "T_AUTORITAET", "T_KAUSALKREDIT"]:
        s = c.execute("SELECT COALESCE(SUM(g),0) FROM grad WHERE topologie=?",
                      (t,)).fetchone()[0]
        m = sum(unb.values())
        # Knoten, die diese Topologie fuehren UND unbestimmte Kanten haben
        betroffen = c.execute(
            "SELECT COUNT(*) FROM grad WHERE topologie=? AND knoten IN "
            "(SELECT knoten FROM grad WHERE topologie='T_UNBESTIMMT')",
            (t,)).fetchone()[0]
        f = ("%.3fx" % ((s + m) / s)) if s else ("unendlich" if m else "-")
        print("%-16s %9d %9d %9d %8s %10d" % (t, s, m, s + m, f, betroffen))
    print("\n'moeglich' ist fuer JEDE Topologie dieselbe Menge — eine unbestimmte")
    print("Kante kommt ueberall in Frage. Genau das ist GESETZ 3.")
    print("Die Verbreiterung ist NICHT gleichmaessig verteilt: sie trifft nur die")
    print("Knoten, die eine unbestimmte Kante haben. Fuer die ist der Zuwachs gross,")
    print("fuer alle anderen null. Deshalb hier der Zuwachs je betroffenem Knoten:")
    for r in c.execute("""SELECT AVG(g), MAX(g) FROM grad WHERE topologie='T_UNBESTIMMT'"""):
        print("  unbestimmte Kanten je betroffenem Knoten: Mittel %.2f, Maximum %d"
              % (r[0] or 0, r[1] or 0))


# ------------------------------------------------ 1./5. Lesen (H5 + GESETZ 3)

_ID_KONTEXT = None      # wird beim ersten Gebrauch gefuellt


def _id_lesarten(c, artikel_id):
    """Achse 'id' zur Laufzeit aus `artikel` — nicht gespeichert.

    Genau dieselben Zeilen, die `ernte` vorher als Kopie abgelegt hat:
    sphaere/status/epistemik unter kontext {"identitaetsachse":"id"}.
    Ruht auf GESETZ 1, also offen=0.
    """
    global _ID_KONTEXT
    if _ID_KONTEXT is None:
        _ID_KONTEXT = kanon({"identitaetsachse": "id"})
    r = c.execute("""SELECT sphaere,status,epistemic_class,konfidenz
                     FROM artikel WHERE id=?""", (artikel_id,)).fetchone()
    if r is None:
        return []
    raus = []
    for achse, wert in (("sphaere", r["sphaere"]), ("status", r["status"]),
                        ("epistemik", r["epistemic_class"])):
        if not wert:
            continue
        quelle = "artikel.%s" % achse
        raus.append({
            "lesart_id": lesart_kennung(artikel_id, achse, wert,
                                        {"identitaetsachse": "id"}, quelle),
            "achse": achse, "wert": wert, "kontext_json": _ID_KONTEXT,
            "domaene": "FACT_EXACT", "quelle": quelle,
            "konfidenz": r["konfidenz"], "erzeugt_am": None, "gueltig_von": None,
            "kandidat": "gesetz:G1", "offen": 0,
            "offen_grund": ("zur Laufzeit aus artikel erzeugt, nicht gespeichert; "
                            "ruht auf GESETZ 1"),
            "basis_json": None,
        })
    return raus


def lesen(c, artikel_id, kontext=None):
    """Kontext-gesteuertes Auflesen (H5, OFFEN) unter GESETZ 1 und GESETZ 3.

    Gibt NIE eine Lesart so zurueck, als waere sie die einzige.
    Rate nie: weder die neueste noch die mit der hoechsten Konfidenz.
    """
    kontext = kontext or {}
    reihen = list(c.execute(
        """SELECT lesart_id,achse,wert,kontext_json,domaene,quelle,konfidenz,
                  erzeugt_am,gueltig_von,kandidat,offen,offen_grund,basis_json
           FROM wm_lesart
           WHERE artikel_id=? AND gueltig_bis IS NULL""",
        (artikel_id,)).fetchall())

    # Die Achse 'id' wird zur LAUFZEIT aus `artikel` erzeugt statt gespeichert.
    # Sie war eine reine Kopie der kanonischen Wahrheit (5868 Zeilen). udb
    # fuehrt sie ohnehin; doppelt halten heisst zweimal pflegen.
    reihen.extend(_id_lesarten(c, artikel_id))

    # Waehrend der Umstellung koennen gespeicherte und erzeugte id-Lesarten
    # nebeneinander liegen. lesart_id ist deterministisch, also sind sie
    # identisch — einmal reicht.
    gesehen, eindeutig = set(), []
    for r in reihen:
        if r["lesart_id"] in gesehen:
            continue
        gesehen.add(r["lesart_id"])
        eindeutig.append(r)
    reihen = eindeutig

    achsen = {}
    for r in reihen:
        achsen.setdefault(r["achse"], []).append(r)

    ergebnis = {"artikel_id": artikel_id, "kontext": kontext, "achsen": {},
                "gesetze": ["G1 kein destruktiver Kollaps",
                            "G3 UNKNOWN verbreitert"],
                "kandidat": "H5", "offen": 1,
                "offen_hinweis": "H5 (kontext-gesteuertes Auflesen) ist OPEN."}

    for achse, rr in achsen.items():
        passt, unbekannt, passt_nicht = [], [], []
        for r in rr:
            praed = json.loads(r["kontext_json"] or "{}")
            fehlend = [k for k in praed if k not in kontext]
            if fehlend:
                unbekannt.append((r, fehlend))
            elif all(kontext.get(k) == v for k, v in praed.items()):
                passt.append((r, []))
            else:
                passt_nicht.append((r, []))

        def form(paar, warum):
            r, fehlend = paar
            d = {"lesart_id": r["lesart_id"], "wert": r["wert"],
                 "domaene": r["domaene"], "quelle": r["quelle"],
                 "kontext": json.loads(r["kontext_json"] or "{}"),
                 "kandidat": r["kandidat"], "offen": r["offen"],
                 "offen_grund": r["offen_grund"], "warum": warum}
            if fehlend:
                d["fehlender_kontext"] = fehlend
            return d

        if unbekannt:
            # GESETZ 3: unbestimmte Abhaengigkeit verbreitert und eskaliert.
            kand = [form(p, "Kontext bestimmt nicht") for p in unbekannt] + \
                   [form(p, "passt zum Kontext") for p in passt]
            achsen_erg = {
                "status": "UNBESTIMMT",
                "gewaehlt": None,
                "kandidaten": kand,
                "verworfen": [form(p, "Kontext schliesst aus") for p in passt_nicht],
                "grund": "GESETZ 3: fehlender Kontext (%s) verbreitert; es wird "
                         "NICHT geraten, auch nicht nach Datum oder Konfidenz."
                         % ",".join(sorted({f for _, fl in unbekannt for f in fl})),
            }
        elif len(passt) == 1 and not passt_nicht and len(rr) == 1:
            achsen_erg = {
                "status": "BESTIMMT",
                "gewaehlt": form(passt[0], "einzige Lesart"),
                "kandidaten": [],
                "verworfen": [],
                "grund": "genau eine Lesart vorhanden; keine Alternative unterdrueckt.",
            }
        elif len(passt) == 1:
            achsen_erg = {
                "status": "BESTIMMT",
                "gewaehlt": form(passt[0], "Kontext waehlt diese"),
                "kandidaten": [],
                "verworfen": [form(p, "Kontext schliesst aus") for p in passt_nicht],
                "grund": "Kontext trifft genau eine Lesart; die anderen bleiben "
                         "erhalten und werden mitgeliefert (GESETZ 1).",
            }
        elif len(passt) > 1:
            achsen_erg = {
                "status": "UNBESTIMMT",
                "gewaehlt": None,
                "kandidaten": [form(p, "passt zum Kontext") for p in passt],
                "verworfen": [form(p, "Kontext schliesst aus") for p in passt_nicht],
                "grund": "mehrere Lesarten passen gleichzeitig; kein Kollaps.",
            }
        else:
            achsen_erg = {
                "status": "UNBESTIMMT",
                "gewaehlt": None,
                "kandidaten": [form(p, "keine passt zum Kontext") for p in passt_nicht],
                "verworfen": [],
                "grund": "keine Lesart passt zum Kontext; GESETZ 3: verbreitern "
                         "statt raten.",
            }
        achsen_erg["anzahl_lesarten"] = len(rr)
        ergebnis["achsen"][achse] = achsen_erg

    if not achsen:
        ergebnis["achsen"] = {}
        ergebnis["hinweis"] = "keine Lesart hinterlegt — UNBEKANNT, nicht leer."
    return ergebnis


def cmd_lesen(args):
    c = verbinden(schreibend=False)
    k = json.loads(args.kontext) if args.kontext else {}
    t0 = time.perf_counter()
    r = lesen(c, args.artikel_id, k)
    ms = (time.perf_counter() - t0) * 1000.0
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print("\n-- %0.3f ms (kalt) --" % ms, file=sys.stderr)


def cmd_bank(args):
    """Latenz von lesen() messen — warm, wie gefordert."""
    c = verbinden(schreibend=False)
    ids = [r[0] for r in c.execute(
        """SELECT artikel_id FROM wm_lesart WHERE gueltig_bis IS NULL
           GROUP BY artikel_id ORDER BY COUNT(*) DESC LIMIT ?""",
        (args.n,)).fetchall()]
    if not ids:
        print("keine Lesarten — erst 'ernte' laufen lassen.")
        return
    for i in ids[:50]:          # aufwaermen
        lesen(c, i, {"identitaetsachse": "id"})
    zeiten = []
    for i in ids:
        t0 = time.perf_counter()
        lesen(c, i, {"identitaetsachse": "id"})
        zeiten.append((time.perf_counter() - t0) * 1000.0)
    zeiten.sort()
    n = len(zeiten)
    print("lesen() warm, n=%d Artikel (die mit den MEISTEN Lesarten)" % n)
    print("  mittel : %0.3f ms" % (sum(zeiten) / n))
    print("  median : %0.3f ms" % zeiten[n // 2])
    print("  p95    : %0.3f ms" % zeiten[int(n * 0.95) - 1])
    print("  p99    : %0.3f ms" % zeiten[int(n * 0.99) - 1])
    print("  max    : %0.3f ms" % zeiten[-1])
    print("  Ziel   : < 5 ms warm  ->  %s" %
          ("ERREICHT" if zeiten[int(n * 0.99) - 1] < 5.0 else "VERFEHLT"))


# ------------------------------------------------------------------- 2. Kanten

def cmd_kanten(args):
    """wm_topologie aus `kante` ableiten und die Mischkanten ausweisen."""
    c = verbinden()
    n = jetzt()
    kanten = c.execute("SELECT von,nach,art,konfidenz,beleg FROM kante").fetchall()

    # Messung ZUERST: wie viele Paare tragen mehr als eine Topologie?
    paar_top = {}
    paar_art = {}
    mehrfach_kanten = 0
    for k in kanten:
        ts = ART_TOPOLOGIE.get(k["art"], [("T_UNBESTIMMT", "art nicht im Katalog")])
        if len(ts) > 1:
            mehrfach_kanten += 1
        for t, _ in ts:
            paar_top.setdefault((k["von"], k["nach"]), set()).add(t)
        paar_art.setdefault((k["von"], k["nach"]), set()).add(k["art"])

    paare = len(paar_top)
    mehrere_arten = sum(1 for v in paar_art.values() if len(v) > 1)
    echt_gemischt = sum(1 for v in paar_top.values() if len(v) > 1)
    nur_art_dopplung = sum(1 for p in paar_art
                           if len(paar_art[p]) > 1 and len(paar_top[p]) == 1)
    unbestimmt_beteiligt = sum(1 for v in paar_top.values() if "T_UNBESTIMMT" in v)

    kombi = {}
    for p, ts in paar_top.items():
        if len(ts) > 1:
            kombi["+".join(sorted(ts))] = kombi.get("+".join(sorted(ts)), 0) + 1

    print("== GESETZ 2, gemessen an `kante` ==")
    print("  Kanten gesamt            : %d" % len(kanten))
    print("  davon mehrfach zugehoerig: %d   (eine Kante, mehrere Topologien "
          "— GESETZ 2 erlaubt das ausdruecklich)" % mehrfach_kanten)
    print("  Knotenpaare gesamt       : %d" % paare)
    print("  Paare mit >1 kante.art   : %d" % mehrere_arten)
    print("  davon ECHT GEMISCHT      : %d   (Paar traegt >=2 VERSCHIEDENE Topologien)"
          % echt_gemischt)
    print("  davon nur art-Dopplung   : %d   (zwei arten, dieselbe Topologie)"
          % nur_art_dopplung)
    print("  Paare mit T_UNBESTIMMT   : %d   (GESETZ 3: verbreitert, nicht geraten)"
          % unbestimmt_beteiligt)
    print("  gemischte Kombinationen:")
    for k2, v in sorted(kombi.items(), key=lambda x: -x[1])[:15]:
        print("    %-45s %d" % (k2, v))

    if args.trocken:
        print("\n(trocken — nichts geschrieben)")
        return

    def tun():
        with c:
            for k in kanten:
                ts = ART_TOPOLOGIE.get(k["art"],
                                       [("T_UNBESTIMMT", "art nicht im Katalog")])
                for t, warum in ts:
                    kand = "H6" if t == "T_KAUSALKREDIT" else (
                        "gesetz:G3" if t == "T_UNBESTIMMT" else "H5")
                    grund = ("Aufteilung in getrennte Topologien ruht auf %s (Status OPEN). "
                             "Zuordnung aus den Daten: %s" % (kand, warum))
                    c.execute(
                    """INSERT INTO wm_topologie
                       (von,nach,topologie,herkunft_art,gewicht,basis_json,quelle,
                        erzeugt_am,gueltig_von,gueltig_bis,kandidat,offen,offen_grund)
                       VALUES (?,?,?,?,?,?,?,?,?,NULL,?,?,?)
                       ON CONFLICT(von,nach,topologie,herkunft_art) DO UPDATE SET
                         gewicht=excluded.gewicht,
                         basis_json=excluded.basis_json,
                         quelle=excluded.quelle,
                         erzeugt_am=excluded.erzeugt_am,
                         gueltig_von=excluded.gueltig_von,
                         gueltig_bis=NULL,
                         kandidat=excluded.kandidat,
                         offen=excluded.offen,
                         offen_grund=excluded.offen_grund""",
                    (k["von"], k["nach"], t, k["art"],
                     k["konfidenz"] if k["konfidenz"] is not None else 1.0,
                     basis("kanten-ableitung", "kante.art=%s" % k["art"]),
                     k["beleg"], n, n, kand, 1, grund))
    mit_wiederholung(tun)

    # Ueberholte Zuordnungen ausmustern — NICHT loeschen (GESETZ 1).
    gueltig = [(a, t) for a, ts in ART_TOPOLOGIE.items() for t, _ in ts]
    def raus():
        with c:
            cur = c.execute("SELECT COUNT(*) FROM wm_topologie WHERE gueltig_bis IS NULL")
            offen_paare = c.execute(
                "SELECT DISTINCT herkunft_art,topologie FROM wm_topologie "
                "WHERE gueltig_bis IS NULL").fetchall()
            # Eine Art, die NICHT im Katalog steht, gehoert zu Recht auf
            # T_UNBESTIMMT — die darf nicht ausgemustert werden.
            weg = [(r["herkunft_art"], r["topologie"]) for r in offen_paare
                   if (r["herkunft_art"], r["topologie"]) not in gueltig
                   and not (r["herkunft_art"] not in ART_TOPOLOGIE
                            and r["topologie"] == "T_UNBESTIMMT")]
            k = 0
            for a, t in weg:
                cur = c.execute("UPDATE wm_topologie SET gueltig_bis=? "
                                "WHERE herkunft_art=? AND topologie=? AND gueltig_bis IS NULL",
                                (n, a, t))
                k += cur.rowcount
            return k, weg
    k, weg = mit_wiederholung(raus)
    if k:
        print("\n  ueberholte Zuordnungen ausgemustert (nicht geloescht): %d" % k)
        for a, t in weg:
            print("    %s -> %s" % (a, t))

    ges = c.execute("SELECT COUNT(*) FROM wm_topologie WHERE gueltig_bis IS NULL").fetchone()[0]
    print("\n  wm_topologie gueltige Zeilen: %d" % ges)
    for r in c.execute("""SELECT topologie,COUNT(*) n FROM wm_topologie
                          WHERE gueltig_bis IS NULL GROUP BY 1 ORDER BY 2 DESC"""):
        print("    %-16s %d" % (r[0], r[1]))


# --------------------------------------------------------------------- Ernte

def cmd_ernte(args):
    """Lesarten aus dem Bestand ableiten. `artikel` wird NICHT veraendert."""
    c = verbinden()
    n = jetzt()
    reihen = []

    def add(aid, achse, wert, kontext, quelle, kandidat, offen, grund,
            domaene="FACT_EXACT", konf=None):
        reihen.append((lesart_kennung(aid, achse, wert, kontext, quelle),
                       aid, achse, wert, kanon(kontext), domaene,
                       basis("ernte", quelle), quelle, konf, n, n,
                       kandidat, offen, grund))

    # A) Identitaetsachse "id": was heute in `artikel` steht.
    #    Ruht allein auf GESETZ 1 -> offen=0.
    G1 = ("Zeile ruht auf GESETZ 1 (C-CURRENT-001 / "
          "KMP-CLAY-HYPERPOSITION-SEMANTICS). Achtung: C-CURRENT-001 traegt "
          "scope 'RAE-8.8/G3 sandbox' = synthetische Grenze. "
          "Das Feld basis_json folgt H3 (OPEN).")
    for r in c.execute("""SELECT id,sphaere,status,epistemic_class,konfidenz
                          FROM artikel"""):
        for achse, wert in (("sphaere", r["sphaere"]), ("status", r["status"]),
                            ("epistemik", r["epistemic_class"])):
            if wert:
                add(r["id"], achse, wert, {"identitaetsachse": "id"},
                    "artikel.%s" % achse, "gesetz:G1", 0, G1, konf=r["konfidenz"])

    # B) Identitaetsachse "inhalt": KMP-G11-IDENTITY-AXES (OPEN_REFINEMENT).
    #    Zwei Artikel mit kante.art='gleicher_inhalt' sind auf der
    #    Inhaltsachse dasselbe. Dann ist der Wert des Partners eine
    #    gleichzeitig gueltige Lesart. Kein Ueberschreiben.
    G11 = ("Zeile ruht auf KMP-G11-IDENTITY-AXES (Status OPEN_REFINEMENT): "
           "Feuerschneisen sollen die Identitaets-Vergleichsachse deklarieren. "
           "NICHT entschieden.")
    b_zahl = 0
    for r in c.execute("""SELECT k.von v,k.nach w,
                                 a.sphaere asp,b.sphaere bsp,
                                 a.status ast,b.status bst
                          FROM kante k
                          JOIN artikel a ON a.id=k.von
                          JOIN artikel b ON b.id=k.nach
                          WHERE k.art='gleicher_inhalt'"""):
        for achse, x, y in (("sphaere", r["asp"], r["bsp"]),
                            ("status", r["ast"], r["bst"])):
            if x != y:
                if y:
                    add(r["v"], achse, y, {"identitaetsachse": "inhalt"},
                        "gleicher_inhalt:%s" % r["w"], "KMP-G11-IDENTITY-AXES", 1, G11)
                    b_zahl += 1
                if x:
                    add(r["w"], achse, x, {"identitaetsachse": "inhalt"},
                        "gleicher_inhalt:%s" % r["v"], "KMP-G11-IDENTITY-AXES", 1, G11)
                    b_zahl += 1
        # Die Identitaet SELBST ist mehrdeutig: welche Zeile ist "der" Fakt?
        # Heute gewinnt willkuerlich eine. Beide Antworten sind gueltig.
        add(r["v"], "identitaet", r["w"], {"identitaetsachse": "inhalt"},
            "gleicher_inhalt:%s" % r["w"], "KMP-G11-IDENTITY-AXES", 1, G11)
        add(r["w"], "identitaet", r["v"], {"identitaetsachse": "inhalt"},
            "gleicher_inhalt:%s" % r["v"], "KMP-G11-IDENTITY-AXES", 1, G11)
        b_zahl += 2

    # C) Identitaetsachse "logisch": mehrere artikel.id teilen eine logical_id.
    #    Auch das ist eine Identitaetsachse (KMP-G11, OPEN).
    gruppen = {}
    for r in c.execute("""SELECT id,logical_id,sphaere,status,epistemic_class
                          FROM artikel WHERE logical_id IS NOT NULL"""):
        gruppen.setdefault(r["logical_id"], []).append(
            (r["id"], r["sphaere"], r["status"], r["epistemic_class"]))
    c_zahl = 0
    uebersprungen = 0
    for lid, mit in gruppen.items():
        if len(mit) < 2:
            continue
        if len(mit) > args.gruppen_kappe:
            uebersprungen += 1
            continue
        for aid, sp, st, ep in mit:
            for oid, osp, ost, oep in mit:
                if oid == aid:
                    continue
                # Die Identitaet selbst: dieselbe logische Sache, andere Zeile.
                # Heute gewinnt willkuerlich eine — das ist der Kollaps.
                add(aid, "identitaet", oid, {"identitaetsachse": "logisch"},
                    "logical_id:%s" % oid, "KMP-G11-IDENTITY-AXES", 1, G11)
                c_zahl += 1
                for achse, eigen, fremd in (("sphaere", sp, osp),
                                            ("status", st, ost),
                                            ("epistemik", ep, oep)):
                    if fremd and fremd != eigen:
                        add(aid, achse, fremd, {"identitaetsachse": "logisch"},
                            "logical_id:%s" % oid, "KMP-G11-IDENTITY-AXES", 1, G11)
                        c_zahl += 1

    def tun():
        with c:
            c.executemany(
                """INSERT INTO wm_lesart
                   (lesart_id,artikel_id,achse,wert,kontext_json,domaene,
                    basis_json,quelle,konfidenz,erzeugt_am,gueltig_von,
                    gueltig_bis,kandidat,offen,offen_grund)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?)
                   ON CONFLICT(lesart_id) DO UPDATE SET
                     wert=excluded.wert,
                     kontext_json=excluded.kontext_json,
                     domaene=excluded.domaene,
                     basis_json=excluded.basis_json,
                     quelle=excluded.quelle,
                     konfidenz=excluded.konfidenz,
                     erzeugt_am=excluded.erzeugt_am,
                     gueltig_von=excluded.gueltig_von,
                     gueltig_bis=NULL,
                     kandidat=excluded.kandidat,
                     offen=excluded.offen,
                     offen_grund=excluded.offen_grund""", reihen)
    mit_wiederholung(tun)
    print("Lesarten geschrieben (INSERT ... ON CONFLICT DO UPDATE, "
          "ausdrueckliche Spaltenliste): %d" % len(reihen))
    print("  A Achse 'id'      : %d" % (len(reihen) - b_zahl - c_zahl))
    print("  B Achse 'inhalt'  : %d   (KMP-G11, OFFEN)" % b_zahl)
    print("  C Achse 'logisch' : %d   (KMP-G11, OFFEN)" % c_zahl)
    print("  Gruppen uebersprungen (groesser als Kappe %d): %d"
          % (args.gruppen_kappe, uebersprungen))


def cmd_aufraeumen(args):
    """Die gespeicherten id-Lesarten entfernen — sie sind reine Kopien aus
    `artikel` und werden seit dem Umbau zur Laufzeit erzeugt.

    Erst sichern, dann loeschen. Ohne Sicherung passiert nichts.
    """
    c = verbinden()
    kid = kanon({"identitaetsachse": "id"})
    reihen = c.execute("SELECT * FROM wm_lesart WHERE kontext_json=?", (kid,)).fetchall()
    if not reihen:
        print("nichts zu tun — keine gespeicherten id-Lesarten vorhanden.")
        return
    spalten = [d[0] for d in c.execute("SELECT * FROM wm_lesart LIMIT 1").description]
    ziel = args.sicherung or ("/opt/clayverse/werkzeug/wm_proben/wm_lesart-id-%s.json"
                              % jetzt().replace(":", "").replace("-", ""))
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump({"spalten": spalten,
                   "zeilen": [list(r) for r in reihen]},
                  f, ensure_ascii=False)
    groesse = os.path.getsize(ziel)
    print("Sicherung: %s (%d Zeilen, %d Bytes)" % (ziel, len(reihen), groesse))
    if groesse < 1000 or len(reihen) == 0:
        print("Sicherung sieht nicht plausibel aus — ABBRUCH, nichts geloescht.")
        return 1
    if args.trocken:
        print("(trocken — nichts geloescht)")
        return
    def tun():
        with c:
            cur = c.execute("DELETE FROM wm_lesart WHERE kontext_json=?", (kid,))
            return cur.rowcount
    k = mit_wiederholung(tun)
    print("geloescht: %d Zeilen. Sie werden ab jetzt in lesen() zur Laufzeit "
          "aus `artikel` erzeugt." % k)
    print("Rueckweg: die Sicherung oben enthaelt jede Zeile vollstaendig.")


def cmd_ausmustern(args):
    """Lesart zurueckziehen — NIE loeschen, nur gueltig_bis setzen."""
    c = verbinden()
    n = jetzt()
    def tun():
        with c:
            cur = c.execute("""UPDATE wm_lesart SET gueltig_bis=?
                               WHERE lesart_id=? AND gueltig_bis IS NULL""",
                            (n, args.lesart_id))
            return cur.rowcount
    k = mit_wiederholung(tun)
    print("ausgemustert: %d (gueltig_bis=%s). Es wurde nichts geloescht." % (k, n))


# --------------------------------------------------------------------- Messen

def cmd_messen(args):
    """Die Groesse des heutigen destruktiven Kollapses."""
    c = verbinden(schreibend=False)
    q = lambda s, p=(): c.execute(s, p).fetchone()[0]
    print("== 1. Wie viele Fakten haben ueberhaupt eine sphaere? ==")
    ges = q("SELECT COUNT(*) FROM artikel")
    mit = q("SELECT COUNT(*) FROM artikel WHERE sphaere IS NOT NULL AND sphaere<>''")
    print("  artikel gesamt         : %d" % ges)
    print("  mit sphaere            : %d  (%.1f %%)" % (mit, 100.0 * mit / ges))
    print("  ohne sphaere           : %d" % (ges - mit))
    for r in c.execute("""SELECT sphaere,COUNT(*) FROM artikel
                          WHERE sphaere IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"""):
        print("      %-14s %d" % (r[0], r[1]))
    print("  Nebentabelle artikel_sphaere: %d Zeilen, %d Artikel, "
          "max %d sphaeren je Artikel"
          % (q("SELECT COUNT(*) FROM artikel_sphaere"),
             q("SELECT COUNT(DISTINCT artikel_id) FROM artikel_sphaere"),
             q("SELECT MAX(n) FROM (SELECT COUNT(*) n FROM artikel_sphaere GROUP BY artikel_id)")))

    print("\n== 2. epistemic_class CONFLICT ==")
    print("  epistemic_class = 'CONFLICT'      : %d"
          % q("SELECT COUNT(*) FROM artikel WHERE epistemic_class='CONFLICT'"))
    print("  epistemic_class LIKE '%%CONFLICT%%': %d"
          % q("SELECT COUNT(*) FROM artikel WHERE epistemic_class LIKE '%CONFLICT%'"))
    print("  status LIKE '%%CONFLICT%%'         : %d"
          % q("SELECT COUNT(*) FROM artikel WHERE status LIKE '%CONFLICT%'"))
    for r in c.execute("""SELECT status,COUNT(*) FROM artikel
                          WHERE status LIKE '%CONFLICT%' GROUP BY 1"""):
        print("      %-40s %d" % (r[0], r[1]))

    print("\n== 3. Ueberschriebene sphaere / konkurrierende Vorschlaege ==")
    print("  anreicherung Zeilen              : %d" % q("SELECT COUNT(*) FROM anreicherung"))
    print("  anreicherung betroffene artikel  : %d"
          % q("SELECT COUNT(DISTINCT artikel_id) FROM anreicherung"))
    print("  artikel mit >1 anreicherung      : %d"
          % q("""SELECT COUNT(*) FROM (SELECT artikel_id FROM anreicherung
                 GROUP BY 1 HAVING COUNT(*)>1)"""))
    print("  artikel mit >1 verschiedenem hash: %d"
          % q("""SELECT COUNT(*) FROM (SELECT artikel_id FROM anreicherung
                 GROUP BY artikel_id HAVING COUNT(DISTINCT hash)>1)"""))
    print("  artikel.sphaere weicht von artikel_sphaere ab: %d"
          % q("""SELECT COUNT(*) FROM artikel a
                 WHERE a.sphaere IS NOT NULL AND a.sphaere<>''
                   AND EXISTS(SELECT 1 FROM artikel_sphaere s WHERE s.artikel_id=a.id)
                   AND NOT EXISTS(SELECT 1 FROM artikel_sphaere s
                                  WHERE s.artikel_id=a.id AND s.sphaere=a.sphaere)"""))
    print("  -> es gibt KEINE Historie der ueberschriebenen Werte. Was frueher "
          "in artikel.sphaere stand, ist nicht rekonstruierbar. UNBEKANNT.")

    print("\n== 4. Verdeckter Kollaps ueber Identitaetsachsen (KMP-G11, OFFEN) ==")
    print("  logical_id-Gruppen mit >1 artikel : %d"
          % q("""SELECT COUNT(*) FROM (SELECT logical_id FROM artikel
                 WHERE logical_id IS NOT NULL GROUP BY 1 HAVING COUNT(*)>1)"""))
    print("  artikel in solchen Gruppen        : %d"
          % q("""SELECT COUNT(*) FROM artikel a WHERE a.logical_id IS NOT NULL
                 AND (SELECT COUNT(*) FROM artikel b WHERE b.logical_id=a.logical_id)>1"""))
    print("  gleicher_inhalt-Paare, sphaere weicht ab : %d"
          % q("""SELECT COUNT(*) FROM kante k JOIN artikel a ON a.id=k.von
                 JOIN artikel b ON b.id=k.nach WHERE k.art='gleicher_inhalt'
                 AND a.sphaere IS NOT NULL AND b.sphaere IS NOT NULL
                 AND a.sphaere<>b.sphaere"""))
    print("  gleicher_inhalt-Paare, status weicht ab  : %d"
          % q("""SELECT COUNT(*) FROM kante k JOIN artikel a ON a.id=k.von
                 JOIN artikel b ON b.id=k.nach WHERE k.art='gleicher_inhalt'
                 AND a.status IS NOT NULL AND b.status IS NOT NULL
                 AND a.status<>b.status"""))


# ---------------------------------------------------------------------- Stand

def cmd_stand(args):
    c = verbinden(schreibend=False)
    hat = lambda t: c.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (t,)).fetchone()[0] > 0
    if not hat("wm_lesart"):
        print("wm_* fehlt. Erst 'weltmodell.py init'.")
        return

    # Die Achse 'id' liegt nicht mehr in der Tabelle, sondern wird in lesen()
    # zur Laufzeit aus `artikel` erzeugt. Fuer die Zaehlung muss sie mit rein,
    # sonst zaehlt der Stand weniger als lesen() liefert.
    kid = kanon({"identitaetsachse": "id"})
    c.execute("""CREATE TEMP TABLE alle AS
        SELECT artikel_id, achse, kontext_json FROM wm_lesart
          WHERE gueltig_bis IS NULL AND kontext_json <> ?
        UNION ALL SELECT id,'sphaere',?   FROM artikel WHERE sphaere IS NOT NULL AND sphaere<>''
        UNION ALL SELECT id,'status',?    FROM artikel WHERE status IS NOT NULL AND status<>''
        UNION ALL SELECT id,'epistemik',? FROM artikel WHERE epistemic_class IS NOT NULL
        """, (kid, kid, kid, kid))
    lz = c.execute("SELECT COUNT(*) FROM alle WHERE kontext_json=?", (kid,)).fetchone()[0]

    z = c.execute("""SELECT COUNT(*) n, COUNT(DISTINCT artikel_id) a,
                            SUM(CASE WHEN gueltig_bis IS NULL THEN 1 ELSE 0 END) g,
                            SUM(CASE WHEN offen=1 THEN 1 ELSE 0 END) o
                     FROM wm_lesart""").fetchone()
    ein = c.execute("""SELECT COUNT(*) FROM (
        SELECT artikel_id,achse FROM alle GROUP BY 1,2 HAVING COUNT(*)=1)""").fetchone()[0]
    mehr = c.execute("""SELECT COUNT(*) FROM (
        SELECT artikel_id,achse FROM alle GROUP BY 1,2 HAVING COUNT(*)>1)""").fetchone()[0]
    a_ein = c.execute("""SELECT COUNT(*) FROM (
        SELECT artikel_id FROM alle GROUP BY 1 HAVING COUNT(*)=1)""").fetchone()[0]
    a_mehr = c.execute("""SELECT COUNT(*) FROM (
        SELECT artikel_id FROM alle GROUP BY 1 HAVING COUNT(*)>1)""").fetchone()[0]
    # UNBESTIMMT ohne Kontext: sobald eine Achse Lesarten mit Kontextpraedikat
    # hat, die der leere Kontext nicht bestimmt -> GESETZ 3.
    unbest = c.execute("""SELECT COUNT(*) FROM (
        SELECT artikel_id,achse FROM alle WHERE kontext_json<>'{}'
        GROUP BY 1,2)""").fetchone()[0]
    ausgem = c.execute("SELECT COUNT(*) FROM wm_lesart WHERE gueltig_bis IS NOT NULL").fetchone()[0]
    # Zweite Messung unter dem gebraeuchlichen Kontext: identitaetsachse=id.
    # Ohne jeden Kontext ist per GESETZ 3 alles unbestimmt — das ist richtig,
    # aber wenig aussagekraeftig. Also zusaetzlich mit gesetztem Kontext.
    best_id = c.execute("""SELECT COUNT(*) FROM (
        SELECT artikel_id,achse FROM alle GROUP BY 1,2
        HAVING SUM(CASE WHEN kontext_json=? THEN 1 ELSE 0 END)=1)""",
        (kid,)).fetchone()[0]
    unbest_id = c.execute("""SELECT COUNT(*) FROM (
        SELECT artikel_id,achse FROM alle GROUP BY 1,2
        HAVING SUM(CASE WHEN kontext_json=? THEN 1 ELSE 0 END)<>1)""",
        (kid,)).fetchone()[0]

    top = c.execute("""SELECT COUNT(*) n,
                              SUM(CASE WHEN offen=1 THEN 1 ELSE 0 END) o
                       FROM wm_topologie""").fetchone()
    gem = c.execute("""SELECT COUNT(*) FROM (
        SELECT von,nach FROM wm_topologie WHERE gueltig_bis IS NULL
        GROUP BY 1,2 HAVING COUNT(DISTINCT topologie)>1)""").fetchone()[0]
    verw = c.execute("""SELECT COUNT(*) FROM wm_guss_log
                        WHERE ergebnis='VERWEIGERT'""").fetchone()[0]
    erl = c.execute("""SELECT COUNT(*) FROM wm_guss_log
                       WHERE ergebnis='ERLAUBT'""").fetchone()[0]

    L = "  %-52s %10s"
    print("=" * 66)
    print("  WELTMODELL — STAND   %s" % jetzt())
    print("=" * 66)
    print(L % ("Lesarten gespeichert", z["n"] or 0))
    print(L % ("Lesarten zur Laufzeit erzeugt (Achse id)", lz))
    print(L % ("Lesarten gesamt", (z["n"] or 0) + lz))
    print(L % ("davon gueltig (gueltig_bis IS NULL)", z["g"] or 0))
    print(L % ("davon ausgemustert (nie geloescht)", ausgem))
    print(L % ("davon auf OFFENEM Kandidaten (offen=1)", z["o"] or 0))
    print(L % ("Artikel mit Lesarten", z["a"] or 0))
    print("-" * 66)
    print(L % ("Fakten mit GENAU 1 Lesart", a_ein))
    print(L % ("Fakten mit 2+ Lesarten (Hyperposition)", a_mehr))
    print(L % ("(Artikel,Achse)-Paare mit genau 1 Lesart", ein))
    print(L % ("(Artikel,Achse)-Paare mit 2+ Lesarten", mehr))
    print(L % ("(Artikel,Achse) UNBESTIMMT ohne Kontext (G3)", unbest))
    print(L % ("   dasselbe mit Kontext identitaetsachse=id: BESTIMMT", best_id))
    print(L % ("   dasselbe mit Kontext identitaetsachse=id: UNBESTIMMT", unbest_id))
    print("-" * 66)
    print(L % ("Topologie-Kanten gesamt", top["n"] or 0))
    print(L % ("davon auf OFFENEM Kandidaten (offen=1)", top["o"] or 0))
    print(L % ("Knotenpaare auf >=2 Topologien (GESETZ 2)", gem))
    for r in c.execute("""SELECT topologie,COUNT(*) FROM wm_topologie
                          GROUP BY 1 ORDER BY 2 DESC"""):
        print(L % ("    " + r[0], r[1]))
    print("-" * 66)
    print(L % ("Guss-Versuche VERWEIGERT", verw))
    print(L % ("Guss-Versuche ERLAUBT", erl))
    print("=" * 66)
    print("  OFFEN: H1..H6 und KMP-G11 tragen Status OPEN. Alles mit offen=1")
    print("  ist Architektur-KANDIDAT, kein Ergebnis. G1 stuetzt sich auf")
    print("  C-CURRENT-001 mit scope 'RAE-8.8/G3 sandbox' (synthetisch).")
    print("=" * 66)


def cmd_regeln(args):
    c = verbinden(schreibend=False)
    print("%-18s %-16s %-9s %-32s %s" %
          ("VON", "NACH", "ERLAUBT", "BEDINGUNG", "KANDIDAT"))
    for r in c.execute("""SELECT * FROM wm_cast_regel
                          ORDER BY erlaubt DESC, von_domaene"""):
        print("%-18s %-16s %-9s %-32s %s(offen=%d)" %
              (r["von_domaene"], r["nach_domaene"],
               "ja" if r["erlaubt"] else "NEIN",
               r["bedingung"] or "-", r["kandidat"], r["offen"]))
    print("\nNicht aufgefuehrte Paare werden abgelehnt. Ablehnung ist Vorgabe.")
    print("Die sieben Domaenen: %s" % ", ".join(DOMAENEN))


def main():
    global DB
    p = argparse.ArgumentParser(description="Weltmodell auf Basis von Hyperposition")
    p.add_argument("--db", default=None)
    s = p.add_subparsers(dest="befehl", required=True)

    s.add_parser("init").set_defaults(fn=cmd_init)
    s.add_parser("stand").set_defaults(fn=cmd_stand)
    s.add_parser("messen").set_defaults(fn=cmd_messen)
    s.add_parser("regeln").set_defaults(fn=cmd_regeln)

    q = s.add_parser("ernte"); q.add_argument("--gruppen-kappe", type=int, default=25)
    q.set_defaults(fn=cmd_ernte)

    q = s.add_parser("kanten"); q.add_argument("--trocken", action="store_true")
    q.set_defaults(fn=cmd_kanten)

    q = s.add_parser("lesen")
    q.add_argument("artikel_id"); q.add_argument("--kontext", default=None,
                                                 help='JSON, z.B. {"identitaetsachse":"id"}')
    q.set_defaults(fn=cmd_lesen)

    q = s.add_parser("giessen")
    q.add_argument("von"); q.add_argument("nach")
    q.add_argument("--artikel-id", default=None,
                   help="Gegenstand des Gusses; ohne ihn ist nichts pruefbar "
                        "und der Guss wird abgelehnt")
    q.add_argument("--gegenstand", default=None)
    q.set_defaults(fn=cmd_giessen)

    q = s.add_parser("nachbarn"); q.add_argument("knoten")
    q.add_argument("--topologie", default=None)
    q.set_defaults(fn=cmd_nachbarn)

    q = s.add_parser("verbreiterung"); q.add_argument("-n", type=int, default=2000)
    q.set_defaults(fn=cmd_verbreiterung)

    q = s.add_parser("aufraeumen")
    q.add_argument("--sicherung", default=None)
    q.add_argument("--trocken", action="store_true")
    q.set_defaults(fn=cmd_aufraeumen)

    q = s.add_parser("ausmustern"); q.add_argument("lesart_id")
    q.set_defaults(fn=cmd_ausmustern)

    q = s.add_parser("bank"); q.add_argument("-n", type=int, default=1000)
    q.set_defaults(fn=cmd_bank)

    a = p.parse_args()
    if a.db:
        DB = a.db
    r = a.fn(a)
    sys.exit(r or 0)


if __name__ == "__main__":
    main()
