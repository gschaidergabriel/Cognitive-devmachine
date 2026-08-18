"""Die Mailboxseite und die lesenden Wege daneben.

Zwei Dinge werden hier festgehalten, die beide schon einmal Geld gekostet
haetten:

1. Eine fehlende Oberflaeche faellt NICHT still auf eine andere zurueck. Sie
   gibt 503 mit klarer Meldung -- sonst sieht ein Bauproblem aus wie eine
   Designentscheidung.
2. Was nicht messbar ist, kommt als `null` zurueck. `ungelesen: 0` waere die
   Behauptung "keine ungelesene Mail"; ist das Postfach nur nicht erreichbar,
   ist das eine Luege mit Zahlenformat.

⚠️ Kein Test hier baut eine echte IMAP- oder SMTP-Verbindung auf: die
Zugangsdatei wird per ENTITYOS_POSTFACH_ENV auf einen Pfad gezeigt, den es
nicht gibt. Ohne das wuerde die Testsuite auf dem Wirt, auf dem die echte Datei
liegt, ins Netz greifen.
"""
import time

import pytest
from fastapi.testclient import TestClient

from clayverse.store import UnifiedDB
from clayverse.terminal_gateway import create_terminal_app

KARTE = {"clerk_g": "gabriel", "clerk_a": "andreas"}


class _Verifizierer:
    """Nimmt genau die Subjekte an, die es kennt -- sonst wie Clerk: Ablehnung."""

    def __init__(self, subjekt: str = "clerk_g"):
        self.subjekt = subjekt

    def verify(self, token):
        from clayverse.clerk_auth import AuthenticationError
        if token != "gutes-token":
            raise AuthenticationError("invalid Clerk session token")
        return {"sub": self.subjekt, "sid": "clerk_session_1", "exp": time.time() + 3600}


@pytest.fixture
def umgebung(tmp_path, monkeypatch):
    monkeypatch.setenv("ENTITYOS_WEB_ROOT", str(tmp_path / "web"))
    # Absichtlich ein Pfad, den es nicht gibt: keine Zugaenge, kein Netz.
    monkeypatch.setenv("ENTITYOS_POSTFACH_ENV", str(tmp_path / "kein-postfach.env"))
    return tmp_path


def _app(tmp_path, *, subjekt: str = "clerk_g", karte=None):
    db = UnifiedDB(tmp_path / "state" / "unified.db")
    app = create_terminal_app(
        db=db,
        clerk_map=KARTE if karte is None else karte,
        verifier=_Verifizierer(subjekt),
        state_root=tmp_path / "state",
        publishable_key="pk_test_postfach",
        frontend_api_url="https://clerk.invalid",
    )
    return db, app


def _lege_seite(tmp_path, relativ: str, inhalt: str) -> None:
    ziel = tmp_path / "web" / relativ
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(inhalt, encoding="utf-8")


# ── Die Seite ─────────────────────────────────────────────────────────────

def test_postfachseite_wird_aus_der_datei_geliefert(umgebung):
    _lege_seite(
        umgebung, "postfach/index.html",
        '<!doctype html><title>Mailbox</title>'
        '<script src="__CLERK_API__/x" data-clerk-publishable-key="__CLERK_PUBLISHABLE_KEY__"></script>',
    )
    db, app = _app(umgebung)
    try:
        with TestClient(app) as client:
            antwort = client.get("/postfach")
        assert antwort.status_code == 200
        assert "<title>Mailbox</title>" in antwort.text
        # Die Platzhalter werden server-seitig ersetzt, wie beim Chat.
        assert "__CLERK_API__" not in antwort.text
        assert "__CLERK_PUBLISHABLE_KEY__" not in antwort.text
        assert "https://clerk.invalid/x" in antwort.text
        assert "pk_test_postfach" in antwort.text
    finally:
        db.close()


def test_fehlende_postfachseite_gibt_503_ohne_ersatzseite(umgebung):
    db, app = _app(umgebung)
    try:
        with TestClient(app) as client:
            antwort = client.get("/postfach")
        assert antwort.status_code == 503
        assert antwort.text == "postfach surface missing from image"
        assert "<html" not in antwort.text.lower()
    finally:
        db.close()


def test_der_chat_bleibt_auf_dem_wurzelweg(umgebung):
    """Eignerentscheidung 2026-08-18: keine Startseite. "/" ist der Chat.

    Der Test steht hier, weil der Umzug zwischenzeitlich geplant und wieder
    zurueckgenommen wurde -- ohne diese Zusicherung waere er beim naechsten Mal
    still wieder da.
    """
    db, app = _app(umgebung)
    try:
        wege = {r.path for r in app.routes if hasattr(r, "path")}
        assert "/" in wege
        assert "/postfach" in wege
        ziel = next(r for r in app.routes if getattr(r, "path", None) == "/")
        assert ziel.endpoint.__name__ == "chat_index"
    finally:
        db.close()


# ── /api/zustand ──────────────────────────────────────────────────────────

