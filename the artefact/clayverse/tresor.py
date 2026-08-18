"""Zwei Tresore -- und die Trennung, die sie ueberhaupt sinnvoll macht.

Gabriels Auftrag: "agent zero braucht einen vault mit allen credentials und
einen extra vault mit allen api tokens; der vault mit den api tokens muss aber
auch eine liste mit capabilitys etc haben."

⭐⭐ DIE TRAGENDE TRENNUNG: KATALOG UND INHALT

    KATALOG   was es gibt, was es kann, wie es steht.   -> Zero darf ihn sehen
    INHALT    der Schluessel selbst.                    -> Zero sieht ihn NIE

Zero soll wissen, DASS es eine Bahn mit 60 Anfragen je Minute gibt und dass sie
gerade lebt. Es muss dafuer den Schluessel nicht kennen -- und wenn es ihn
kennte, waere er in jedem Kontextfenster, jeder Protokollzeile, jeder
Fehlermeldung. Ein Geheimnis, das durch ein Sprachmodell laeuft, ist kein
Geheimnis mehr.

Deshalb gibt es `katalog()` fuer Zero und `wert()` nur fuer den Serverteil
(Bahnenrouter, Postfach). Und weil "ich habe schon aufgepasst" keine Zusicherung
ist, prueft `katalog()` sein eigenes Ergebnis MECHANISCH gegen jeden gelagerten
Wert, bevor es ihn herausgibt. Eine Sicherung, die von Sorgfalt abhaengt, ist
keine.

ZWEI TRESORE, NICHT EINER, weil sie verschiedene Fragen beantworten:
    zugaenge   Anmeldungen, Passwoerter, Registrare -- selten gebraucht,
               fast immer von einem Menschen
    api        Maschinenschluessel MIT Faehigkeitsliste -- staendig gebraucht,
               fast immer von einem Dienst
Ein gemeinsamer Tresor haette bedeutet, dass jeder Dienst, der eine API braucht,
auch die Registrar-Passwoerter aufmacht.

VERSCHLUESSELUNG: AES-256-GCM (authentifiziert -- eine veraenderte Datei faellt
beim Entschluesseln auf, statt stillschweigend Unsinn zu liefern). Der Schluessel
liegt ausserhalb der Datenbank; ein Tresor, dessen Schluessel danebenliegt, ist
eine Schublade.
"""
from __future__ import annotations

import json
import os
import secrets as _secrets
import time
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

TRESORWURZEL = Path("/etc/entityos/tresor")
SCHLUESSELDATEI = Path("/etc/entityos/tresor.key")
TRESORE = ("zugaenge", "api")


class TresorFehler(RuntimeError):
    pass


def _schluessel() -> bytes:
    if not SCHLUESSELDATEI.is_file():
        raise TresorFehler(
            f"kein Tresorschluessel unter {SCHLUESSELDATEI} -- ohne ihn wird nichts "
            "entschluesselt und nichts geraten")
    roh = SCHLUESSELDATEI.read_bytes().strip()
    if len(roh) != 64:
        raise TresorFehler("Tresorschluessel muss 64 Hexzeichen (32 Byte) sein")
    return bytes.fromhex(roh.decode())


def schluessel_anlegen() -> dict:
    """Einmalig. Legt NICHT neu an, wenn schon einer da ist -- das waere ein
    stiller Totalverlust aller Tresore."""
    if SCHLUESSELDATEI.exists():
        return {"angelegt": False, "grund": "existiert bereits -- nicht ueberschrieben"}
    SCHLUESSELDATEI.parent.mkdir(parents=True, exist_ok=True)
    SCHLUESSELDATEI.write_bytes(_secrets.token_bytes(32).hex().encode())
    os.chmod(SCHLUESSELDATEI, 0o640)
    return {"angelegt": True, "pfad": str(SCHLUESSELDATEI)}


def _pfad(name: str) -> Path:
    if name not in TRESORE:
        raise TresorFehler(f"unbekannter Tresor {name!r}; es gibt {TRESORE}")
    return TRESORWURZEL / f"{name}.tresor"


