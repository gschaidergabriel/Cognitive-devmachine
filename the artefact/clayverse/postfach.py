"""Die Mailschicht von entityOS: IMAP/SMTP fuer die zwei Menschen.

Portiert aus dem Vorbild `/opt/agentforge/api/email_routes.py` (frank.ink), aber
an drei Stellen bewusst anders:

* **Verschluesselt statt lokal.** Das Vorbild laeuft AUF dem Mailwirt und redet
  deshalb unverschluesselt mit `127.0.0.1:143`. entityOS laeuft auf einem
  anderen Rechner -- also `IMAP4_SSL` auf 993 und SMTP mit `starttls()` auf 587.
  Die `mailctl`-Selbstheilung des Vorbilds faellt damit weg: sie ruft ein
  lokales Programm auf dem Mailwirt, das es hier nicht gibt. Ein Aufruf, der
  garantiert scheitert, ist keine Heilung, sondern eine verdeckte Fehlerquelle.
* **Zuordnung ueber die Clerk-Karte, nicht ueber die Mailadresse.** Sein
  Postfach ist `andreas@frank.ink`, und das haengt an KEINER Gmail-Adresse:
  der Weg ist clerk_subject -> clerk_map -> user_id -> Postfach. Ein Abgleich
  ueber die Adresse haette ihm still kein Postfach gegeben -- und "still kein"
  ist der Fehler, den man erst bemerkt, wenn eine Mail fehlt.
  ⚠️ Diese Bauart ist der Grund, warum eine offene Frage hier NICHTS kaputt
  macht: welche Gmail-Adresse Andreas' Clerk-Konto traegt, war am 18.08.
  strittig (`herzradgraz@` im Auftragsdokument, `genuinos@` laut Eigner --
  Eignerentscheid: `genuinos@gmail.com`). Weil die Zuordnung ueber die
  Clerk-Kennung laeuft, war die Postfachvergabe davon zu keinem Zeitpunkt
  betroffen. Genau dafuer ist sie so gebaut.
* **Senden ist eine Wirkung.** Es geht durch das EffectGate und bekommt dort
  sein Urteil, wie jede andere Wirkung auch.

⚠️ Produktgesetz: Passwoerter verlassen dieses Modul NIE als Text. Nicht in
UnifiedDB-Zeilen, nicht in Belegen, nicht in Momentaufnahmen, nicht in
Ausnahmetexten. `_ohne_geheimnisse()` ist die letzte Sperre davor, und sie
sitzt an jeder Stelle, an der eine fremde Fehlermeldung nach aussen geht.
"""
from __future__ import annotations

import asyncio
import email as emaillib
import email.header
import email.mime.multipart
import email.mime.text
import email.utils
import hashlib
import imaplib
import os
import re
import smtplib
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote as _prozent

# ⚠️ Diese drei gehoeren an den Modulkopf, nicht in die Wegefunktion. Diese
# Datei traegt `from __future__ import annotations`, also sind Annotationen
# Zeichenketten -- FastAPI loest `request: Request` ueber die MODULglobalen
# auf. Als lokaler Import in registriere_postfach_wege() blieb der Name
# ungeloest, und FastAPI hielt `request` fuer einen Abfrageparameter: jeder
# Postfachweg antwortete mit 422 statt zu arbeiten. Genau so gemessen.
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from .effects import EffectGate, EffectRequest
from .store import UnifiedDB

# Wo die Zugaenge liegen. 640 root:clay, per read-only-Bind im Container --
# siehe compose.yaml. Absichtlich kein Wert im Image und keiner in der Umgebung
# der Prozessliste: ENTITYOS_POSTFACH_ENV nennt nur den PFAD, nie ein Passwort.
# Ohne diesen Schalter wuerde die Testsuite auf einem Wirt, auf dem die echte
# Datei liegt, echte IMAP-Verbindungen aufbauen -- ein Test, der ins Netz
# greift, ist kein Test.
ZUGANGSDATEI = Path("/etc/entityos/postfach.env")


def zugangsdatei() -> Path:
    return Path(os.environ.get("ENTITYOS_POSTFACH_ENV", "").strip() or str(ZUGANGSDATEI))

# Die zwei Menschen. Dieselbe Menge wie in identity.CANONICAL_USERS -- hier
# noch einmal genannt, weil ein Postfach eine eigene Berechtigung ist und nicht
# automatisch jedem folgt, der irgendwann in die Nutzertabelle kommt.
MENSCHEN = ("gabriel", "andreas")

# Dovecot-Ordner, in der Reihenfolge, in der sie der Mensch sehen will.
ORDNER = ("INBOX", "Sent", "Drafts", "Trash", "Junk")

# Netzgrenzen. Ein haengendes IMAP haelt sonst einen Thread bis zum
# TCP-Zeitablauf des Kernels fest -- gemessen minutenlang.
NETZ_ZEITGRENZE_S = 20

# Obergrenzen fuer alles, was von der Oberflaeche hereinkommt. Nicht Kosmetik:
# eine unbegrenzte IMAP-Suchzeichenkette ist eine Abfrageeinschleusung in den
# Mailserver, und eine unbegrenzte Liste ist ein Speicherproblem.
MAX_LISTE = 200
MAX_SUCHE_ZEICHEN = 200
MAX_EMPFAENGER = 50
MAX_BETREFF = 998          # RFC 5322 Zeilenlaenge
MAX_INHALT_ZEICHEN = 200_000


class PostfachFehler(RuntimeError):
    """Der Mailweg selbst ging nicht (Verbindung, Anmeldung, Serverantwort)."""


class PostfachNichtEingerichtet(PostfachFehler):
    """Es gibt keine Zugangsdatei -- das ist ein Betriebs-, kein Laufzeitfehler."""


# ── Zugaenge ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Zugang:
    """Ein Postfach. Das Passwort ist bewusst aus jeder Textdarstellung heraus.

    `repr=False` allein reicht nicht: ein Fehlerbericht, der das ganze Objekt
    formatiert, geht ueber `__repr__` -- deshalb ist der auch von Hand gesetzt.
    """
    adresse: str
    passwort: str = field(repr=False)
    rolle: str = ""

    def __repr__(self) -> str:  # pragma: no cover -- Schutz, keine Logik
        return f"Zugang(adresse={self.adresse!r}, passwort=<verborgen>)"


@dataclass(frozen=True)
class Zugaenge:
    postfaecher: dict[str, Zugang]
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    # System-Postfaecher (abuse@, postmaster@, welcome@ ...) fuer den
    # Admin-Betrachter. Leer, solange in der Zugangsdatei keine
    # ENTITYOS_POSTFACH_SYSTEM_<SCHLUESSEL>_ADRESSE/_PASSWORT stehen. Leer
    # heisst leer -- hier wird nichts erraten und nichts vorbelegt.
    system: dict[str, Zugang] = field(default_factory=dict)

    def alle_passwoerter(self) -> tuple[str, ...]:
        return tuple(
            z.passwort
            for z in (*self.postfaecher.values(), *self.system.values())
            if z.passwort
        )


def _env_datei_lesen(pfad: Path) -> dict[str, str]:
    """KEY=WERT je Zeile, `#` ist Kommentar.

    Bewusst kein dotenv-Paket: eine Abhaengigkeit mehr im Image fuer acht
    Zeilen Datei, und dotenv wuerde ausserdem Anfuehrungszeichen und
    Zeilenfortsetzungen interpretieren -- also mehr Verhalten, als eine
    Geheimnisdatei haben soll.
    """
    werte: dict[str, str] = {}
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        schluessel, _, wert = zeile.partition("=")
        werte[schluessel.strip()] = wert.strip()
    return werte


def _pflicht(werte: dict[str, str], schluessel: str) -> str:
    wert = werte.get(schluessel, "").strip()
    if not wert:
        raise PostfachNichtEingerichtet(f"{schluessel} fehlt in der Zugangsdatei")
    return wert