def test_zustand_verlangt_ein_gueltiges_clerk_token(umgebung):
    db, app = _app(umgebung)
    try:
        with TestClient(app) as client:
            assert client.get("/api/zustand").status_code == 401
            assert client.get(
                "/api/zustand", headers={"Authorization": "Bearer falsch"}
            ).status_code == 401
    finally:
        db.close()


def test_unbekanntes_subjekt_bekommt_keinen_zustand(umgebung):
    db, app = _app(umgebung, subjekt="clerk_fremd")
    try:
        with TestClient(app) as client:
            antwort = client.get("/api/zustand", headers={"Authorization": "Bearer gutes-token"})
        assert antwort.status_code == 403
    finally:
        db.close()


def test_zustand_liefert_gemessene_zahlen_und_null_fuer_ungemessenes(umgebung):
    db, app = _app(umgebung)
    try:
        with TestClient(app) as client:
            antwort = client.get("/api/zustand", headers={"Authorization": "Bearer gutes-token"})
        assert antwort.status_code == 200
        stand = antwort.json()
        assert stand["mensch"] == "gabriel"
        # Gemessen: die Tabellen gibt es, sie sind leer. Eine echte 0.
        assert stand["zuege"] == 0 and stand["turns"] == 0
        assert stand["wirkungen"] == 0 and stand["effects"] == 0
        assert isinstance(stand["generation"], int)
        # Nicht gemessen: `artikel` gibt es nur auf der echten wiki.db, und ohne
        # Zugangsdatei ist kein Postfach erreichbar. Beides null, nicht 0.
        assert stand["artikel"] is None and stand["articles"] is None
        assert stand["ungelesen"] is None and stand["unread"] is None
    finally:
        db.close()


# ── /api/postfach/* ───────────────────────────────────────────────────────

WEGE = (
    "/api/postfach/ordner",
    "/api/postfach/liste",
    "/api/postfach/lesen",
    "/api/postfach/suchen",
    "/api/postfach/entwurf",
    "/api/postfach/loeschen",
    "/api/postfach/spam",
    "/api/postfach/gelesen",
    "/api/postfach/markiere-alle-gelesen",
    "/api/postfach/anhang",
    "/api/postfach/senden",
    "/api/postfach/systempostfaecher",
    "/api/postfach/system/liste",
    "/api/postfach/system/nachrichten",
    "/api/postfach/system/lesen",
    "/api/postfach/system/loeschen",
    "/api/postfach/system/senden",
)


def test_alle_postfachwege_sind_da_und_clerk_geschuetzt(umgebung):
    db, app = _app(umgebung)
    try:
        wege = {r.path for r in app.routes if hasattr(r, "path")}
        for weg in WEGE:
            assert weg in wege, weg
        with TestClient(app) as client:
            for weg in WEGE:
                assert client.post(weg, json={}).status_code == 401, weg
    finally:
        db.close()


def test_ohne_zugangsdatei_meldet_der_dienst_das_offen(umgebung):
    """Nicht eingerichtet ist etwas anderes als leer.

    503 mit Grund -- eine leere Mailliste waere die Behauptung "du hast keine
    Post".
    """
    db, app = _app(umgebung)
    try:
        with TestClient(app) as client:
            antwort = client.post(
                "/api/postfach/ordner", json={},
                headers={"Authorization": "Bearer gutes-token"})
        assert antwort.status_code == 503
        assert antwort.json()["error"] == "postfach_not_configured"
    finally:
        db.close()


def test_ohne_eingetragene_systempostfaecher_kommt_404_statt_leerer_liste(umgebung, monkeypatch):
    """Der Betrachterknopf blendet sich dann still aus.

    Ein Aufklappfeld mit null Reitern sieht aus wie ein Fehler; 404 ist die
    ehrliche Auskunft "diese Einrichtung gibt es hier nicht".
    """
    datei = umgebung / "postfach.env"
    datei.write_text(
        "ENTITYOS_POSTFACH_GABRIEL_ADRESSE=gabriel@frank.ink\n"
        "ENTITYOS_POSTFACH_GABRIEL_PASSWORT=GEHEIM-A\n"
        "ENTITYOS_POSTFACH_ANDREAS_ADRESSE=andreas@frank.ink\n"
        "ENTITYOS_POSTFACH_ANDREAS_PASSWORT=GEHEIM-B\n"
        "ENTITYOS_IMAP_HOST=mail.frank.ink\nENTITYOS_IMAP_PORT=993\n"
        "ENTITYOS_SMTP_HOST=mail.frank.ink\nENTITYOS_SMTP_PORT=587\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ENTITYOS_POSTFACH_ENV", str(datei))
    db, app = _app(umgebung)
    try:
        with TestClient(app) as client:
            antwort = client.post(
                "/api/postfach/systempostfaecher", json={},
                headers={"Authorization": "Bearer gutes-token"})
        assert antwort.status_code == 404
        assert antwort.json()["error"] == "keine_systempostfaecher"
    finally:
        db.close()
