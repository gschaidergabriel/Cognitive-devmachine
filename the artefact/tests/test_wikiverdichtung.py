"""Tests fuer clayverse/wikiverdichtung.py -- viele Baunotizen zu wenigen Artikeln.

Deckt die drei Regeln aus dem Modulkopf konkret ab: Verdichtung schrumpft
(Regel 1), jede Aussage braucht einen zeichengenauen Beleg in GENAU der
angegebenen Quelle (Regel 2, gegen erfundene Aussagen), und eine erschoepfte
Bahn wird nicht heimlich durch eine selbst geschriebene Vorlage ersetzt
(Regel 3 aus bahnen.py).
"""
from __future__ import annotations

import json

import pytest

from clayverse import wikiverdichtung as wv
from clayverse.bahnen import BahnErschoepft
from clayverse.store import UnifiedDB


@pytest.fixture
def db(tmp_path):
    d = UnifiedDB(tmp_path / "unified.db")
    d.db.executescript(
        """
        CREATE TABLE IF NOT EXISTS artikel(
            id TEXT PRIMARY KEY, art TEXT NOT NULL, titel TEXT, quelle TEXT,
            quell_hash TEXT, datum TEXT, metadaten TEXT, belegt INTEGER,
            erzeugt_am TEXT, wirt TEXT, zuletzt_von TEXT, von_quelle TEXT,
            status TEXT, konfidenz REAL, projekt TEXT, projekt_art TEXT,
            sphaere TEXT,
            herkunft TEXT DEFAULT 'gemessen' CHECK (herkunft IN ('gemessen','nutzer'))
        )
        """
    )
    yield d
    d.close()


def _baunotiz(db, id_, *, tag="2026-08-18", uhrzeit="10:00:00", betreff, wieso=""):
    meta = {"wieso": wieso, "betreff": betreff, "herkunft": "git-commit"}
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO artikel(id,art,titel,datum,metadaten,von_quelle,herkunft) "
            "VALUES(?,?,?,?,?,?,?)",
            (id_, "baunotiz", betreff, f"{tag}T{uhrzeit}+00:00",
             json.dumps(meta, ensure_ascii=False), "git-commit", "gemessen"),
        )


def _verdichtungen(db):
    return db.db.execute("SELECT * FROM artikel WHERE art='verdichtung'").fetchall()


# ── Mechanischer Pfad: keine Bahn, keine Woertlichkeitspruefung noetig ─────

def test_mechanische_gruppe_ruft_keine_bahn_auf(db, monkeypatch):
    def _explodiert(self, *a, **kw):
        raise AssertionError("Bahnrouter.rufe haette hier nicht laufen duerfen")
    monkeypatch.setattr(wv.Bahnrouter, "rufe", _explodiert)

    for i in range(4):
        _baunotiz(db, f"b{i}", betreff=f"claycode supervisor: sync {i}", wieso="")

    ergebnis = wv.verdichten(db)
    assert ergebnis["mechanisch"] == 1
    assert ergebnis["narrativ"] == 0
    zeilen = _verdichtungen(db)
    assert len(zeilen) == 1
    assert zeilen[0]["status"] == "mechanisch"
    assert zeilen[0]["herkunft"] == "gemessen"  # CHECK-Constraint eingehalten


def test_gruppen_unter_mindestgroesse_bleiben_unverdichtet(db):
    _baunotiz(db, "x1", betreff="einzelding: nur eine notiz")
    _baunotiz(db, "x2", betreff="einzelding: noch eine")  # 2 < MIN_GRUPPENGROESSE=3
    ergebnis = wv.verdichten(db)
    assert ergebnis["gruppen"] == 0
    assert ergebnis["notizen_ohne_gruppe"] == 2
    assert len(_verdichtungen(db)) == 0


# ── Narrativer Pfad + Woertlichkeitspruefung ────────────────────────────────

_LANGER_TEXT_A = (
    "Cross-user-Leck gefunden: memory_tabelle hatte keine Spalte user_id, "
    "memory_suche() filterte gar nicht -- Andreas bekam Gabriels private "
    "Eintraege woertlich zurueck. " + ("Zusatztext fuer Laenge. " * 15)
)
_LANGER_TEXT_B = (
    "77 rote Tests durch executescript() in sicherstellen() -- committet "
    "implizit, reisst die laufende Transaktion auseinander. " + ("Zusatztext. " * 15)
)


def _fake_rufe_factory(antwort_text: str, bahn="test_bahn", modell="test_modell"):
    def _fake(self, prozess, auftrag, *, system=None, max_token=800, timeout=60):
        return {"prozess": prozess, "bahn": bahn, "modell": modell, "text": antwort_text,
                "token": 42, "ms": 1.0, "benutzt_heute": 1, "deckel": None, "verworfene_bahnen": []}
    return _fake