def _port(werte: dict[str, str], schluessel: str) -> int:
    roh = _pflicht(werte, schluessel)
    if not roh.isdigit() or not 1 <= int(roh) <= 65535:
        raise PostfachNichtEingerichtet(f"{schluessel} ist kein gueltiger Port")
    return int(roh)


def zugaenge_laden(pfad: Path | str | None = None) -> Zugaenge:
    """Zugangsdatei einlesen oder ehrlich scheitern.

    Kein Rueckfall auf Umgebungsvariablen: dann stuende ein Passwort in der
    Prozessumgebung und damit in jedem Absturzbericht des Dienstes.
    """
    pfad = Path(pfad) if pfad is not None else zugangsdatei()
    if not pfad.is_file():
        raise PostfachNichtEingerichtet(f"Zugangsdatei fehlt: {pfad}")
    werte = _env_datei_lesen(pfad)

    postfaecher: dict[str, Zugang] = {}
    for mensch in MENSCHEN:
        gross = mensch.upper()
        postfaecher[mensch] = Zugang(
            adresse=_pflicht(werte, f"ENTITYOS_POSTFACH_{gross}_ADRESSE"),
            passwort=_pflicht(werte, f"ENTITYOS_POSTFACH_{gross}_PASSWORT"),
        )

    system: dict[str, Zugang] = {}
    for schluessel, wert in werte.items():
        treffer = re.fullmatch(r"ENTITYOS_POSTFACH_SYSTEM_([A-Z0-9_]+)_ADRESSE", schluessel)
        if not treffer:
            continue
        name = treffer.group(1)
        passwort = werte.get(f"ENTITYOS_POSTFACH_SYSTEM_{name}_PASSWORT", "").strip()
        if not wert.strip() or not passwort:
            # Halb eingetragen ist nicht eingetragen. Ein System-Postfach ohne
            # Passwort waere im Betrachter ein Reiter, der beim Anklicken
            # immer scheitert -- besser gar nicht anbieten.
            continue
        system[name.lower()] = Zugang(adresse=wert.strip(), passwort=passwort, rolle=name.lower())

    return Zugaenge(
        postfaecher=postfaecher,
        imap_host=_pflicht(werte, "ENTITYOS_IMAP_HOST"),
        imap_port=_port(werte, "ENTITYOS_IMAP_PORT"),
        smtp_host=_pflicht(werte, "ENTITYOS_SMTP_HOST"),
        smtp_port=_port(werte, "ENTITYOS_SMTP_PORT"),
        system=system,
    )


def postfach_fuer_subjekt(zugaenge: Zugaenge, clerk_map: dict[str, str], clerk_subject: str) -> Zugang:
    """Clerk-Subjekt -> Postfach, ueber die Karte, NICHT ueber die Mailadresse.

    Ein drittes Subjekt bekommt `PermissionError` -- genau wie beim
    IdentityRouter. Ein Postfach ist keine Vorgabe, die man erbt, weil man
    sich anmelden konnte.
    """
    user_id = clerk_map.get(clerk_subject)
    if user_id not in MENSCHEN:
        raise PermissionError("unmapped Clerk subject")
    return postfach_fuer_menschen(zugaenge, user_id)


def postfach_fuer_menschen(zugaenge: Zugaenge, user_id: str) -> Zugang:
    if user_id not in MENSCHEN:
        raise PermissionError("unmapped Clerk subject")
    zugang = zugaenge.postfaecher.get(user_id)
    if zugang is None:
        raise PermissionError(f"kein Postfach fuer {user_id}")
    return zugang


def _ohne_geheimnisse(text: str, zugaenge: Zugaenge) -> str:
    """Letzte Sperre: kein Passwort verlaesst dieses Modul als Text.

    Fremde Fehlermeldungen (imaplib, smtplib, die Serverantwort) sind der
    Weg, auf dem ein Geheimnis unbeabsichtigt nach aussen kommt -- keiner
    dieser Texte ist von uns geschrieben, also wird jeder gefiltert statt
    einzeln geprueft.
    """
    for passwort in zugaenge.alle_passwoerter():
        text = text.replace(passwort, "<verborgen>")
    return text


# ── Verbindungen ───────────────────────────────────────────────────────────

def _imap_verbinden(zugaenge: Zugaenge, zugang: Zugang) -> imaplib.IMAP4:
    try:
        verbindung = imaplib.IMAP4_SSL(
            zugaenge.imap_host, zugaenge.imap_port, timeout=NETZ_ZEITGRENZE_S
        )
        verbindung.login(zugang.adresse, zugang.passwort)
        return verbindung
    except Exception as exc:
        raise PostfachFehler(
            _ohne_geheimnisse(f"IMAP {zugang.adresse}: {exc}", zugaenge)
        ) from None


def _imap_trennen(verbindung: imaplib.IMAP4) -> None:
    for schritt in (verbindung.close, verbindung.logout):
        try:
            schritt()
        except Exception:
            pass


def _ordner_waehlen(verbindung: imaplib.IMAP4, ordner: str, *, nur_lesen: bool = True) -> int:
    if ordner not in ORDNER:
        raise ValueError(f"unbekannter Ordner: {ordner}")
    status, daten = verbindung.select(f'"{ordner}"', readonly=nur_lesen)
    if status != "OK":
        raise PostfachFehler(f"Ordner nicht waehlbar: {ordner}")
    try:
        return int(daten[0])
    except (ValueError, IndexError, TypeError):
        return 0


# ── Kopf- und Koerperzerlegung (aus dem Vorbild uebernommen) ───────────────

def _kopf_entschluesseln(roh: str | None) -> str:
    """RFC-2047-Kopfzeile in lesbaren Text."""
    if not roh:
        return ""
    try:
        teile = email.header.decode_header(roh)
        aus = []
        for daten, zeichensatz in teile:
            if isinstance(daten, bytes):
                aus.append(daten.decode(zeichensatz or "utf-8", errors="replace"))
            else:
                aus.append(daten)
        return " ".join(aus).strip()
    except Exception:
        return str(roh).strip()


def _name_und_adresse(roh: str | None) -> tuple[str, str]:
    if not roh:
        return ("", "")
    entschluesselt = _kopf_entschluesseln(roh)
    name, adresse = email.utils.parseaddr(entschluesselt)
    return (name or "", adresse or entschluesselt)


def _koerper(nachricht: emaillib.message.Message) -> tuple[str, str]:
    """(Klartext, HTML). Anhaenge werden uebersprungen."""
    text = ""
    html_text = ""
    if nachricht.is_multipart():
        for teil in nachricht.walk():
            art = teil.get_content_type()
            lage = str(teil.get("Content-Disposition", ""))
            if "attachment" in lage:
                continue
            try:
                nutzlast = teil.get_payload(decode=True)
                if nutzlast is None:
                    continue
                zeichensatz = teil.get_content_charset() or "utf-8"
                inhalt = nutzlast.decode(zeichensatz, errors="replace")
            except Exception:
                continue
            if art == "text/plain" and not text:
                text = inhalt
            elif art == "text/html" and not html_text:
                html_text = inhalt
    else:
        try:
            nutzlast = nachricht.get_payload(decode=True)
            if nutzlast:
                zeichensatz = nachricht.get_content_charset() or "utf-8"
                inhalt = nutzlast.decode(zeichensatz, errors="replace")
                if nachricht.get_content_type() == "text/html":
                    html_text = inhalt
                else:
                    text = inhalt
        except Exception:
            text = str(nachricht.get_payload(decode=False) or "")
    return (text, html_text)


def _anhaenge(nachricht: emaillib.message.Message) -> list[dict]:
    aus: list[dict] = []
    if not nachricht.is_multipart():
        return aus
    for teil in nachricht.walk():
        if "attachment" not in str(teil.get("Content-Disposition", "")):
            continue
        name = teil.get_filename()
        name = _kopf_entschluesseln(name) if name else f"anhang_{len(aus) + 1}"
        aus.append({
            "n": len(aus),
            "name": name,
            "size": len(teil.get_payload(decode=True) or b""),
            "content_type": teil.get_content_type(),
        })
    return aus


