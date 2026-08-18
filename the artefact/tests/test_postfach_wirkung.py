"""Senden ist eine Wirkung: Urteil aus dem Tor, Beleg in der UnifiedDB.

⚠️ Kein Test hier darf eine echte Mail verschicken. SMTP und IMAP sind
weggemockt; wer die Mocks entfernt, bekommt beim naechsten Lauf ein leeres
Postfach beim Empfaenger und keinen Hinweis darauf.

Der zweite Zweck dieser Datei ist die Produktgesetz-Sperre: nach einem Versand
darf das Passwort NIRGENDS in der Datenbankdatei stehen -- weder in der
Effektzeile noch im Beleg noch in einem Ausnahmetext.
"""
import pytest

import clayverse.postfach as postfach
from clayverse.identity import IdentityRouter
from clayverse.postfach import PostfachFehler, Zugaenge, Zugang, senden
from clayverse.store import UnifiedDB

GEHEIM = "GEHEIM-SMTP-PASSWORT-3f9d"
INHALT = "Innentext-der-niemals-in-die-Datenbank-gehoert-8a7c"


def _zugaenge() -> Zugaenge:
    return Zugaenge(
        postfaecher={
            "gabriel": Zugang("gabriel@frank.ink", GEHEIM),
            "andreas": Zugang("andreas@frank.ink", GEHEIM),
        },
        imap_host="mail.frank.ink", imap_port=993,
        smtp_host="mail.frank.ink", smtp_port=587,
    )


def _db(tmp_path) -> UnifiedDB:
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _stumm_schalten(monkeypatch, *, smtp_fehler: Exception | None = None):
    """Netzwerk aus. Alles, was hier gerufen wird, wird protokolliert."""
    gerufen = {"smtp": [], "sent": 0}

    def falsches_smtp(zugaenge, zugang, empfaenger, roh):
        gerufen["smtp"].append((zugang.adresse, tuple(empfaenger), len(roh)))
        if smtp_fehler is not None:
            raise smtp_fehler

    def falsches_ablegen(zugaenge, zugang, roh):
        gerufen["sent"] += 1
        return True

    monkeypatch.setattr(postfach, "_smtp_senden", falsches_smtp)
    monkeypatch.setattr(postfach, "_in_sent_ablegen", falsches_ablegen)
    return gerufen


def _dateiinhalt(db: UnifiedDB) -> bytes:
    """Die ganze Datenbank als Bytes -- samt WAL, sonst prueft man am Fleck vorbei."""
    roh = db.path.read_bytes()
    wal = db.path.with_name(db.path.name + "-wal")
    if wal.exists():
        roh += wal.read_bytes()
    return roh


def test_gesendete_mail_bekommt_urteil_und_beleg(tmp_path, monkeypatch):
    db = _db(tmp_path)
    gerufen = _stumm_schalten(monkeypatch)
    try:
        ergebnis = senden(
            db, _zugaenge(), user_id="gabriel", session_id="session:gabriel",
            an="andreas@frank.ink", betreff="Pruefsendung", inhalt=INHALT,
        )
        assert ergebnis["ok"] is True
        assert ergebnis["urteil"] == "VERIFIED"
        assert gerufen["smtp"] == [("gabriel@frank.ink", ("andreas@frank.ink",), gerufen["smtp"][0][2])]

        wirkung = db.db.execute(
            "SELECT capability,status,user_id FROM effects WHERE effect_id=?",
            (ergebnis["effect_id"],),
        ).fetchone()
        assert wirkung["capability"] == "postfach.senden"
        assert wirkung["status"] == "VERIFIED"
        assert wirkung["user_id"] == "gabriel"

        # Die Wirkung haengt in der Kausalkette wie jede andere auch.
        kausal = db.db.execute(
            "SELECT causal_id,credit FROM causal_episodes WHERE effect_id=?",
            (ergebnis["effect_id"],),
        ).fetchone()
        assert kausal is not None and kausal["credit"] == 1.0

        beleg = db.db.execute(
            "SELECT * FROM entityos_postfach_belege WHERE beleg_id=?",
            (ergebnis["beleg_id"],),
        ).fetchone()
        assert beleg["empfaenger"] == "andreas@frank.ink"
        assert beleg["betreff"] == "Pruefsendung"
        assert beleg["urteil"] == "VERIFIED"
        assert beleg["effect_id"] == ergebnis["effect_id"]
        assert beleg["causal_id"] == kausal["causal_id"]
        assert len(beleg["inhalt_sha256"]) == 64
        assert beleg["inhalt_bytes"] > 0
    finally:
        db.close()


def test_der_mailtext_selbst_steht_nirgends_in_der_datenbank(tmp_path, monkeypatch):
    """Nur die Pruefsumme gehoert in den Beleg, nicht der Inhalt."""
    db = _db(tmp_path)
    _stumm_schalten(monkeypatch)
    try:
        senden(db, _zugaenge(), user_id="gabriel", session_id="session:gabriel",
               an="andreas@frank.ink", betreff="Pruefsendung", inhalt=INHALT)
        assert INHALT.encode() not in _dateiinhalt(db)
    finally:
        db.close()