def test_narrativ_verwirft_aussage_mit_beleg_aus_falscher_quelle(db, monkeypatch):
    _baunotiz(db, "n1", betreff="vorgang: leck gefunden", wieso=_LANGER_TEXT_A)
    _baunotiz(db, "n2", betreff="vorgang: tests rot", wieso=_LANGER_TEXT_B)
    _baunotiz(db, "n3", betreff="vorgang: dritte notiz", wieso=_LANGER_TEXT_A)

    # Eine Aussage ist echt belegt (Beleg steht woertlich in n1), die zweite
    # gibt einen Beleg an, der bei n2 angegeben wird, aber gar nicht in n2
    # vorkommt (er stammt tatsaechlich aus n1) -- muss verworfen werden.
    antwort = json.dumps({
        "titel": "Testtitel",
        "claims": [
            {"text": "Cross-user-Leck gefunden", "beleg": "Cross-user-Leck gefunden: memory_tabelle hatte keine Spalte user_id",
             "quelle_id": "n1"},
            {"text": "Erfundene Aussage", "beleg": "Cross-user-Leck gefunden: memory_tabelle hatte keine Spalte user_id",
             "quelle_id": "n2"},
        ],
    }, ensure_ascii=False)
    monkeypatch.setattr(wv.Bahnrouter, "rufe", _fake_rufe_factory(antwort))

    ergebnis = wv.verdichten(db)
    assert ergebnis["narrativ"] == 1
    assert ergebnis["claims_geprueft"] == 2
    assert ergebnis["claims_verworfen"] == 1

    zeile = _verdichtungen(db)[0]
    meta = json.loads(zeile["metadaten"])
    assert "Cross-user-Leck gefunden" in meta["text"]
    assert "[n1]" in meta["text"]
    assert "Erfundene Aussage" not in meta["text"]
    assert meta["claims_verworfen"] == 1


def test_narrativ_behaelt_zeichengenau_belegte_aussage(db, monkeypatch):
    _baunotiz(db, "n1", betreff="vorgang: leck gefunden", wieso=_LANGER_TEXT_A)
    _baunotiz(db, "n2", betreff="vorgang: tests rot", wieso=_LANGER_TEXT_B)
    _baunotiz(db, "n3", betreff="vorgang: dritte notiz", wieso=_LANGER_TEXT_A)

    antwort = json.dumps({
        "titel": "77 rote Tests durch implizites Commit",
        "claims": [
            {"text": "executescript() in sicherstellen() committet implizit und machte 77 Tests rot",
             "beleg": "77 rote Tests durch executescript() in sicherstellen()", "quelle_id": "n2"},
        ],
    }, ensure_ascii=False)
    monkeypatch.setattr(wv.Bahnrouter, "rufe", _fake_rufe_factory(antwort))

    ergebnis = wv.verdichten(db)
    assert ergebnis["claims_verworfen"] == 0
    zeile = _verdichtungen(db)[0]
    meta = json.loads(zeile["metadaten"])
    assert "77 Tests rot" in meta["text"]
    assert meta["quellnotizen"] == ["n1", "n2", "n3"]


def test_kompression_schrumpft_gegenueber_den_quellen(db, monkeypatch):
    _baunotiz(db, "n1", betreff="vorgang: leck gefunden", wieso=_LANGER_TEXT_A)
    _baunotiz(db, "n2", betreff="vorgang: tests rot", wieso=_LANGER_TEXT_B)
    _baunotiz(db, "n3", betreff="vorgang: dritte notiz", wieso=_LANGER_TEXT_A)
    antwort = json.dumps({"titel": "kurz", "claims": []}, ensure_ascii=False)
    monkeypatch.setattr(wv.Bahnrouter, "rufe", _fake_rufe_factory(antwort))

    ergebnis = wv.verdichten(db)
    assert ergebnis["zeichen_artikel"] < ergebnis["zeichen_quellen"]
    assert ergebnis["kompression_gesamt"] > 1


def test_kein_json_wird_ehrlich_benannt_nicht_erfunden(db, monkeypatch):
    _baunotiz(db, "n1", betreff="vorgang: eins", wieso=_LANGER_TEXT_A)
    _baunotiz(db, "n2", betreff="vorgang: zwei", wieso=_LANGER_TEXT_B)
    _baunotiz(db, "n3", betreff="vorgang: drei", wieso=_LANGER_TEXT_A)
    monkeypatch.setattr(wv.Bahnrouter, "rufe", _fake_rufe_factory("das ist kein JSON, nur Prosa"))

    ergebnis = wv.verdichten(db)
    assert ergebnis["narrativ"] == 1
    zeile = _verdichtungen(db)[0]
    assert "kein JSON" in zeile["titel"]
    meta = json.loads(zeile["metadaten"])
    assert meta["claims_geprueft"] == 0