def einlagern(name: str, eintraege: list[dict]) -> dict:
    """Tresor schreiben. Jeder Eintrag: kennung, wert, art, plus Metadaten.

    `wert` ist das Geheimnis. Alles andere ist Katalog und wird spaeter
    unverschluesselt zeigbar sein -- deshalb gehoert dort NICHTS hinein, was
    geheim bleiben soll.
    """
    for e in eintraege:
        if not e.get("kennung"):
            raise TresorFehler("jeder Eintrag braucht eine kennung")
    klartext = json.dumps(
        {"geschrieben": time.time(), "eintraege": eintraege},
        ensure_ascii=False).encode()
    nonce = _secrets.token_bytes(12)
    kiste = AESGCM(_schluessel()).encrypt(nonce, klartext, name.encode())
    p = _pfad(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(nonce + kiste)
    os.chmod(p, 0o640)
    return {"tresor": name, "eintraege": len(eintraege), "bytes": p.stat().st_size}


def oeffnen(name: str) -> dict:
    """Vollstaendig entschluesseln. NUR fuer den Serverteil -- nie an ein Modell."""
    p = _pfad(name)
    if not p.is_file():
        raise TresorFehler(f"Tresor {name} existiert nicht")
    roh = p.read_bytes()
    try:
        klar = AESGCM(_schluessel()).decrypt(roh[:12], roh[12:], name.encode())
    except Exception as e:
        # AES-GCM ist authentifiziert: das hier heisst falscher Schluessel ODER
        # veraenderte Datei. Beides ist ein Alarm, kein Randfall.
        raise TresorFehler(f"Tresor {name} laesst sich nicht oeffnen: {type(e).__name__}") from e
    return json.loads(klar)


def wert(name: str, kennung: str) -> str:
    """EIN Geheimnis holen. Serverseitig. Wirft, statt leer zurueckzugeben --
    ein leerer Schluessel sieht in einem Aufruf aus wie ein fehlendes Recht."""
    for e in oeffnen(name)["eintraege"]:
        if e["kennung"] == kennung:
            w = e.get("wert")
            if not w:
                raise TresorFehler(f"{kennung} liegt im Tresor, hat aber keinen Wert")
            return w
    raise TresorFehler(f"{kennung} nicht im Tresor {name}")


# Felder, die NIE in den Katalog duerfen.
GEHEIM = {"wert", "passwort", "token", "secret", "key"}


def katalog(name: str) -> dict:
    """Was es gibt und was es kann -- OHNE ein einziges Geheimnis.

    ⭐ Das Ergebnis wird MECHANISCH gegen jeden gelagerten Wert geprueft, bevor
    es herausgeht. "Ich habe die geheimen Felder weggelassen" ist eine Absicht;
    diese Pruefung ist eine Zusicherung. Wer sich auf Sorgfalt verlaesst, hat
    keine Sicherung, sondern eine Gewohnheit.
    """
    inhalt = oeffnen(name)
    zeilen, werte = [], []
    for e in inhalt["eintraege"]:
        w = e.get("wert") or ""
        if w:
            werte.append(w)
        zeilen.append({k: v for k, v in e.items() if k not in GEHEIM})
    ergebnis = {
        "tresor": name,
        "eintraege": zeilen,
        "anzahl": len(zeilen),
        "geschrieben_vor_s": round(time.time() - inhalt.get("geschrieben", 0)),
        "hinweis": ("Katalog, kein Inhalt: hier steht, WAS es gibt und was es kann. "
                    "Die Schluessel selbst verlassen den Serverteil nie -- ein "
                    "Geheimnis, das durch ein Sprachmodell laeuft, ist keines mehr."),
    }
    text = json.dumps(ergebnis, ensure_ascii=False)
    for w in werte:
        if len(w) >= 8 and w in text:
            raise TresorFehler(
                "Katalog enthielt einen gelagerten Wert -- Ausgabe verweigert. "
                "Das ist die Sperre, nicht ein Hinweis.")
    return ergebnis


def stand() -> dict:
    """Welche Tresore gibt es, wie gross, wann zuletzt geschrieben."""
    aus = {}
    for n in TRESORE:
        p = _pfad(n)
        aus[n] = ({"vorhanden": False} if not p.is_file() else
                  {"vorhanden": True, "bytes": p.stat().st_size,
                   "geaendert_vor_s": round(time.time() - p.stat().st_mtime)})
    aus["schluessel"] = SCHLUESSELDATEI.is_file()
    return aus