def _auszug(text: str, laenge: int = 200) -> str:
    if not text:
        return ""
    sauber = re.sub(r"\s+", " ", text).strip()
    return sauber[:laenge]


# Die Oberflaeche liest jedes Feld unter deutschem UND englischem Namen. Beide
# zu liefern kostet nichts -- ein einseitiger Vertrag ist die Stelle, an der
# spaeter still ein Feld leer bleibt, ohne dass jemand einen Fehler sieht.
_FELDNAMEN = {
    "from": "von", "from_name": "von_name", "to": "an", "cc": "kopie",
    "subject": "betreff", "date": "datum", "snippet": "auszug",
    "read": "gelesen", "body": "text", "html": "html_text",
    "attachments": "anhaenge", "in_reply_to": "antwort_auf",
}


def _zweisprachig(eintrag: dict) -> dict:
    for englisch, deutsch in _FELDNAMEN.items():
        if englisch in eintrag:
            eintrag[deutsch] = eintrag[englisch]
    return eintrag


def _umschlag(verbindung: imaplib.IMAP4, nummer: bytes) -> dict | None:
    """Kopfdaten einer Nachricht fuer die Liste. BODY.PEEK -- liest nicht ungelesen weg."""
    try:
        status, daten = verbindung.fetch(
            nummer,
            "(UID FLAGS BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID)] BODY.PEEK[TEXT])",
        )
        if status != "OK" or not daten or daten[0] is None:
            return None
        roh_kopf = b""
        roh_koerper = b""
        marken = ""
        uid = ""
        for eintrag in daten:
            if not (isinstance(eintrag, tuple) and len(eintrag) >= 2):
                continue
            meta = eintrag[0].decode("utf-8", errors="replace") if isinstance(eintrag[0], bytes) else str(eintrag[0])
            nutzlast = eintrag[1]
            if "HEADER.FIELDS" in meta:
                roh_kopf = nutzlast
            elif "TEXT" in meta or "BODY[TEXT]" in meta:
                roh_koerper = nutzlast
            treffer = re.search(r"FLAGS \(([^)]*)\)", meta)
            if treffer:
                marken = treffer.group(1)
            treffer = re.search(r"UID (\d+)", meta)
            if treffer:
                uid = treffer.group(1)

        nachricht = emaillib.message_from_bytes(roh_kopf)
        von_name, von_adresse = _name_und_adresse(nachricht.get("From"))
        _, an_adresse = _name_und_adresse(nachricht.get("To"))
        text = ""
        if roh_koerper:
            try:
                text, _ = _koerper(emaillib.message_from_bytes(roh_koerper))
            except Exception:
                text = roh_koerper.decode("utf-8", errors="replace")
        return _zweisprachig({
            "id": _kopf_entschluesseln(nachricht.get("Message-ID", "")).strip() or uid or nummer.decode(),
            "uid": uid,
            "from": f"{von_name} <{von_adresse}>" if von_name else von_adresse,
            "from_name": von_name,
            "to": an_adresse,
            "subject": _kopf_entschluesseln(nachricht.get("Subject", "")),
            "date": _kopf_entschluesseln(nachricht.get("Date", "")),
            "snippet": _auszug(text),
            "read": r"\Seen" in marken,
        })
    except Exception:
        return None


def _vollstaendig(verbindung: imaplib.IMAP4, nummer: bytes) -> tuple[dict | None, emaillib.message.Message | None]:
    status, daten = verbindung.fetch(nummer, "(UID FLAGS RFC822)")
    if status != "OK" or not daten or daten[0] is None:
        return None, None
    roh = b""
    marken = ""
    uid = ""
    for eintrag in daten:
        if not (isinstance(eintrag, tuple) and len(eintrag) >= 2):
            continue
        meta = eintrag[0].decode("utf-8", errors="replace") if isinstance(eintrag[0], bytes) else str(eintrag[0])
        roh = eintrag[1]
        treffer = re.search(r"FLAGS \(([^)]*)\)", meta)
        if treffer:
            marken = treffer.group(1)
        treffer = re.search(r"UID (\d+)", meta)
        if treffer:
            uid = treffer.group(1)
    nachricht = emaillib.message_from_bytes(roh)
    von_name, von_adresse = _name_und_adresse(nachricht.get("From"))
    _, an_adresse = _name_und_adresse(nachricht.get("To"))
    text, html_text = _koerper(nachricht)
    return _zweisprachig({
        "id": _kopf_entschluesseln(nachricht.get("Message-ID", "")).strip() or uid or "",
        "uid": uid,
        "from": f"{von_name} <{von_adresse}>" if von_name else von_adresse,
        "from_name": von_name,
        "to": an_adresse,
        "cc": _kopf_entschluesseln(nachricht.get("Cc", "")),
        "subject": _kopf_entschluesseln(nachricht.get("Subject", "")),
        "date": _kopf_entschluesseln(nachricht.get("Date", "")),
        "body": text,
        "html": html_text,
        "read": r"\Seen" in marken,
        "in_reply_to": _kopf_entschluesseln(nachricht.get("In-Reply-To", "")).strip(),
        "attachments": _anhaenge(nachricht),
    }), nachricht


def _nummern(verbindung: imaplib.IMAP4) -> list[bytes]:
    """Alle Nachrichtennummern des gewaehlten Ordners, neueste zuerst."""
    status, daten = verbindung.search(None, "ALL")
    if status != "OK" or not daten or daten[0] is None:
        return []
    return list(reversed(daten[0].split()))


# ── Eingaben pruefen ───────────────────────────────────────────────────────

def _text(wert, *, name: str, max_zeichen: int, pflicht: bool = False) -> str:
    if wert is None:
        wert = ""
    if not isinstance(wert, str):
        raise ValueError(f"{name} muss Text sein")
    wert = wert.strip()
    if pflicht and not wert:
        raise ValueError(f"{name} fehlt")
    if len(wert) > max_zeichen:
        raise ValueError(f"{name} ist zu lang")
    return wert


def _adressliste(roh: str, *, name: str) -> list[str]:
    adressen = [a.strip() for a in roh.split(",") if a.strip()]
    if len(adressen) > MAX_EMPFAENGER:
        raise ValueError(f"{name}: zu viele Empfaenger")
    for adresse in adressen:
        if "@" not in adresse or any(z in adresse for z in "\r\n"):
            raise ValueError(f"{name}: ungueltige Adresse")
    return adressen


def _suchbegriff(roh: str) -> str:
    """IMAP-Suche ist eine Abfragesprache, kein Textfeld.

    Anfuehrungszeichen und Klammern wuerden die Abfrage aufbrechen -- das ist
    dieselbe Klasse Fehler wie SQL-Einschleusung, nur an einem Mailserver.
    Deshalb bleiben nur unverfaengliche Zeichen uebrig.
    """
    sauber = re.sub(r'[^\w @.\-äöüÄÖÜß]', " ", roh, flags=re.UNICODE).strip()
    return sauber[:MAX_SUCHE_ZEICHEN]


# ── Lesende Wege ───────────────────────────────────────────────────────────