def test_kein_passwort_gelangt_in_einen_beleg(tmp_path, monkeypatch):
    db = _db(tmp_path)
    _stumm_schalten(monkeypatch)
    try:
        senden(db, _zugaenge(), user_id="gabriel", session_id="session:gabriel",
               an="andreas@frank.ink", betreff="Pruefsendung", inhalt=INHALT)
        assert GEHEIM.encode() not in _dateiinhalt(db)
        for tabelle in ("effects", "causal_episodes", "entityos_postfach_belege"):
            zeilen = db.db.execute(f"SELECT * FROM {tabelle}").fetchall()
            for zeile in zeilen:
                assert GEHEIM not in " ".join(str(w) for w in tuple(zeile))
    finally:
        db.close()


def test_gescheiterter_versand_wird_als_fehlschlag_verbucht_ohne_passwort(tmp_path, monkeypatch):
    """Die Serverantwort ist fremder Text -- sie kann alles enthalten.

    Der Fehlschlag muss trotzdem eine Spur hinterlassen: ein Versuch ohne Spur
    wird spaeter fuer "wurde nie versucht" gehalten.
    """
    db = _db(tmp_path)
    _stumm_schalten(monkeypatch, smtp_fehler=PostfachFehler(f"SMTP sagte: {GEHEIM}"))
    try:
        with pytest.raises(PostfachFehler) as fehler:
            senden(db, _zugaenge(), user_id="gabriel", session_id="session:gabriel",
                   an="andreas@frank.ink", betreff="Pruefsendung", inhalt=INHALT)
        # Die Ausnahme reicht der Test bewusst durch -- geprueft wird, was
        # DAUERHAFT wird: Effektzeile und Beleg.
        assert str(fehler.value)

        wirkung = db.db.execute(
            "SELECT status,outcome FROM effects WHERE capability='postfach.senden'"
        ).fetchone()
        assert wirkung["status"] == "FAILED"
        assert GEHEIM not in str(wirkung["outcome"])

        beleg = db.db.execute("SELECT urteil,betreff FROM entityos_postfach_belege").fetchone()
        assert beleg["urteil"] == "FAILED"
        assert beleg["betreff"] == "Pruefsendung"
        assert GEHEIM.encode() not in _dateiinhalt(db)
    finally:
        db.close()


def test_ohne_angeschlossenen_wirker_wird_verweigert_statt_behauptet(tmp_path):
    """Wie bei der EntityOS-Bruecke: kein Wirker, kein Erfolg -- ein DENIED mit Grund."""
    from clayverse.effects import EffectGate, EffectRequest

    db = _db(tmp_path)
    try:
        gate = EffectGate(db)
        effect_id, ergebnis = gate.execute(EffectRequest(
            user_id="gabriel", session_id="session:gabriel",
            capability="postfach.senden", target="postfach:senden:niemand@example.org",
        ))
        assert ergebnis["ok"] is False
        assert ergebnis["reason"] == "postfach_unavailable"
        status = db.db.execute(
            "SELECT status FROM effects WHERE effect_id=?", (effect_id,)
        ).fetchone()[0]
        assert status == "DENIED"
    finally:
        db.close()


def test_postfach_senden_bleibt_ausserhalb_der_modellwege():
    """Mail ist ein Weg fuer den Menschen, nicht fuer Zero.

    Das Tor kennt die Faehigkeit, die Modellwege duerfen sie nicht anfordern --
    und sie darf auch nicht im Weltzustand auftauchen, den Zero liest.
    """
    from clayverse.autonomy import EFFECT_CAPABILITIES
    from clayverse.effects import EffectGate
    from clayverse.inference_protocol import ALLOWED_INFERENCE_EFFECTS

    assert "postfach.senden" in EffectGate.ALLOWED
    assert "postfach.senden" not in ALLOWED_INFERENCE_EFFECTS
    assert "postfach.senden" not in EFFECT_CAPABILITIES
    mcp = __import__("pathlib").Path(__file__).resolve().parents[1] / "clayverse" / "mcp_server.py"
    quelle = mcp.read_text(encoding="utf-8")
    assert 'capability not in {"entityos.exec", "state.noop"}' in quelle


def test_ungueltige_empfaenger_kommen_nicht_bis_zum_tor(tmp_path, monkeypatch):
    """Kopfzeilen-Einschleusung und Massenversand fallen vor der Wirkung durch."""
    db = _db(tmp_path)
    gerufen = _stumm_schalten(monkeypatch)
    try:
        for an in ("", "keine-adresse", "gut@example.org\nBcc: heimlich@example.org"):
            with pytest.raises(ValueError):
                senden(db, _zugaenge(), user_id="gabriel", session_id="session:gabriel",
                       an=an, betreff="x", inhalt="y")
        assert gerufen["smtp"] == []
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
    finally:
        db.close()
