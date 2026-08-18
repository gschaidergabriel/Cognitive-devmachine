"""Tests fuer clayverse/profile.py -- die zwei Menschenprofile.

Zwei Regeln stehen im Fokus:
  d) profil() fuer gabriel enthaelt NICHTS Privates von andreas, und umgekehrt.
     gemeinsam ist absichtlich geteilt -- kein Leck.
  f) profil() ist eine LESEFUNKTION. Sie darf keine Transaktion aufreissen,
     indem sie executescript() aufruft (das committet implizit). Gemessen:
     77 rote Tests, als genau das passierte.
"""
from __future__ import annotations

import pytest

from clayverse import profile
from clayverse.store import UnifiedDB


@pytest.fixture
def db(tmp_path):
    d = UnifiedDB(tmp_path / "unified.db")
    yield d
    d.close()


@pytest.fixture
def db_grundstock(db):
    profile.grundstock(db)
    return db


# ── Regel d: keine Cross-user-Lecks, gemeinsam ist kein Leck ──────────────

def test_gabriel_profil_enthaelt_kein_privates_andreas_feld(db_grundstock):
    p = profile.profil(db_grundstock, "gabriel")
    werte = [v["wert"] for v in p["felder"].values()]
    # andreas' private Mail (herkunft=eigner) darf in gabriels felder nicht auftauchen
    assert "genuinos@gmail.com" not in werte
    assert "Dr. Andreas Unterweger" not in werte


def test_andreas_profil_enthaelt_kein_privates_gabriel_feld(db_grundstock):
    p = profile.profil(db_grundstock, "andreas")
    werte = [v["wert"] for v in p["felder"].values()]
    assert "structured.thinking.gschaider@gmail.com" not in werte
    assert "Gabriel Gschaider" not in werte


def test_gemeinsam_ist_bei_beiden_sichtbar_das_ist_kein_leck(db_grundstock):
    g = profile.profil(db_grundstock, "gabriel")
    a = profile.profil(db_grundstock, "andreas")
    assert "institut" in g["gemeinsam"]
    assert "institut" in a["gemeinsam"]
    assert g["gemeinsam"]["institut"] == a["gemeinsam"]["institut"]


def test_mit_gemeinsam_false_liefert_kein_geteiltes_feld(db_grundstock):
    p = profile.profil(db_grundstock, "gabriel", mit_gemeinsam=False)
    assert p["gemeinsam"] == {}


def test_felder_sind_strikt_nach_user_id_gefiltert(db_grundstock):
    """Direkter DB-Beleg: die felder-Abfrage in profil() ist nach user_id
    parametrisiert -- kein Feld eines anderen user_id landet drin."""
    p = profile.profil(db_grundstock, "gabriel")
    for feld in p["felder"]:
        row = db_grundstock.db.execute(
            "SELECT user_id FROM entityos_profil WHERE feld=? AND user_id='gabriel'", (feld,)
        ).fetchone()
        assert row is not None


# ── Regel f: profil() darf keine Transaktion aufreissen ───────────────────

def test_profil_ohne_tabellen_reisst_laufende_transaktion_nicht_auseinander(db):
    """Frische DB, entityos_profil existiert noch nicht. profil() muss den
    'Tabellen fehlen'-Pfad nehmen (try/except SELECT), NICHT executescript()
    aufrufen -- sonst committet es die laufende Transaktion implizit weg."""
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO users(user_id,display_name) VALUES('sentinel','Sentinel')"
        )
        assert db.db.in_transaction, "Transaktion sollte laufen"
        ergebnis = profile.profil(db, "gabriel")
        assert ergebnis["hinweis"] == "Profiltabellen noch nicht angelegt."
        assert db.db.in_transaction, (
            "profil() hat die laufende Transaktion aufgerissen -- das ist "
            "genau der Fehler, der 77 Tests rot gemacht hat"
        )
    # Transaktion normal zu Ende gebracht -- Insert ist committet.
    row = db.db.execute(
        "SELECT display_name FROM users WHERE user_id='sentinel'"
    ).fetchone()
    assert row["display_name"] == "Sentinel"


def test_profil_mit_bestehenden_tabellen_reisst_transaktion_auch_nicht_auf(db_grundstock):
    """Gleiche Probe, aber diesmal SIND die Tabellen schon da -- profil() geht
    dann den vollen Lesepfad (mehrere SELECTs), darf aber ebenfalls nichts
    committen."""
    with db_grundstock.tx() as sql:
        sql.execute(
            "INSERT INTO users(user_id,display_name) VALUES('sentinel2','Sentinel2')"
        )
        assert db_grundstock.db.in_transaction
        p = profile.profil(db_grundstock, "gabriel")
        assert p["felder"]  # echter Lesepfad, nicht der Fallback
        assert db_grundstock.db.in_transaction


# ── rechner: Wirt-Zugehoerigkeit im Profil (nutzt entityos_wirte.gehoert_zu) ─

def test_profil_zeigt_eigene_und_fremde_rechner_korrekt_markiert(db_grundstock):
    from clayverse import wirte

    wirte._sicherstellen(db_grundstock)
    with db_grundstock.tx() as sql:
        sql.execute(
            "INSERT INTO entityos_wirte(wirt,gehoert_zu,erste_sichtung,zuletzt_gesehen,gesund) "
            "VALUES(?,?,?,?,?)",
            ("ai-core-node", "gabriel", 0, 0, 1),
        )
        sql.execute(
            "INSERT INTO entityos_wirte(wirt,gehoert_zu,erste_sichtung,zuletzt_gesehen,gesund) "
            "VALUES(?,?,?,?,?)",
            ("andreas-maco", "andreas", 0, 0, 1),
        )
    p = profile.profil(db_grundstock, "gabriel")
    eigen = {r["wirt"]: r["meiner"] for r in p["rechner"]}
    assert eigen["ai-core-node"] is True
    assert eigen["andreas-maco"] is False


# ── sitzungsvorspann ────────────────────────────────────────────────────────

def test_sitzungsvorspann_nennt_namen_und_verweist_auf_den_anderen(db_grundstock):
    text = profile.sitzungsvorspann(db_grundstock, "gabriel", "session:gabriel", platz=1)
    assert "Gabriel Gschaider" in text
    assert "andreas" in text
    assert "session:gabriel" in text
    assert "clerk-verifiziert" in text


def test_sitzungsvorspann_andreas_verweist_auf_gabriel(db_grundstock):
    text = profile.sitzungsvorspann(db_grundstock, "andreas", "session:andreas")
    assert "Dr. Andreas Unterweger" in text
    assert "gabriel" in text