class Postfach:
    """Ein Postfach, gebunden an genau einen Menschen.

    Jede Methode oeffnet und schliesst ihre eigene Verbindung. Das ist bewusst
    nicht gepoolt: eine gehaltene IMAP-Verbindung ueber viele Anfragen hinweg
    braucht eine eigene Lebenszeit- und Fehlerverwaltung, und die waere hier
    mehr Zustand als die ganze Mailschicht Nutzen bringt.
    """

    def __init__(self, zugaenge: Zugaenge, zugang: Zugang):
        self.zugaenge = zugaenge
        self.zugang = zugang

    # -- Verbindung --------------------------------------------------------
    def _offen(self) -> imaplib.IMAP4:
        return _imap_verbinden(self.zugaenge, self.zugang)

    def _fehlertext(self, exc: Exception) -> str:
        return _ohne_geheimnisse(f"{type(exc).__name__}: {exc}", self.zugaenge)

    # -- Ordner ------------------------------------------------------------
    def ordner(self) -> dict:
        verbindung = self._offen()
        try:
            aus: dict[str, dict] = {}
            for ordner in ORDNER:
                try:
                    status, daten = verbindung.status(f'"{ordner}"', "(UNSEEN MESSAGES)")
                except Exception:
                    continue
                if status != "OK" or not daten:
                    continue
                antwort = daten[0].decode("utf-8", errors="replace")
                ungelesen = re.search(r"UNSEEN\s+(\d+)", antwort)
                gesamt = re.search(r"MESSAGES\s+(\d+)", antwort)
                aus[ordner] = {
                    "unread": int(ungelesen.group(1)) if ungelesen else 0,
                    "total": int(gesamt.group(1)) if gesamt else 0,
                }
            return {"ok": True, "adresse": self.zugang.adresse, "unread": aus, "ungelesen": aus}
        finally:
            _imap_trennen(verbindung)

    def ungelesen_im_posteingang(self) -> int:
        """Nur die eine Zahl, die die Schale und die Startseite brauchen."""
        verbindung = self._offen()
        try:
            status, daten = verbindung.status('"INBOX"', "(UNSEEN)")
            if status != "OK" or not daten:
                raise PostfachFehler("INBOX meldet keinen Zaehlerstand")
            treffer = re.search(r"UNSEEN\s+(\d+)", daten[0].decode("utf-8", errors="replace"))
            if not treffer:
                raise PostfachFehler("INBOX-Antwort ohne UNSEEN")
            return int(treffer.group(1))
        finally:
            _imap_trennen(verbindung)

    # -- Liste / Lesen / Suche --------------------------------------------
    def liste(self, ordner: str = "INBOX", grenze: int = 25) -> dict:
        grenze = max(1, min(int(grenze), MAX_LISTE))
        verbindung = self._offen()
        try:
            gesamt = _ordner_waehlen(verbindung, ordner, nur_lesen=True)
            if gesamt == 0:
                return {"ok": True, "folder": ordner, "ordner": ordner, "total": 0,
                        "gesamt": 0, "emails": [], "mails": []}
            mails = []
            for i, nummer in enumerate(_nummern(verbindung)[:grenze]):
                umschlag = _umschlag(verbindung, nummer)
                if umschlag:
                    umschlag["idx"] = i
                    mails.append(umschlag)
            return {"ok": True, "folder": ordner, "ordner": ordner, "total": gesamt,
                    "gesamt": gesamt, "emails": mails, "mails": mails}
        finally:
            _imap_trennen(verbindung)

    def _nachricht_finden(self, verbindung: imaplib.IMAP4, *, idx: int,
                          uid: str = "", msg_id: str = "") -> bytes:
        """UID oder Message-ID schlagen die Position.

        `idx` ist nur eine Stelle in der aktuell gelisteten Reihenfolge -- sie
        verschiebt sich, sobald eine Mail eintrifft oder geloescht wird. Wer
        einen Anhang oeffnet, waehrend gerade eine neue Mail ankommt, bekaeme
        sonst den Anhang der falschen Nachricht. Deshalb: stabile Kennung
        zuerst, Position nur als Rueckfall.
        """
        if uid:
            kennung = self._nachrichtenkennung(uid)
            if kennung.isdigit():
                status, daten = verbindung.search(None, f"(UID {kennung})")
                if status == "OK" and daten and daten[0]:
                    return daten[0].split()[-1]
        if msg_id:
            kennung = self._nachrichtenkennung(msg_id)
            status, daten = verbindung.search(None, f'(HEADER Message-ID "{kennung}")')
            if status == "OK" and daten and daten[0]:
                return daten[0].split()[-1]
        nummern = _nummern(verbindung)
        if not isinstance(idx, int) or idx < 0 or idx >= len(nummern):
            raise ValueError("Nachricht nicht gefunden")
        return nummern[idx]

    def lesen(self, ordner: str = "INBOX", idx: int = 0, uid: str = "",
              msg_id: str = "") -> dict:
        verbindung = self._offen()
        try:
            _ordner_waehlen(verbindung, ordner, nur_lesen=False)
            nummer = self._nachricht_finden(verbindung, idx=idx, uid=uid, msg_id=msg_id)
            verbindung.store(nummer, "+FLAGS", r"(\Seen)")
            mail, _ = _vollstaendig(verbindung, nummer)
            if mail is None:
                raise PostfachFehler("Nachricht nicht lesbar")
            mail["idx"] = idx
            return {"ok": True, "folder": ordner, "ordner": ordner, "email": mail, "mail": mail}
        finally:
            _imap_trennen(verbindung)

    def anhang(self, ordner: str = "INBOX", index: int = 0, idx: int = 0,
               uid: str = "", msg_id: str = "", name: str = "") -> tuple[str, str, bytes]:
        """(Dateiname, Inhaltsart, Bytes) eines Anhangs.

        Gesucht wird nach `name`, wenn einer mitkommt, sonst nach `index`.
        Der Name ist das, was der Mensch angeklickt hat -- er trifft auch dann
        noch, wenn die Reihenfolge der Teile anders gezaehlt wird als in der
        Anzeige.
        """
        verbindung = self._offen()
        try:
            _ordner_waehlen(verbindung, ordner, nur_lesen=True)
            nummer = self._nachricht_finden(verbindung, idx=idx, uid=uid, msg_id=msg_id)
            _, nachricht = _vollstaendig(verbindung, nummer)
            if nachricht is None:
                raise PostfachFehler("Nachricht nicht lesbar")
            gefunden = 0
            for teil in nachricht.walk():
                if "attachment" not in str(teil.get("Content-Disposition", "")):
                    continue
                roh_name = teil.get_filename()
                teil_name = _kopf_entschluesseln(roh_name) if roh_name else f"anhang_{gefunden}"
                if (name and teil_name == name) or (not name and gefunden == index):
                    return (teil_name, teil.get_content_type(),
                            teil.get_payload(decode=True) or b"")
                gefunden += 1
            raise ValueError("Anhang nicht vorhanden")
        finally:
            _imap_trennen(verbindung)

    def suchen(self, begriff: str, ordner: str = "INBOX", grenze: int = 25) -> dict:
        begriff = _suchbegriff(_text(begriff, name="Suchbegriff", max_zeichen=MAX_SUCHE_ZEICHEN))
        grenze = max(1, min(int(grenze), MAX_LISTE))
        if not begriff:
            return {"ok": True, "folder": ordner, "ordner": ordner, "emails": [], "mails": []}
        verbindung = self._offen()
        try:
            _ordner_waehlen(verbindung, ordner, nur_lesen=True)
            abfrage = f'(OR OR SUBJECT "{begriff}" FROM "{begriff}" BODY "{begriff}")'
            try:
                status, daten = verbindung.search(None, abfrage)
            except imaplib.IMAP4.error:
                status, daten = verbindung.search(None, f'(SUBJECT "{begriff}")')
            if status != "OK" or not daten or daten[0] is None:
                return {"ok": True, "folder": ordner, "ordner": ordner, "emails": [], "mails": []}
            mails = []
            for i, nummer in enumerate(list(reversed(daten[0].split()))[:grenze]):
                umschlag = _umschlag(verbindung, nummer)
                if umschlag:
                    umschlag["idx"] = i
                    mails.append(umschlag)
            return {"ok": True, "folder": ordner, "ordner": ordner, "emails": mails, "mails": mails}
        finally:
            _imap_trennen(verbindung)

    # -- Aendernde Wege ohne Aussenwirkung ---------------------------------
    def _suchen_nach_id(self, verbindung: imaplib.IMAP4, msg_id: str) -> list[bytes]:
        status, daten = verbindung.search(None, f'(HEADER Message-ID "{msg_id}")')
        if (status != "OK" or not daten or not daten[0]) and msg_id.isdigit():
            status, daten = verbindung.search(None, f"(UID {msg_id})")
        if status != "OK" or not daten or not daten[0]:
            raise ValueError("Nachricht nicht gefunden")
        return daten[0].split()

    @staticmethod
    def _nachrichtenkennung(roh) -> str:
        kennung = _text(roh, name="msg_id", max_zeichen=998, pflicht=True)
        if any(z in kennung for z in '"\r\n'):
            raise ValueError("ungueltige Nachrichtenkennung")
        return kennung

    def loeschen(self, ordner: str, msg_id: str) -> dict:
        msg_id = self._nachrichtenkennung(msg_id)
        verbindung = self._offen()
        try:
            _ordner_waehlen(verbindung, ordner, nur_lesen=False)
            for nummer in self._suchen_nach_id(verbindung, msg_id):
                verbindung.store(nummer, "+FLAGS", r"(\Deleted)")
            verbindung.expunge()
            return {"ok": True}
        finally:
            _imap_trennen(verbindung)

    def spam(self, ordner: str, msg_id: str) -> dict:
        msg_id = self._nachrichtenkennung(msg_id)
        verbindung = self._offen()
        try:
            _ordner_waehlen(verbindung, ordner, nur_lesen=False)
            for nummer in self._suchen_nach_id(verbindung, msg_id):
                verbindung.copy(nummer, '"Junk"')
                verbindung.store(nummer, "+FLAGS", r"(\Deleted)")
            verbindung.expunge()
            return {"ok": True}
        finally:
            _imap_trennen(verbindung)

    def gelesen(self, ordner: str, msg_id: str, gelesen: bool = True) -> dict:
        msg_id = self._nachrichtenkennung(msg_id)
        verbindung = self._offen()
        try:
            _ordner_waehlen(verbindung, ordner, nur_lesen=False)
            marke = "+FLAGS" if gelesen else "-FLAGS"
            for nummer in self._suchen_nach_id(verbindung, msg_id):
                verbindung.store(nummer, marke, r"(\Seen)")
            return {"ok": True, "read": bool(gelesen)}
        finally:
            _imap_trennen(verbindung)

    def alle_gelesen(self, ordner: str = "INBOX") -> dict:
        verbindung = self._offen()
        try:
            _ordner_waehlen(verbindung, ordner, nur_lesen=False)
            status, daten = verbindung.search(None, "UNSEEN")
            if status != "OK" or not daten or not daten[0]:
                return {"ok": True, "folder": ordner, "markiert": 0}
            nummern = daten[0].split()
            for nummer in nummern:
                verbindung.store(nummer, "+FLAGS", r"(\Seen)")
            return {"ok": True, "folder": ordner, "markiert": len(nummern)}
        finally:
            _imap_trennen(verbindung)

    def entwurf(self, an: str, betreff: str, inhalt: str) -> dict:
        nachricht = _entwurfsnachricht(self.zugang.adresse, an, betreff, inhalt)
        verbindung = self._offen()
        try:
            status, _ = verbindung.append(
                '"Drafts"', r"(\Draft)", imaplib.Time2Internaldate(time.time()),
                nachricht.as_bytes(),
            )
            if status != "OK":
                raise PostfachFehler("Entwurf konnte nicht abgelegt werden")
            return {"ok": True}
        finally:
            _imap_trennen(verbindung)


