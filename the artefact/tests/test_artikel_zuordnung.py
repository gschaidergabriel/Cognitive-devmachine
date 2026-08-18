"""Tests fuer clayverse/artikel_zuordnung.py -- wer kriegt welchen Artikel.

Zentrale Regel des Moduls: zuletzt_von (Git-Committer) entscheidet NIE ueber
Zugehoerigkeit. Diese Datei baut genau die Falle nach, die im Modulkopf
beschrieben ist (501 Andreas-Artikel mit Gabriels Namen als Bearbeiter) und
prueft, dass sie nicht zuschnappt.
"""
from __future__ import annotations

import pytest

from clayverse import profile
from clayverse.artikel_zuordnung import _entscheide, bestand, zuordnen
from clayverse.store import UnifiedDB


@pytest.fixture
def db(tmp_path):
    d = UnifiedDB(tmp_path / "unified.db")
    profile.sicherstellen(d)
    d.db.executescript(
        "CREATE TABLE IF NOT EXISTS artikel(id TEXT PRIMARY KEY, sphaere TEXT, "
        "projekt TEXT, zuletzt_von TEXT)"
    )
    yield d
    d.close()


def _fuelle(db, zeilen):
    """zeilen: Liste (id, sphaere, projekt, zuletzt_von)."""
    with db.tx() as sql:
        sql.executemany(
            "INSERT INTO artikel(id,sphaere,projekt,zuletzt_von) VALUES(?,?,?,?)", zeilen
        )


# ── Regel a: zuletzt_von entscheidet NIE ──────────────────────────────────

def test_andreas_artikel_mit_gabriels_namen_als_committer_geht_an_andreas(db):
    """501 echte Artikel haben genau diese Form -- Dr.-Unterweger-Projekt,
    aber 'Gabriel Gschaider' als zuletzt_von. Muss trotzdem andreas werden."""
    zeilen = [
        (f"a{i}", None, "Dr.-Unterweger", "Gabriel Gschaider") for i in range(5)
    ]
    _fuelle(db, zeilen)
    ergebnis = zuordnen(db)
    assert ergebnis["verteilung"] == {"andreas": 5}
    reihen = db.db.execute(
        "SELECT gehoert FROM entityos_artikel_zuordnung ORDER BY artikel_id"
    ).fetchall()
    assert all(r["gehoert"] == "andreas" for r in reihen)


def test_gleicher_committer_gabriel_selbst_bleibt_gabriel_projekt_faellt_anders(db):
    """Gegenprobe: derselbe Committer-Name, aber ein gabriel-gebundenes Projekt
    -- landet bei gabriel. Zeigt, dass PROJEKT entscheidet, nicht der Name."""
    _fuelle(db, [("b1", None, "Project-Frankenstein", "Gabriel Gschaider")])
    ergebnis = zuordnen(db)
    assert ergebnis["verteilung"] == {"gabriel": 1}


def test_zuletzt_von_taucht_in_keiner_entscheidungsbegruendung_auf(db):
    """Statischer Gegenbeweis: _entscheide bekommt zuletzt_von nicht mal als
    Parameter -- kann es also gar nicht auswerten."""
    import inspect

    sig = inspect.signature(_entscheide)
    assert "zuletzt_von" not in sig.parameters


# ── Regel b: kein Signal -> unbekannt, NIE die wahrscheinlichere Zuordnung ─

def test_signalloser_artikel_wird_unbekannt_nicht_geraten(db):
    _fuelle(db, [("c1", None, None, "Gabriel Gschaider")])
    ergebnis = zuordnen(db)
    assert ergebnis["verteilung"] == {"unbekannt": 1}
    assert ergebnis["ohne_signal"] == 1


def test_unbekanntes_projekt_faellt_nie_an_gabriel_obwohl_er_meistschreiber_ist(db):
    """Mischung: viele Gabriel-committete, signallose Artikel -- keiner darf
    aus reiner Mehrheit an gabriel fallen."""
    zeilen = [(f"d{i}", None, "irgendein-unbekanntes-repo", "Gabriel Gschaider") for i in range(20)]
    _fuelle(db, zeilen)
    ergebnis = zuordnen(db)
    assert ergebnis["verteilung"] == {"unbekannt": 20}
    assert ergebnis["mittlere_sicherheit"] == 0.0


# ── Die Leiter, Stufe fuer Stufe ───────────────────────────────────────────

@pytest.mark.parametrize(
    "sphaere,projekt,erwartet,sicherheit",
    [
        ("andreas", None, "andreas", 0.95),
        ("gabriel", None, "gabriel", 0.95),
        (None, "Dr.-Unterweger", "andreas", 0.90),
        (None, "gabriel-claude", "gabriel", 0.90),
        (None, "digital-retina", "gabriel", 0.75),
        ("frank_v0_1", "irgendwas", "gabriel", 0.75),
        (None, "clay-global-research-entity", "gemeinsam", 0.60),
        ("clayverse", None, "gemeinsam", 0.60),
        (None, None, "unbekannt", 0.0),
        (None, "voellig-unbekanntes-repo", "unbekannt", 0.0),
    ],
)
def test_leiter_stufen(sphaere, projekt, erwartet, sicherheit):
    gehoert, _grund, s = _entscheide(sphaere, projekt)
    assert gehoert == erwartet
    assert s == sicherheit


def test_sphaere_schlaegt_projekt_stufe1_vor_stufe2(db):
    """sphaere=andreas ausdruecklich gesetzt gewinnt gegen ein gabriel-Projekt."""
    gehoert, _grund, sicherheit = _entscheide("andreas", "gabriel-claude")
    assert gehoert == "andreas"
    assert sicherheit == 0.95


# ── bestand() -- Sitzungsvorspann-Zahlen ───────────────────────────────────

def test_bestand_zaehlt_eigene_und_gemeinsame_getrennt(db):
    _fuelle(
        db,
        [
            ("e1", "andreas", None, "x"),
            ("e2", "andreas", None, "x"),
            ("e3", None, "clay-global-research-entity", "x"),
        ],
    )
    zuordnen(db)
    b = bestand(db, "andreas")
    assert b.get("andreas") == 2
    assert b.get("gemeinsam") == 1


def test_bestand_ohne_tabelle_gibt_leeres_dict_statt_zu_werfen(tmp_path):
    """Tabelle entityos_artikel_zuordnung existiert noch nicht -- bestand()
    darf nicht werfen, sondern liefert einen leeren Befund."""
    frisch = UnifiedDB(tmp_path / "frisch.db")
    try:
        assert bestand(frisch, "gabriel") == {}
    finally:
        frisch.close()


# ── nur_zaehlen darf nicht schreiben ────────────────────────────────────────

def test_nur_zaehlen_schreibt_nichts_in_die_zuordnungstabelle(db):
    _fuelle(db, [("f1", "andreas", None, "x")])
    zuordnen(db, nur_zaehlen=True)
    n = db.db.execute("SELECT COUNT(*) n FROM entityos_artikel_zuordnung").fetchone()["n"]
    assert n == 0
