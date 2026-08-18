"""Tests fuer clayverse/profil_verdichtung.py -- autonome Profilverdichtung.

Regel c) im Fokus: ERKLAERTES WIRD NIE UEBERSCHRIEBEN (herkunft eigner /
iar.frank.ink ist unantastbar), und die Verdichtung darf NUR in den
Namensraum gemessen_* schreiben -- alles andere ist ein Programmierfehler
und muss RAISEN, nicht schweigen.

Regel g) im Fokus: die Rechner-Sonde nutzt die Spalte entityos_wirte.gehoert_zu.
Ein Tippfehler hier (frueher: 'gehoert') liess die Sonde bei voller, korrekter
Tabelle "nichts gemessen" melden -- ein stiller Fehler mit Datenverlust-Optik.
"""
from __future__ import annotations

import time

import pytest

from clayverse import profile, profil_verdichtung, wirte
from clayverse.store import UnifiedDB


@pytest.fixture
def db(tmp_path):
    d = UnifiedDB(tmp_path / "unified.db")
    profile.sicherstellen(d)
    yield d
    d.close()


def _setze_erklaert(db, user_id, feld, wert, herkunft):
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO entityos_profil(user_id,feld,wert,herkunft,beleg,erfasst) "
            "VALUES(?,?,?,?,?,?)",
            (user_id, feld, wert, herkunft, "test", time.time()),
        )


# ── Regel c1: eigner/iar.frank.ink sind unantastbar ────────────────────────

@pytest.mark.parametrize("herkunft", ["eigner", "iar.frank.ink"])
def test_schreibe_verweigert_ueberschreiben_von_unantastbarer_herkunft(db, herkunft):
    _setze_erklaert(db, "gabriel", "gemessen_test", "urspruenglicher_wert", herkunft)
    erfolg = profil_verdichtung._schreibe(db, "gabriel", "gemessen_test", "neuer_wert", "beleg")
    assert erfolg is False
    row = db.db.execute(
        "SELECT wert, herkunft FROM entityos_profil WHERE user_id='gabriel' AND feld='gemessen_test'"
    ).fetchone()
    assert row["wert"] == "urspruenglicher_wert"
    assert row["herkunft"] == herkunft


def test_schreibe_darf_gemessen_herkunft_ueberschreiben(db):
    """Gegenprobe: eine vorherige eigene Messung (herkunft=gemessen) darf
    aktualisiert werden -- nur eigner/iar.frank.ink sind gesperrt."""
    _setze_erklaert(db, "gabriel", "gemessen_test", "alt", "gemessen")
    erfolg = profil_verdichtung._schreibe(db, "gabriel", "gemessen_test", "neu", "beleg2")
    assert erfolg is True
    row = db.db.execute(
        "SELECT wert FROM entityos_profil WHERE user_id='gabriel' AND feld='gemessen_test'"
    ).fetchone()
    assert row["wert"] == "neu"


# ── Regel c2: nur gemessen_* -- alles andere RAISED ────────────────────────

def test_schreibe_ausserhalb_namensraum_raised(db):
    with pytest.raises(ValueError, match="gemessen_"):
        profil_verdichtung._schreibe(db, "gabriel", "name", "geraten", "beleg")


def test_schreibe_leerer_feldname_raised(db):
    with pytest.raises(ValueError):
        profil_verdichtung._schreibe(db, "gabriel", "", "x", "beleg")


# ── Regel g: entityos_wirte.gehoert_zu ist die richtige Spalte ────────────

def test_rechner_sonde_findet_seinen_eigenen_wirt(db):
    wirte._sicherstellen(db)
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO entityos_wirte(wirt,gehoert_zu,erste_sichtung,zuletzt_gesehen,gesund) "
            "VALUES(?,?,?,?,?)",
            ("ai-core-node", "gabriel", 0, 0, 1),
        )
    treffer = profil_verdichtung._rechner(db, "gabriel")
    assert treffer is not None
    feld, wert, beleg = treffer
    assert feld == "gemessen_rechner"
    assert "ai-core-node" in wert
    assert "gehoert_zu" in beleg


def test_rechner_sonde_ignoriert_fremde_wirte(db):
    wirte._sicherstellen(db)
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO entityos_wirte(wirt,gehoert_zu,erste_sichtung,zuletzt_gesehen,gesund) "
            "VALUES(?,?,?,?,?)",
            ("andreas-maco", "andreas", 0, 0, 1),
        )
    assert profil_verdichtung._rechner(db, "gabriel") is None


def test_rechner_sonde_ohne_tabelle_ist_still_kein_fehler(db):
    assert profil_verdichtung._rechner(db, "gabriel") is None


def test_verdichten_traegt_rechner_wirklich_ein_end_zu_end(db):
    """Regressionstest fuer den stillen Bug: verdichten() muss die Sonde in
    'geschrieben' fuehren, NICHT in 'nichts_gemessen' oder 'fehler', wenn ein
    Wirt korrekt zugeordnet in der Tabelle steht."""
    wirte._sicherstellen(db)
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO entityos_wirte(wirt,gehoert_zu,erste_sichtung,zuletzt_gesehen,gesund) "
            "VALUES(?,?,?,?,?)",
            ("ai-core-node", "gabriel", 0, 0, 1),
        )
    bericht = profil_verdichtung.verdichten(db, user_ids=("gabriel",))
    assert "gemessen_rechner" in bericht["gabriel"]["geschrieben"]
    assert not any(f.startswith("rechner:") for f in bericht["gabriel"]["fehler"])
    row = db.db.execute(
        "SELECT wert FROM entityos_profil WHERE user_id='gabriel' AND feld='gemessen_rechner'"
    ).fetchone()
    assert "ai-core-node" in row["wert"]


# ── Ausfallsicherheit: eine kaputte Sonde darf die anderen nicht mitreissen ─

def test_eine_werfende_sonde_wird_genannt_nicht_verschluckt(db, monkeypatch):
    def kaputt(db, user_id):
        raise RuntimeError("absichtlich kaputt")

    monkeypatch.setattr(profil_verdichtung, "SONDEN", (kaputt,))
    bericht = profil_verdichtung.verdichten(db, user_ids=("gabriel",))
    assert bericht["gabriel"]["fehler"]
    assert "kaputt" in bericht["gabriel"]["fehler"][0]
    assert bericht["gabriel"]["geschrieben"] == []