def _entwurfsnachricht(absender: str, an: str, betreff: str, inhalt: str):
    nachricht = email.mime.text.MIMEText(
        _text(inhalt, name="Inhalt", max_zeichen=MAX_INHALT_ZEICHEN), "plain", "utf-8"
    )
    nachricht["From"] = absender
    nachricht["To"] = _text(an, name="Empfaenger", max_zeichen=4000)
    nachricht["Subject"] = _text(betreff, name="Betreff", max_zeichen=MAX_BETREFF)
    nachricht["Date"] = email.utils.formatdate(localtime=True)
    nachricht["Message-ID"] = email.utils.make_msgid(domain=absender.split("@")[-1])
    return nachricht


# ── Senden: eine Wirkung, mit Urteil und Beleg ─────────────────────────────

BELEG_SCHEMA = """
CREATE TABLE IF NOT EXISTS entityos_postfach_belege(
  beleg_id TEXT PRIMARY KEY,
  effect_id TEXT,
  causal_id TEXT,
  user_id TEXT NOT NULL,
  absender TEXT NOT NULL,
  empfaenger TEXT NOT NULL,
  betreff TEXT NOT NULL,
  inhalt_sha256 TEXT NOT NULL,
  inhalt_bytes INTEGER NOT NULL,
  urteil TEXT NOT NULL,
  ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_postfach_belege_ts ON entityos_postfach_belege(ts DESC);
"""


def beleg_schema_sicherstellen(db: UnifiedDB) -> None:
    """Nur Tabelle und Index. Startaufgabe, keine Leseaufgabe.

    `executescript()` committet implizit -- aus einem laufenden Zug heraus
    aufgerufen reisst das dessen Transaktion auseinander. Dieselbe Falle wie
    bei wirte.verbundene_systeme(), dort schon einmal mit 77 roten Tests
    bezahlt.
    """
    db.db.executescript(BELEG_SCHEMA)


def _absenderdomaene(adresse: str) -> str:
    return adresse.rsplit("@", 1)[-1]


def _sendenachricht(absender: str, an: list[str], betreff: str, inhalt: str,
                    cc: list[str], in_reply_to: str, references: str,
                    anzeigename: str = ""):
    nachricht = email.mime.multipart.MIMEMultipart("alternative")
    nachricht["From"] = email.utils.formataddr((anzeigename, absender)) if anzeigename else absender
    nachricht["To"] = ", ".join(an)
    nachricht["Subject"] = betreff
    nachricht["Date"] = email.utils.formatdate(localtime=True)
    nachricht["Message-ID"] = email.utils.make_msgid(domain=_absenderdomaene(absender))
    if cc:
        nachricht["Cc"] = ", ".join(cc)
    if in_reply_to:
        nachricht["In-Reply-To"] = in_reply_to
        nachricht["References"] = references or in_reply_to
    nachricht.attach(email.mime.text.MIMEText(inhalt, "plain", "utf-8"))
    return nachricht


def _smtp_senden(zugaenge: Zugaenge, zugang: Zugang, empfaenger: list[str], roh: bytes) -> None:
    try:
        verbindung = smtplib.SMTP(zugaenge.smtp_host, zugaenge.smtp_port, timeout=NETZ_ZEITGRENZE_S)
        try:
            verbindung.starttls()
            verbindung.login(zugang.adresse, zugang.passwort)
            verbindung.sendmail(zugang.adresse, empfaenger, roh)
        finally:
            try:
                verbindung.quit()
            except Exception:
                pass
    except Exception as exc:
        raise PostfachFehler(
            _ohne_geheimnisse(f"SMTP {zugang.adresse}: {exc}", zugaenge)
        ) from None


def _in_sent_ablegen(zugaenge: Zugaenge, zugang: Zugang, roh: bytes) -> bool:
    """Kopie in "Sent". Darf den Versand nie umwerfen -- die Mail ist dann schon weg.

    Der Rueckgabewert sagt, ob es geklappt hat: die Oberflaeche soll "gesendet,
    aber nicht abgelegt" zeigen koennen statt still einen leeren Sent-Ordner.
    """
    try:
        verbindung = _imap_verbinden(zugaenge, zugang)
    except PostfachFehler:
        return False
    try:
        status, _ = verbindung.append(
            '"Sent"', r"(\Seen)", imaplib.Time2Internaldate(time.time()), roh
        )
        return status == "OK"
    except Exception:
        return False
    finally:
        _imap_trennen(verbindung)