def test_bahn_erschoepft_erzeugt_keinen_artikel_diesen_lauf(db, monkeypatch):
    _baunotiz(db, "n1", betreff="vorgang: eins", wieso=_LANGER_TEXT_A)
    _baunotiz(db, "n2", betreff="vorgang: zwei", wieso=_LANGER_TEXT_B)
    _baunotiz(db, "n3", betreff="vorgang: drei", wieso=_LANGER_TEXT_A)

    def _erschoepft(self, prozess, auftrag, **kw):
        raise BahnErschoepft("keine Bahn frei")
    monkeypatch.setattr(wv.Bahnrouter, "rufe", _erschoepft)

    ergebnis = wv.verdichten(db)
    assert ergebnis["bahn_erschoepft"] == 1
    assert len(_verdichtungen(db)) == 0
    assert ergebnis["fehler"]


# ── Hypothese/Gegenhypothese: mechanisch, nie vom Modell erfragt ──────────

def test_hypothese_nur_bei_woertlichem_zeilenanfang_gesetzt(db, monkeypatch):
    text_mit_hyp = "Befund X.\nHypothese: der Cache ist die Ursache\nWeiterer Text. " + ("y " * 60)
    _baunotiz(db, "n1", betreff="vorgang: eins", wieso=text_mit_hyp)
    _baunotiz(db, "n2", betreff="vorgang: zwei", wieso=_LANGER_TEXT_B)
    _baunotiz(db, "n3", betreff="vorgang: drei", wieso=_LANGER_TEXT_A)
    antwort = json.dumps({"titel": "t", "claims": []}, ensure_ascii=False)
    monkeypatch.setattr(wv.Bahnrouter, "rufe", _fake_rufe_factory(antwort))

    wv.verdichten(db)
    meta = json.loads(_verdichtungen(db)[0]["metadaten"])
    assert meta["hypothese"] == "der Cache ist die Ursache"
    assert meta["gegenhypothese"] is None


# ── Idempotenz ──────────────────────────────────────────────────────────────

def test_zweiter_lauf_ohne_aenderung_erzeugt_keine_duplikate(db, monkeypatch):
    for i in range(4):
        _baunotiz(db, f"b{i}", betreff=f"claycode supervisor: sync {i}", wieso="")
    monkeypatch.setattr(wv.Bahnrouter, "rufe",
                         lambda *a, **kw: (_ for _ in ()).throw(AssertionError("keine Bahn erwartet")))

    r1 = wv.verdichten(db)
    assert r1["artikel_neu"] == 1
    r2 = wv.verdichten(db)
    assert r2["artikel_neu"] == 0
    assert r2["uebersprungen"] == 1
    assert len(_verdichtungen(db)) == 1


def test_neue_quellnotiz_aendert_hash_und_wird_neu_verdichtet(db, monkeypatch):
    for i in range(4):
        _baunotiz(db, f"b{i}", betreff=f"claycode supervisor: sync {i}", wieso="")
    monkeypatch.setattr(wv.Bahnrouter, "rufe",
                         lambda *a, **kw: (_ for _ in ()).throw(AssertionError("keine Bahn erwartet")))
    wv.verdichten(db)
    _baunotiz(db, "b4", betreff="claycode supervisor: sync 4", wieso="")
    r2 = wv.verdichten(db)
    assert r2["artikel_aktualisiert"] == 1
    assert len(_verdichtungen(db)) == 1  # dieselbe id, kein Duplikat
    meta = json.loads(_verdichtungen(db)[0]["metadaten"])
    assert "b4" in meta["quellnotizen"]


def test_leere_db_ohne_artikel_tabelle_tut_nichts(tmp_path):
    d = UnifiedDB(tmp_path / "leer.db")
    ergebnis = wv.verdichten(d)
    assert ergebnis["gruppen"] == 0
    d.close()


def test_thema_erkennt_maschinelles_muster_und_faengt_menschliche_titel_auf():
    assert wv._thema("claycode supervisor: sync X") == "claycode supervisor"
    assert wv._thema("receipt(go): bind PR810") == "receipt(go)"
    assert wv._thema("Zero weiss jetzt, mit WEM es spricht") == "vorgang"
    assert wv._thema("") == "vorgang"


def test_tag_utc_normalisiert_verschiedene_offsets():
    assert wv._tag_utc("2026-08-18T23:30:00+07:00") == "2026-08-18"
    assert wv._tag_utc("2026-08-18T07:00:00+00:00") == "2026-08-18"
    assert wv._tag_utc(None) is None
    assert wv._tag_utc("nicht-lesbar") is None
