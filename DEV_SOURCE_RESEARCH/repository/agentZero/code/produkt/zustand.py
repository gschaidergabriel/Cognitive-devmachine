"""Ein lesender Blick auf den kanonischen Zustand -- fuer /api/zustand.

Nur Zahlen, die es wirklich gibt. Was diese Datenbank nicht fuehrt, kommt als
`None` zurueck und wird oben als „—" gezeigt.

⭐ Der Unterschied, um den es hier geht: `0` ist eine Behauptung ("es gibt
keine"), `None` ist eine Auskunft ("ich weiss es nicht"). Auf einer
Betriebsseite ist das der ganze Punkt -- ein Platzhalter, der wie ein Messwert
aussieht, ist der schlimmste Fehler in diesem Projekt. Deshalb faengt jede
Messung ihren eigenen Fehler und faellt auf `None`, nie auf 0 oder False.

Die Oberflaeche liest jedes Feld unter deutschem UND englischem Namen; beide
zu liefern kostet nichts und nimmt der Zuordnung jede Rateoperation.

Dieses Modul schreibt nie. Es legt insbesondere keine Tabellen an -- eine
Lesefunktion, die nebenbei `executescript()` ruft, ist eine Schreiboperation im
Tarnanzug und reisst die Transaktion eines laufenden Zuges auseinander (in
wirte.py schon einmal mit 77 roten Tests bezahlt).
"""
from __future__ import annotations

import sqlite3
from typing import Callable

from .store import UnifiedDB

# Was gezaehlt wird, und aus welcher Tabelle.
# ⚠️ Die Tabellennamen stehen ausschliesslich hier -- nie aus einer Anfrage.
# Ein Tabellenname laesst sich in SQLite nicht binden, deshalb wird er
# formatiert; die feste Herkunft aus diesem Tupel ist der Schutz davor.
_ZAEHLUNGEN = (
    ("zuege", "turns"),
    ("kausalepisoden", "causal_episodes"),
    ("arbeitsraum_episoden", "workspace_episodes"),
    ("pruefpunkte", "checkpoints"),
    ("wirkungen", "effects"),
    ("artikel", "artikel"),
)

_ENGLISCH = {
    "zuege": "turns",
    "kausalepisoden": "causal_episodes",
    "arbeitsraum_episoden": "workspace_episodes",
    "pruefpunkte": "checkpoints",
    "wirkungen": "effects",
    "artikel": "articles",
    "ungelesen": "unread",
    "bereit": "ready",
}


def _zaehle(db: UnifiedDB, tabelle: str) -> int | None:
    """COUNT(*) oder None.

    `artikel` gibt es nur auf der echten wiki.db; auf einer Testdatenbank fehlt
    die Tabelle, und das ist kein Fehler, sondern ehrliches Nichtwissen.
    """
    try:
        zeile = db.db.execute(f"SELECT COUNT(*) FROM {tabelle}").fetchone()
    except sqlite3.Error:
        return None
    return int(zeile[0]) if zeile else None


def _generation(db: UnifiedDB) -> int | None:
    """Direkt aus meta, nicht ueber entity_generation().

    Die Bequemlichkeitsfunktion gibt bei fehlender Zeile eine 1 zurueck -- als
    Vorgabe fuer den Betrieb richtig, als Anzeige falsch: die Oberflaeche wuerde
    „Generation 1" behaupten, wo nichts steht.
    """
    try:
        zeile = db.db.execute("SELECT value FROM meta WHERE key='entity_generation'").fetchone()
    except sqlite3.Error:
        return None
    if not zeile:
        return None
    try:
        return int(zeile[0])
    except (TypeError, ValueError):
        return None


def _messen(mess: Callable | None):
    """Eine Messung ausserhalb der Datenbank -- oder ehrlich None.

    Absichtlich ohne Fehlertext nach aussen: die Postfachmessung kann eine
    Serverantwort tragen, und die gehoert nicht in eine Zustandsantwort.
    """
    if mess is None:
        return None
    try:
        return mess()
    except Exception:
        return None


def zustand(db: UnifiedDB, *, user_id: str,
            ungelesen: Callable[[], int] | None = None,
            bereit: Callable[[], bool] | None = None) -> dict:
    """Der lesbare Zustand fuer einen angemeldeten Menschen.

    `ungelesen` und `bereit` kommen als Aufrufe herein, weil beide ausserhalb
    der Datenbank messen (IMAP bzw. tmux/Bereitschaftssonde). Scheitert einer,
    steht dort `None` -- nicht 0 und nicht False.
    """
    aus: dict[str, object] = {"mensch": user_id, "generation": _generation(db)}
    for name, tabelle in _ZAEHLUNGEN:
        aus[name] = _zaehle(db, tabelle)
    aus["ungelesen"] = _messen(ungelesen)
    aus["bereit"] = _messen(bereit)
    for deutsch, englisch in _ENGLISCH.items():
        aus[englisch] = aus.get(deutsch)
    return aus