def _beleg_schreiben(db: UnifiedDB, *, effect_id: str | None, causal_id: str | None,
                     user_id: str, absender: str, empfaenger: list[str], betreff: str,
                     inhalt_sha256: str, inhalt_bytes: int, urteil: str) -> str:
    """Der lesbare Teil des Belegs.

    Warum eine eigene Tabelle statt der `effects`-Zeile: EffectJournal
    verschwiegt Ziel und Ergebnis absichtlich zu Pruefsummen
    (`_target_receipt`, `SAFE_OUTCOME_FIELDS`) -- Empfaenger und Betreff
    kaemen dort nie lesbar an. Diese Redaktion zu lockern wuerde eine Grenze
    aufweichen, die JEDE Wirkung schuetzt, nur damit eine bequemer wird. Also
    bleibt das Urteil im Journal und der lesbare Teil steht hier, ueber
    effect_id/causal_id verbunden.

    Der Mailtext selbst steht bewusst nicht hier -- nur seine Pruefsumme.
    """
    beleg_id = str(uuid.uuid4())
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO entityos_postfach_belege(beleg_id,effect_id,causal_id,user_id,"
            "absender,empfaenger,betreff,inhalt_sha256,inhalt_bytes,urteil,ts) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (beleg_id, effect_id, causal_id, user_id, absender, ", ".join(empfaenger),
             betreff, inhalt_sha256, int(inhalt_bytes), urteil, time.time()),
        )
    return beleg_id


def senden(db: UnifiedDB, zugaenge: Zugaenge, *, user_id: str, session_id: str,
           an: str, betreff: str, inhalt: str, cc: str = "", bcc: str = "",
           in_reply_to: str = "", references: str = "",
           gate: EffectGate | None = None) -> dict:
    """Eine Mail verschicken -- durch das Tor, mit Urteil und Beleg.

    Die Reihenfolge ist der Punkt: erst wird die Nachricht gebaut und ihre
    Pruefsumme genommen, dann faellt das Urteil, und erst danach geht etwas
    ueber SMTP. Wer zuerst sendet und danach beurteilt, hat kein Tor, sondern
    ein Protokoll.
    """
    zugang = postfach_fuer_menschen(zugaenge, user_id)
    empfaenger_an = _adressliste(_text(an, name="Empfaenger", max_zeichen=4000, pflicht=True), name="an")
    if not empfaenger_an:
        raise ValueError("Empfaenger fehlt")
    empfaenger_cc = _adressliste(_text(cc, name="Kopie", max_zeichen=4000), name="cc")
    empfaenger_bcc = _adressliste(_text(bcc, name="Blindkopie", max_zeichen=4000), name="bcc")
    betreff = _text(betreff, name="Betreff", max_zeichen=MAX_BETREFF)
    inhalt = _text(inhalt, name="Inhalt", max_zeichen=MAX_INHALT_ZEICHEN)
    if not betreff and not inhalt:
        raise ValueError("Betreff oder Inhalt wird gebraucht")

    nachricht = _sendenachricht(
        zugang.adresse, empfaenger_an, betreff, inhalt, empfaenger_cc,
        _text(in_reply_to, name="In-Reply-To", max_zeichen=998),
        _text(references, name="References", max_zeichen=4000),
    )
    roh = nachricht.as_bytes()
    inhalt_sha256 = hashlib.sha256(roh).hexdigest()
    alle = [*empfaenger_an, *empfaenger_cc, *empfaenger_bcc]

    abgelegt = {"sent": False}

    def wirker(_req: EffectRequest) -> dict:
        _smtp_senden(zugaenge, zugang, alle, roh)
        abgelegt["sent"] = _in_sent_ablegen(zugaenge, zugang, roh)
        # Was hier zurueckkommt, landet als Pruefsumme im Effektbuch. Deshalb
        # nur Zaehlbares -- kein Empfaenger, kein Betreff, kein Inhalt, und
        # unter keinen Umstaenden ein Zugang.
        return {"ok": True, "empfaenger_anzahl": len(alle), "bytes": len(roh)}

    gate = gate or EffectGate(db, postfach_sender=wirker)
    if gate.postfach_sender is None:
        gate.postfach_sender = wirker
    ziel = f"postfach:senden:{','.join(alle)}"[:2048]
    beleg_schema_sicherstellen(db)

    try:
        effect_id, ergebnis = gate.execute(
            EffectRequest(user_id=user_id, session_id=session_id,
                          capability="postfach.senden", target=ziel)
        )
    except Exception:
        # Das Tor hat die Wirkung schon als FAILED verbucht. Der lesbare Beleg
        # gehoert trotzdem geschrieben: ein Fehlversuch, der keine Spur
        # hinterlaesst, ist genau die Sorte Nichtwissen, die spaeter fuer
        # "wurde nie versucht" gehalten wird.
        _beleg_schreiben(db, effect_id=None, causal_id=None, user_id=user_id,
                         absender=zugang.adresse, empfaenger=alle, betreff=betreff,
                         inhalt_sha256=inhalt_sha256, inhalt_bytes=len(roh),
                         urteil="FAILED")
        raise

    zeile = db.db.execute(
        "SELECT status FROM effects WHERE effect_id=?", (effect_id,)
    ).fetchone()
    urteil = str(zeile[0]) if zeile else "UNKNOWN"
    beleg_id = _beleg_schreiben(
        db, effect_id=effect_id, causal_id=gate.causal_for_effect(effect_id),
        user_id=user_id, absender=zugang.adresse, empfaenger=alle, betreff=betreff,
        inhalt_sha256=inhalt_sha256, inhalt_bytes=len(roh), urteil=urteil,
    )
    return {
        "ok": bool(ergebnis.get("ok")),
        "urteil": urteil,
        "effect_id": effect_id,
        "beleg_id": beleg_id,
        "inhalt_sha256": inhalt_sha256,
        "in_sent_abgelegt": abgelegt["sent"],
    }


# ── Admin-Postfachbetrachter (System-Postfaecher) ──────────────────────────
# Gabriel will ihn ausdruecklich behalten. Im Vorbild heisst er
# `_showSystemMailboxModal` und haengt an /api/admin/system-mailboxes/*.
# Hier liest er seine Zugaenge aus derselben Datei wie alles andere --
# Zeilen ENTITYOS_POSTFACH_SYSTEM_<NAME>_ADRESSE/_PASSWORT. Stehen dort keine,
# ist die Liste leer. Leer heisst leer: es wird kein Postfach erraten und
# keines mit erfundenen Zaehlern angezeigt.

def system_postfaecher(zugaenge: Zugaenge) -> list[dict]:
    return [
        {"key": name, "email": zugang.adresse, "role": zugang.rolle}
        for name, zugang in sorted(zugaenge.system.items())
    ]


def _system_zugang(zugaenge: Zugaenge, key: str) -> Zugang:
    zugang = zugaenge.system.get(str(key).strip().lower())
    if zugang is None:
        raise ValueError(f"System-Postfach nicht eingerichtet: {key}")
    return zugang


def system_nachrichten(zugaenge: Zugaenge, key: str, grenze: int = 40) -> dict:
    zugang = _system_zugang(zugaenge, key)
    grenze = max(1, min(int(grenze), MAX_LISTE))
    verbindung = _imap_verbinden(zugaenge, zugang)
    try:
        _ordner_waehlen(verbindung, "INBOX", nur_lesen=True)
        mails = []
        for i, nummer in enumerate(_nummern(verbindung)[:grenze]):
            umschlag = _umschlag(verbindung, nummer)
            if umschlag:
                umschlag["idx"] = i
                mails.append(umschlag)
        return {"ok": True, "mailbox": zugang.adresse, "count": len(mails),
                "items": mails, "mails": mails}
    finally:
        _imap_trennen(verbindung)


def system_nachricht(zugaenge: Zugaenge, key: str, idx: int) -> dict:
    zugang = _system_zugang(zugaenge, key)
    verbindung = _imap_verbinden(zugaenge, zugang)
    try:
        _ordner_waehlen(verbindung, "INBOX", nur_lesen=False)
        nummern = _nummern(verbindung)
        if not isinstance(idx, int) or idx < 0 or idx >= len(nummern):
            raise ValueError("Nachricht nicht im Bereich")
        nummer = nummern[idx]
        verbindung.store(nummer, "+FLAGS", r"(\Seen)")
        mail, _ = _vollstaendig(verbindung, nummer)
        if mail is None:
            raise PostfachFehler("Nachricht nicht lesbar")
        mail["idx"] = idx
        return {"ok": True, "mailbox": zugang.adresse, "email": mail, "mail": mail}
    finally:
        _imap_trennen(verbindung)


def system_loeschen(zugaenge: Zugaenge, key: str, idx: int) -> dict:
    zugang = _system_zugang(zugaenge, key)
    verbindung = _imap_verbinden(zugaenge, zugang)
    try:
        _ordner_waehlen(verbindung, "INBOX", nur_lesen=False)
        nummern = _nummern(verbindung)
        if not isinstance(idx, int) or idx < 0 or idx >= len(nummern):
            raise ValueError("Nachricht nicht im Bereich")
        verbindung.store(nummern[idx], "+FLAGS", r"(\Deleted)")
        verbindung.expunge()
        return {"ok": True, "mailbox": zugang.adresse}
    finally:
        _imap_trennen(verbindung)


def system_senden(db: UnifiedDB, zugaenge: Zugaenge, key: str, *, user_id: str,
                  session_id: str, an: str, betreff: str, inhalt: str, cc: str = "",
                  in_reply_to: str = "", references: str = "",
                  gate: EffectGate | None = None) -> dict:
    """Als System-Postfach senden -- dieselbe Wirkungskette wie beim Menschen.

    Der Absender ist ein anderer, das Urteil kommt aus demselben Tor. Eine
    zweite, torlose Sendestrecke waere genau das Schlupfloch, gegen das das
    Tor gebaut wurde.
    """
    zugang = _system_zugang(zugaenge, key)
    empfaenger_an = _adressliste(_text(an, name="Empfaenger", max_zeichen=4000, pflicht=True), name="an")
    if not empfaenger_an:
        raise ValueError("Empfaenger fehlt")
    empfaenger_cc = _adressliste(_text(cc, name="Kopie", max_zeichen=4000), name="cc")
    betreff = _text(betreff, name="Betreff", max_zeichen=MAX_BETREFF, pflicht=True)
    inhalt = _text(inhalt, name="Inhalt", max_zeichen=MAX_INHALT_ZEICHEN)

    nachricht = _sendenachricht(
        zugang.adresse, empfaenger_an, betreff, inhalt, empfaenger_cc,
        _text(in_reply_to, name="In-Reply-To", max_zeichen=998),
        _text(references, name="References", max_zeichen=4000),
        anzeigename=zugang.rolle or key,
    )
    roh = nachricht.as_bytes()
    inhalt_sha256 = hashlib.sha256(roh).hexdigest()
    alle = [*empfaenger_an, *empfaenger_cc]
    abgelegt = {"sent": False}

    def wirker(_req: EffectRequest) -> dict:
        _smtp_senden(zugaenge, zugang, alle, roh)
        abgelegt["sent"] = _in_sent_ablegen(zugaenge, zugang, roh)
        return {"ok": True, "empfaenger_anzahl": len(alle), "bytes": len(roh)}

    gate = gate or EffectGate(db, postfach_sender=wirker)
    if gate.postfach_sender is None:
        gate.postfach_sender = wirker
    beleg_schema_sicherstellen(db)
    ziel = f"postfach:senden:{zugang.adresse}->{','.join(alle)}"[:2048]

    try:
        effect_id, ergebnis = gate.execute(
            EffectRequest(user_id=user_id, session_id=session_id,
                          capability="postfach.senden", target=ziel)
        )
    except Exception:
        _beleg_schreiben(db, effect_id=None, causal_id=None, user_id=user_id,
                         absender=zugang.adresse, empfaenger=alle, betreff=betreff,
                         inhalt_sha256=inhalt_sha256, inhalt_bytes=len(roh),
                         urteil="FAILED")
        raise

    zeile = db.db.execute("SELECT status FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
    urteil = str(zeile[0]) if zeile else "UNKNOWN"
    beleg_id = _beleg_schreiben(
        db, effect_id=effect_id, causal_id=gate.causal_for_effect(effect_id),
        user_id=user_id, absender=zugang.adresse, empfaenger=alle, betreff=betreff,
        inhalt_sha256=inhalt_sha256, inhalt_bytes=len(roh), urteil=urteil,
    )
    return {
        "ok": bool(ergebnis.get("ok")),
        "urteil": urteil,
        "effect_id": effect_id,
        "beleg_id": beleg_id,
        "mailbox": zugang.adresse,
        "inhalt_sha256": inhalt_sha256,
        "in_sent_abgelegt": abgelegt["sent"],
    }


# ── Die Wege ───────────────────────────────────────────────────────────────
def _feld(rumpf: dict, *namen, vorgabe=None):
    """Ein Feld unter mehreren Namen lesen.

    Die Oberflaeche darf deutsch ODER englisch schicken (`ordner`/`folder`,
    `betreff`/`subject`). Zwei getrennte Vertraege zwischen Vorder- und
    Rueckseite waeren genau die Stelle, an der spaeter ein Feld still leer
    bleibt -- also nimmt der Server beides an.
    """
    if not isinstance(rumpf, dict):
        raise ValueError("Rumpf muss ein Objekt sein")
    for name in namen:
        if name in rumpf and rumpf[name] is not None:
            return rumpf[name]
    return vorgabe


def _zahl(wert, vorgabe: int = 0) -> int:
    if wert is None or wert == "":
        return vorgabe
    try:
        return int(wert)
    except (TypeError, ValueError):
        raise ValueError("Zahl erwartet")


def registriere_postfach_wege(app, *, db: UnifiedDB, mensch_aufloesen,
                              antwort_auf_fehler, zugangspfad: Path | str | None = None) -> None:
    """Haengt /api/postfach/* in die App.

    `mensch_aufloesen(request)` liefert (user_id, session_id) aus dem
    Clerk-Bearer -- dieselbe Kette wie bei /api/history; die Clerk-Einzelheiten
    bleiben deshalb im Gateway und nicht hier. `antwort_auf_fehler(exc)`
    uebersetzt Ausnahmen einheitlich in Statuscodes.
    """
    # Die Zugaenge werden je Anfrage frisch gelesen. Der Container haelt sie
    # damit nicht dauerhaft im Speicher, und eine geaenderte Zugangsdatei wirkt
    # ohne Neustart. Acht Zeilen Datei -- die Kosten sind keine.
    def _zugaenge() -> Zugaenge:
        return zugaenge_laden(zugangspfad)

    async def _rumpf(request) -> dict:
        try:
            rumpf = await request.json()
        except Exception as exc:
            raise ValueError("ungueltiger JSON-Rumpf") from exc
        if not isinstance(rumpf, dict):
            raise ValueError("Rumpf muss ein Objekt sein")
        return rumpf

    async def _postfach(request) -> tuple[str, str, Zugaenge, Postfach]:
        user_id, session_id = await mensch_aufloesen(request)
        zugaenge = _zugaenge()
        return (user_id, session_id, zugaenge,
                Postfach(zugaenge, postfach_fuer_menschen(zugaenge, user_id)))

    # ── Ordner, Liste, Lesen, Suche ───────────────────────────────────────
    @app.post("/api/postfach/ordner")
    async def postfach_ordner(request: Request):
        try:
            *_, postfach = await _postfach(request)
            return JSONResponse(await asyncio.to_thread(postfach.ordner))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/liste")
    async def postfach_liste(request: Request):
        try:
            *_, postfach = await _postfach(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                postfach.liste,
                str(_feld(rumpf, "ordner", "folder", vorgabe="INBOX")),
                _zahl(_feld(rumpf, "grenze", "limit"), 25)))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/lesen")
    async def postfach_lesen(request: Request):
        try:
            *_, postfach = await _postfach(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                postfach.lesen,
                str(_feld(rumpf, "ordner", "folder", vorgabe="INBOX")),
                _zahl(_feld(rumpf, "index", "idx"), 0),
                str(_feld(rumpf, "uid", vorgabe="")),
                str(_feld(rumpf, "id", "msg_id", vorgabe=""))))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/suchen")
    async def postfach_suchen(request: Request):
        try:
            *_, postfach = await _postfach(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                postfach.suchen,
                str(_feld(rumpf, "begriff", "query", "q", vorgabe="")),
                str(_feld(rumpf, "ordner", "folder", vorgabe="INBOX")),
                _zahl(_feld(rumpf, "grenze", "limit"), 25)))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/anhang")
    async def postfach_anhang(request: Request):
        """Rohe Bytes, kein JSON -- die Oberflaeche macht daraus einen Blob."""
        try:
            *_, postfach = await _postfach(request)
            rumpf = await _rumpf(request)
            name, art, daten = await asyncio.to_thread(
                postfach.anhang,
                str(_feld(rumpf, "ordner", "folder", vorgabe="INBOX")),
                _zahl(_feld(rumpf, "index", "n", "idx_anhang"), 0),
                _zahl(_feld(rumpf, "idx", "nachricht_index"), 0),
                str(_feld(rumpf, "uid", vorgabe="")),
                str(_feld(rumpf, "id", "msg_id", vorgabe="")),
                str(_feld(rumpf, "name", "dateiname", vorgabe="")))
            # Der Dateiname kommt aus einer fremden Mail. Ungefiltert in einen
            # Content-Disposition-Kopf gesetzt waere das eine Kopfzeilen-
            # Einschleusung -- deshalb nur der ASCII-Anteil in `filename` und
            # der volle Name prozentkodiert in `filename*`.
            sicher = re.sub(r"[^A-Za-z0-9._-]", "_", name) or "anhang"
            return Response(
                content=daten,
                media_type=art or "application/octet-stream",
                headers={
                    "content-disposition":
                        f'attachment; filename="{sicher}"; filename*=UTF-8\'\'{_prozent(name)}',
                    "content-length": str(len(daten)),
                },
            )
        except Exception as exc:
            return antwort_auf_fehler(exc)

    # ── Aendernde Wege ohne Aussenwirkung ─────────────────────────────────
    @app.post("/api/postfach/entwurf")
    async def postfach_entwurf(request: Request):
        try:
            *_, postfach = await _postfach(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                postfach.entwurf,
                str(_feld(rumpf, "an", "to", vorgabe="")),
                str(_feld(rumpf, "betreff", "subject", vorgabe="")),
                str(_feld(rumpf, "text", "body", vorgabe=""))))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/loeschen")
    async def postfach_loeschen(request: Request):
        try:
            *_, postfach = await _postfach(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                postfach.loeschen,
                str(_feld(rumpf, "ordner", "folder", vorgabe="INBOX")),
                str(_feld(rumpf, "id", "msg_id", "uid", vorgabe=""))))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/spam")
    async def postfach_spam(request: Request):
        try:
            *_, postfach = await _postfach(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                postfach.spam,
                str(_feld(rumpf, "ordner", "folder", vorgabe="INBOX")),
                str(_feld(rumpf, "id", "msg_id", "uid", vorgabe=""))))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/gelesen")
    async def postfach_gelesen(request: Request):
        try:
            *_, postfach = await _postfach(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                postfach.gelesen,
                str(_feld(rumpf, "ordner", "folder", vorgabe="INBOX")),
                str(_feld(rumpf, "id", "msg_id", "uid", vorgabe="")),
                bool(_feld(rumpf, "gelesen", "mark_read", "read", vorgabe=True))))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/markiere-alle-gelesen")
    async def postfach_alle_gelesen(request: Request):
        try:
            *_, postfach = await _postfach(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                postfach.alle_gelesen,
                str(_feld(rumpf, "ordner", "folder", vorgabe="INBOX"))))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    # ── Senden: die einzige Aussenwirkung, deshalb durch das Tor ──────────
    @app.post("/api/postfach/senden")
    async def postfach_senden(request: Request):
        try:
            user_id, session_id, zugaenge, _ = await _postfach(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                senden, db, zugaenge, user_id=user_id, session_id=session_id,
                an=str(_feld(rumpf, "an", "to", vorgabe="")),
                betreff=str(_feld(rumpf, "betreff", "subject", vorgabe="")),
                inhalt=str(_feld(rumpf, "text", "body", vorgabe="")),
                cc=str(_feld(rumpf, "kopie", "cc", vorgabe="")),
                bcc=str(_feld(rumpf, "blindkopie", "bcc", vorgabe="")),
                in_reply_to=str(_feld(rumpf, "antwort_auf", "in_reply_to", vorgabe="")),
                references=str(_feld(rumpf, "referenzen", "references", vorgabe=""))))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    # ── Admin-Postfachbetrachter ──────────────────────────────────────────
    # Gabriel will ihn ausdruecklich behalten (im Vorbild `_showSystemMailboxModal`).
    # Sind keine System-Postfaecher eingetragen, kommt 404 -- die Oberflaeche
    # blendet den Knopf dann still aus. Bewusst KEINE leere Liste mit
    # Aufklappfeld: ein Betrachter ohne Postfaecher sieht aus wie ein Fehler.
    def _system_liste() -> list[dict]:
        return [
            {"schluessel": eintrag["key"], "adresse": eintrag["email"], "name": eintrag["role"],
             # Zweitnamen aus dem Vorbild, damit eine aeltere Oberflaeche nicht
             # ins Leere greift.
             "key": eintrag["key"], "email": eintrag["email"], "role": eintrag["role"]}
            for eintrag in system_postfaecher(_zugaenge())
        ]

    async def _systempostfaecher(request):
        await mensch_aufloesen(request)
        postfaecher = _system_liste()
        if not postfaecher:
            return JSONResponse(
                {"ok": False, "error": "keine_systempostfaecher"}, status_code=404)
        return JSONResponse({"ok": True, "postfaecher": postfaecher, "boxes": postfaecher})

    @app.post("/api/postfach/systempostfaecher")
    async def postfach_systempostfaecher(request: Request):
        try:
            return await _systempostfaecher(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/system/liste")
    async def postfach_system_liste(request: Request):
        try:
            return await _systempostfaecher(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/system/nachrichten")
    async def postfach_system_nachrichten(request: Request):
        try:
            await mensch_aufloesen(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                system_nachrichten, _zugaenge(),
                str(_feld(rumpf, "schluessel", "key", vorgabe="")),
                _zahl(_feld(rumpf, "grenze", "limit"), 40)))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/system/lesen")
    async def postfach_system_lesen(request: Request):
        try:
            await mensch_aufloesen(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                system_nachricht, _zugaenge(),
                str(_feld(rumpf, "schluessel", "key", vorgabe="")),
                _zahl(_feld(rumpf, "index", "idx"), 0)))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/system/loeschen")
    async def postfach_system_loeschen(request: Request):
        try:
            await mensch_aufloesen(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                system_loeschen, _zugaenge(),
                str(_feld(rumpf, "schluessel", "key", vorgabe="")),
                _zahl(_feld(rumpf, "index", "idx"), 0)))
        except Exception as exc:
            return antwort_auf_fehler(exc)

    @app.post("/api/postfach/system/senden")
    async def postfach_system_senden(request: Request):
        try:
            user_id, session_id = await mensch_aufloesen(request)
            rumpf = await _rumpf(request)
            return JSONResponse(await asyncio.to_thread(
                system_senden, db, _zugaenge(),
                str(_feld(rumpf, "schluessel", "key", vorgabe="")),
                user_id=user_id, session_id=session_id,
                an=str(_feld(rumpf, "an", "to", vorgabe="")),
                betreff=str(_feld(rumpf, "betreff", "subject", vorgabe="")),
                inhalt=str(_feld(rumpf, "text", "body", vorgabe="")),
                cc=str(_feld(rumpf, "kopie", "cc", vorgabe="")),
                in_reply_to=str(_feld(rumpf, "antwort_auf", "in_reply_to", vorgabe="")),
                references=str(_feld(rumpf, "referenzen", "references", vorgabe=""))))
        except Exception as exc:
            return antwort_auf_fehler(exc)
