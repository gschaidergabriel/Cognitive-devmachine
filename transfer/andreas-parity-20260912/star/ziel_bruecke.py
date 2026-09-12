#!/usr/bin/env python3
"""ziel_bruecke.py -- Bruecke zwischen zwei bisher unverbundenen "Wollen"-
Systemen (Gabriel-Auftrag 2026-09-11, paket-1789133830613-17102f):

    entityos_arbeitspaket   unified.db   Koordinator-Ledger (stern.py
                                          handoff()/reconcile()) -- SITZUNGS-
                                          gebunden, ohne Beleg kein 'fertig'.
    goals                   consciousness.db   FranKensteins eigene, ECHT
                                          verfolgte Ziele (ziele.py
                                          offene()/waehlen()/verfolgt()).

Gabriel woertlich: "wenn ich dir (dem Koordinator) einen Auftrag gebe, muss
das im GRID in ein Goal umgelegt werden ... autark, ueber Jahre wenn es sein
muss."

⭐ ENTSCHEIDUNG: WELCHER MOMENT WIRD ZUM GOAL, und warum handoff() statt
UserPromptSubmit:

Ein UserPromptSubmit-Hook sieht nur rohen Text, OHNE Urteil, ob das gerade
ein "echter Auftrag" oder ein "ja mach weiter"/"ok" ist -- genau das
Urteil, das die Delegationsregel in CLAUDE.md dem Koordinator ausdruecklich
vorbehaelt ("einfache, eindeutige, kleine Aenderungen macht der Koordinator
SELBST, ohne Agent-Overhead"). handoff() ist bereits der Moment, in dem der
Koordinator dieses Urteil GEFAELLT hat: er hat entschieden, dass hier echte,
mehrschrittige Bauarbeit vorliegt, die einen Subagenten braucht -- und hat
dafuer bereits `auftrag`/`womit`/`warum` als saubere Kapsel-Texte formuliert.
Kleine Ein-Zeiler-Fixes, die der Koordinator selbst erledigt, durchlaufen
handoff() nie UND sind typischerweise binnen derselben Sitzung fertig --
sitzungsuebergreifende Verfolgung waere dort ohnehin wirkungslos. Der Bau-
Aufwand, der wirklich "ueber Jahre" ueberleben muss, IST der, der delegiert
wird. Bruecke sitzt deshalb an genau zwei Stellen:

    handoff()   -> goal_fuer_handoff()      (Goal ENTSTEHT, Verknuepfung)
    reconcile() -> goal_bei_reconcile()      (Goal SCHLIESST NUR bei echtem
                                               Beleg, sonst bleibt es aktiv)

⭐⭐ "GESCHEITERT" SCHLIESST DAS GOAL NICHT. reconcile() setzt stand=
'gescheitert' sowohl bei echtem Scheitern als auch bei ungueltigem/fehlendem
Beleg ("unbelegte_behauptung") -- in BEIDEN Faellen ist die Sache nicht
erledigt, nur der Versuch war's nicht wert, als Erfolg gezaehlt zu werden.
Genau das ist "unerbittlich verfolgt": das Goal bleibt 'active', bekommt nur
eine fortschritt()-Notiz, und die naechste Sitzung sieht es wieder ueber den
SessionStart-Hook. Nur ein GEPRUEFTER Beleg (stand='fertig') schliesst es.

Getrennte DB-Dateien (unified.db vs. consciousness.db) -- keine FK ueber
Dateigrenzen moeglich, deshalb eine eigene, kleine Verknuepfungstabelle
`arbeitspaket_ziel` HIER in unified.db (nicht in consciousness.db, weil
ziele.py deren Schema nicht kennt und nicht kennen soll).
"""
from __future__ import annotations

import importlib.util
import os
import time
from typing import Optional

# ziele.py ist bind-gemountet -- beide Pfade sind DIESELBE Datei. Beide
# probieren, falls einer der beiden Mountpunkte in einer Umgebung fehlt.
_ZIELE_PFADE = (
    "/var/lib/entityos/voice/ziele.py",
    "/opt/entityos/voice/ziele.py",
)

_ZIELE_MODUL_CACHE = None
_ZIELE_MODUL_VERSUCHT = False

_LINK_DDL = (
    "CREATE TABLE IF NOT EXISTS arbeitspaket_ziel("
    "paket_id TEXT PRIMARY KEY, goal_id INTEGER NOT NULL, erstellt REAL NOT NULL)"
)


def _noop_log(_s: str) -> None:
    return None


def ziele_modul():
    """Laedt ziele.py per Dateipfad (kein Package, kein sys.path-Zwang).
    Cached fuer den Prozess -- ein fehlender Pfad bleibt fehlend, kein
    wiederholtes Dateisystem-Abklopfen pro Aufruf."""
    global _ZIELE_MODUL_CACHE, _ZIELE_MODUL_VERSUCHT
    if _ZIELE_MODUL_CACHE is not None or _ZIELE_MODUL_VERSUCHT:
        return _ZIELE_MODUL_CACHE
    _ZIELE_MODUL_VERSUCHT = True
    for pfad in _ZIELE_PFADE:
        if os.path.isfile(pfad):
            try:
                spec = importlib.util.spec_from_file_location("entityos_ziele_bruecke", pfad)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
                _ZIELE_MODUL_CACHE = mod
                return mod
            except Exception:
                continue
    return None


def sicherstellen_tabelle(c) -> None:
    c.execute(_LINK_DDL)


def goal_fuer_handoff(c, paket_id: str, auftrag: str, warum: str, log=None) -> Optional[int]:
    """Bei handoff(): legt (wenn Textqualitaet reicht, siehe ziele._taugt())
    ein echtes Goal an und verlinkt paket_id<->goal_id in unified.db.
    `c` ist eine bereits offene SCHREIB-Verbindung von stern.py (dieselbe
    Transaktion wie das INSERT in entityos_arbeitspaket -- kein zweiter
    Commit-Pfad). Gibt goal_id oder None (z.B. Textqualitaet nicht
    ausreichend, ziele.py nicht erreichbar) -- nie erfunden, nie geraten."""
    _log = log or _noop_log
    z = ziele_modul()
    if z is None:
        _log("[ZIEL-BRUECKE] ziele.py nicht gefunden -- kein Goal angelegt")
        return None
    text = f"Gabriel-Auftrag: {auftrag or ''}".strip()
    if warum:
        text = f"{text} ({warum})"
    text = text[:220]
    try:
        goal_id = z.anlegen(text, kategorie="koordinator_auftrag", prioritaet=0.7, log=_log)
    except Exception as e:
        _log(f"[ZIEL-BRUECKE] anlegen() fehlgeschlagen: {e}")
        return None
    if goal_id is None:
        _log(f"[ZIEL-BRUECKE] Goal fuer paket {paket_id} abgelehnt (Textqualitaet _taugt())")
        return None
    try:
        sicherstellen_tabelle(c)
        c.execute(
            "INSERT OR REPLACE INTO arbeitspaket_ziel (paket_id, goal_id, erstellt) VALUES (?,?,?)",
            (paket_id, goal_id, time.time()),
        )
    except Exception as e:
        _log(f"[ZIEL-BRUECKE] Verlinkung paket={paket_id} goal={goal_id} fehlgeschlagen: {e}")
        return goal_id
    try:
        z.verfolgt(goal_id, log=_log)
    except Exception:
        pass
    return goal_id


def goal_bei_reconcile(c, paket_id: str, neuer_stand: str, ergebnis: str, log=None) -> None:
    """Bei reconcile(): 'fertig' (echter, geprueft Beleg) -> Goal 'done'.
    Jeder andere Stand ('gescheitert', egal ob echtes Scheitern oder
    unbelegte_behauptung) -> NUR eine fortschritt()-Notiz, Goal bleibt
    'active'. Das ist die mechanische Umsetzung von "unerbittlich
    verfolgt": ein einzelner gescheiterter Versuch loescht den Auftrag
    nicht, er bleibt fuer die naechste Sitzung sichtbar (offene_gabriel_
    ziele() unten)."""
    _log = log or _noop_log
    z = ziele_modul()
    if z is None:
        return
    try:
        sicherstellen_tabelle(c)
        row = c.execute(
            "SELECT goal_id FROM arbeitspaket_ziel WHERE paket_id=?", (paket_id,)
        ).fetchone()
    except Exception as e:
        _log(f"[ZIEL-BRUECKE] Nachschlagen paket={paket_id} fehlgeschlagen: {e}")
        return
    if not row:
        return  # dieses Paket kam ueber paket-anlegen o.ae., nie ueber handoff() -- kein Goal verlinkt
    goal_id = row[0]
    text = (ergebnis or "").strip()[:300]
    try:
        if neuer_stand == "fertig":
            z.fortschritt(goal_id, f"Paket {paket_id} fertig, Beleg geprueft: {text}", log=_log)
            z.abschliessen(
                goal_id, "done",
                f"entityos_arbeitspaket {paket_id} mit gueltigem Beleg abgeschlossen: {text}",
                log=_log,
            )
        else:
            z.fortschritt(
                goal_id,
                f"Paket {paket_id} Versuch gescheitert/kein gueltiger Beleg ({neuer_stand}): {text}",
                log=_log,
            )
            # status bleibt bewusst 'active' -- kein abschliessen() hier.
    except Exception as e:
        _log(f"[ZIEL-BRUECKE] goal_bei_reconcile paket={paket_id} goal={goal_id} fehler: {e}")


def goal_bei_verdacht(c, paket_id: str, grund: str, log=None) -> None:
    """PHASE 24-Anschluss (arbeitspaket_belege_nachpruefen): ein frueher
    gueltiger Beleg stimmt jetzt nicht mehr. Kein automatisches Zuruecksetzen
    von stand='fertig' (das bleibt bewusst Menschensache, siehe stern.py-
    Docstring der Nachpruefung) -- aber das verlinkte Goal, das schon als
    'done' geschlossen war, bekommt eine sichtbare Notiz. Reaktiviert das
    Goal NICHT automatisch (Status bleibt 'done') -- nur die Spur, damit ein
    Mensch/die naechste Pruefung sieht, dass die Grundlage bruecklig wurde."""
    _log = log or _noop_log
    z = ziele_modul()
    if z is None:
        return
    try:
        row = c.execute(
            "SELECT goal_id FROM arbeitspaket_ziel WHERE paket_id=?", (paket_id,)
        ).fetchone()
    except Exception:
        row = None
    if not row:
        return
    try:
        z.fortschritt(row[0], f"⚠ Beleg-Nachpruefung: {grund}", log=_log)
    except Exception as e:
        _log(f"[ZIEL-BRUECKE] goal_bei_verdacht paket={paket_id} fehler: {e}")


def offene_gabriel_ziele(c, limit: int = 5) -> list:
    """Fuer SessionStart: offene/laufende Pakete MIT verlinktem, noch
    aktivem Goal -- genau die Schnittmenge, die eine neue Sitzung wieder
    aufnehmen soll. `c` ist eine offene LESE-Verbindung von stern.py
    (unified.db). Liefert [(paket_id, goal_id, auftrag, stand, alter_tage)]."""
    z = ziele_modul()
    if z is None:
        return []
    try:
        sicherstellen_tabelle(c)
        rows = c.execute(
            "SELECT az.paket_id, az.goal_id, ap.auftrag, ap.stand, ap.geaendert "
            "FROM arbeitspaket_ziel az JOIN entityos_arbeitspaket ap "
            "ON ap.paket_id = az.paket_id "
            "WHERE ap.stand IN ('offen','laeuft') ORDER BY ap.geaendert DESC LIMIT ?",
            (limit,),
        ).fetchall()
    except Exception:
        return []
    ergebnis = []
    for paket_id, goal_id, auftrag, stand, geaendert in rows:
        try:
            with z._db() as zc:  # noqa: SLF001 -- ziele.py hat keine oeffentliche Einzel-Lesefunktion, nur offene()/waehlen() (Mehrzeilen)
                grow = zc.execute(
                    "SELECT status FROM goals WHERE id=?", (goal_id,)
                ).fetchone()
        except Exception:
            grow = None
        if not grow or grow[0] != "active":
            continue  # bereits (von wem auch immer, z.B. dem 4B-Urteil in abschliessen()) geschlossen
        alter_tage = max(0.0, (time.time() - (geaendert or time.time())) / 86400.0)
        ergebnis.append((paket_id, goal_id, auftrag, stand, alter_tage))
    return ergebnis


def agent_erfassen(payload: dict, log=None) -> Optional[int]:
    """Einen Agentenstart als ZIEL erfassen -- automatisch, im PreToolUse.

    ⭐⭐⭐ 2026-09-12, Gabriels genaue Diagnose, woertlich: **"du benennst es
    selbst jedes Mal ganz genau, aber erfasst es nicht"** -- und, nachdem ich
    es als mein Versaeumnis eingeordnet hatte, die Korrektur: **"ich habe das
    nie gefunden, du benennst es, ich mach Copy-Paste, weil ich merke, du
    checkst es nicht -- das ist ne reine Engineering-Luecke im System."**

    Er hat recht, und die Unterscheidung ist wichtig: der Auftragstext, den
    ich einem Bau-Agenten mitgebe, ist regelmaessig vollstaendig und praezise
    formuliert. Das Benennen funktioniert. Was fehlte, war jeder Weg von
    diesem Text in den Zielspeicher -- also eine fehlende LEITUNG, kein
    Denkfehler und kein Erinnerungsproblem.

    ⚠️ DER BEFUND, gezaehlt: Ziele der Kategorie 'koordinator_auftrag'
    entstanden bisher AUSSCHLIESSLICH in `goal_fuer_handoff()`, also nur
    dann, wenn jemand `stern.py handoff` aufruft (CLAUDE.md PHASE 5). In der
    Nacht zum 2026-09-12 wurden fuenf Bau-Agenten ueber das Agent-Werkzeug
    gestartet, ohne handoff -- und die letzte erfasste Zeile in `goals`
    stammte folgerichtig von 00:21 Uhr, waehrend die Arbeit bis 07:00 Uhr
    weiterlief. Fuenf vollstaendig ausformulierte Auftraege, null erfasst.

    ⚠️ WARUM DAS NICHT "kuenftig an handoff denken" heisst: dieselbe
    Aufforderung steht seit dem 2026-08-26 in CLAUDE.md und wurde fuenfmal
    in einer Nacht uebergangen. Eine Regel, die an mein Erinnern gebunden
    ist, ist in genau dem Moment nicht da, in dem sie gebraucht wird. Der
    Hook sieht den Werkzeugaufruf ohnehin -- also wird hier erfasst und
    nicht ermahnt.

    Vertrag: fail-silent, schnell (PreToolUse-Budget 0.4 s), idempotent
    ueber einen Texthash -- derselbe Agentenstart erzeugt kein zweites Ziel.
    Gibt die Ziel-Id zurueck oder None."""
    _log = log or _noop_log
    try:
        if (payload or {}).get("tool_name") != "Agent":
            return None
        ti = (payload or {}).get("tool_input") or {}
        auftrag = (ti.get("prompt") or "").strip()
        titel = (ti.get("description") or "").strip()
        if not auftrag:
            return None
        z = ziele_modul()
        if z is None:
            return None
        # Der Zieltext: kurze Bezeichnung + Anfang des Auftrags. Der volle
        # Prompt kann tausende Zeichen haben -- ein Ziel ist eine Absicht,
        # kein Pflichtenheft. Das Pflichtenheft steht im Arbeitspaket.
        import hashlib
        marke = hashlib.sha256(auftrag.encode("utf-8")).hexdigest()[:12]
        text = (f"Gabriel-Auftrag (Agent): {titel or auftrag[:60]} "
                f"-- {' '.join(auftrag.split())[:260]} [a:{marke}]")
        # Idempotenz: haengt der Hash schon an einem Ziel, war dieser
        # Agentenstart schon da (Wiederholung nach Fehlschlag, zweiter
        # Anlauf desselben Auftrags).
        try:
            import sqlite3 as _s
            pfad = getattr(z, "DB_PATH", None) or os.path.expanduser(
                "~/.local/share/agentzero/consciousness.db")
            with _s.connect(f"file:{pfad}?mode=ro", uri=True, timeout=3.0) as c:
                if c.execute("SELECT 1 FROM goals WHERE description LIKE ? "
                             "LIMIT 1", (f"%[a:{marke}]%",)).fetchone():
                    return None
        except Exception:
            pass
        neue_id = z.anlegen(text, kategorie="koordinator_auftrag",
                            prioritaet=0.75, log=_log)
        if neue_id:
            _log(f"[ZIEL-BRUECKE] Agentenstart als Ziel {neue_id} erfasst: "
                 f"{titel or auftrag[:50]!r}")
        return neue_id
    except Exception as e:
        _log(f"[ZIEL-BRUECKE] Agentenerfassung ausgefallen "
             f"({type(e).__name__}: {e})")
        return None


# Schalter fuer NUR diesen Mechanismus (agent_erfassen() bleibt davon
# unberuehrt) -- Vorgabe aus dem Bauauftrag: jeder neue Mechanismus muss
# einzeln abschaltbar sein, ohne die anderen mitzuschleifen.
AGENT_SCHLIESSEN_AN = os.environ.get(
    "ZIEL_BRUECKE_AGENT_SCHLIESSEN", "1") != "0"


def agent_abschliessen(payload: dict, fehlerhaft: bool = False,
                        log=None) -> Optional[int]:
    """Schliesst die Luecke, die agent_erfassen() offen liess: ein per
    Agent-Werkzeug erfasstes Ziel blieb bisher fuer immer 'active', weil es
    im PostToolUse ueberhaupt keine Behandlung fuer tool_name=='Agent' gab
    (mit grep gegen stern.py bestaetigt -- Nullstellen). Ohne diese Zeile
    haetten agent_erfassen()'s Ziele auf Dauer denselben Fehler nur
    verschoben: erfasst, aber nie wieder gelesen.

    ⚠️ ABSICHTLICH KEIN abschliessen(status='done'): ob ein Agentenlauf
    sein Ziel tatsaechlich erreicht hat, ist ein Urteil, keine Heuristik --
    genau das, was `ziele.abschliessen()`s eigener Docstring dem 4B
    vorbehaelt ("GRID soll das 4B fuer Urteile nutzen, die keine reine
    Heuristik kann"). Ein PostToolUse-Hook mit 0,4s Budget kann das nicht
    leisten, und ein falsches 'done' waere genau die Selbstbescheinigung,
    vor der ziele.py selbst warnt ("Ein System, das sich selbst Fortschritt
    bescheinigt, misst nichts mehr."). Stattdessen: `fortschritt()` --
    faktisch, unstrittig, ohne Erfolgsbehauptung. Das Ziel bleibt sichtbar
    'active' bis jemand (Mensch oder 4B-Urteil) es wirklich abschliesst --
    aber es traegt jetzt eine Spur, dass der Agent zurueckkam, statt fuer
    immer stumm auf 00:21 Uhr stehenzubleiben.

    Vertrag wie agent_erfassen(): fail-silent, schnell, eigener Schalter
    (ZIEL_BRUECKE_AGENT_SCHLIESSEN=0 schaltet NUR diese Funktion ab)."""
    _log = log or _noop_log
    if not AGENT_SCHLIESSEN_AN:
        return None
    try:
        if (payload or {}).get("tool_name") != "Agent":
            return None
        ti = (payload or {}).get("tool_input") or {}
        auftrag = (ti.get("prompt") or "").strip()
        if not auftrag:
            return None
        z = ziele_modul()
        if z is None:
            return None
        import hashlib
        marke = hashlib.sha256(auftrag.encode("utf-8")).hexdigest()[:12]
        import sqlite3 as _s
        pfad = getattr(z, "INNENWELT_DB", None) or os.path.expanduser(
            "~/.local/share/agentzero/consciousness.db")
        ziel_id = None
        with _s.connect(f"file:{pfad}?mode=ro", uri=True, timeout=3.0) as c:
            row = c.execute(
                "SELECT id FROM goals WHERE description LIKE ? "
                "AND status='active' LIMIT 1", (f"%[a:{marke}]%",)).fetchone()
            if row:
                ziel_id = row[0]
        if not ziel_id:
            # Kein offenes Ziel zu diesem Hash -- entweder agent_erfassen()
            # war abgeschaltet, oder es wurde schon anderweitig geschlossen.
            return None
        text = ("Agent-Werkzeug zurueckgekehrt (PostToolUse)"
                + (" -- mit Fehler (tool_response.is_error)" if fehlerhaft
                   else "")
                + " -- automatisch erfasst, Abschluss/Bewertung bleibt "
                  "offen (siehe Transkript, keine automatische "
                  "Erfolgsbehauptung).")
        if z.fortschritt(ziel_id, text, log=_log):
            _log(f"[ZIEL-BRUECKE] Ziel {ziel_id}: Ruecklauf des "
                 f"Agenten vermerkt (fehlerhaft={fehlerhaft}).")
            return ziel_id
        return None
    except Exception as e:
        _log(f"[ZIEL-BRUECKE] Agentenabschluss ausgefallen "
             f"({type(e).__name__}: {e})")
        return None


if __name__ == "__main__":
    import sqlite3
    import sys

    z = ziele_modul()
    print(f"ziele.py gefunden: {z is not None} ({getattr(z, '__file__', '?')})")
    unified = os.path.expanduser("~/.local/share/agentzero/unified.db")
    if len(sys.argv) > 1 and sys.argv[1] == "offene":
        with sqlite3.connect(unified) as c:
            for zeile in offene_gabriel_ziele(c, limit=20):
                print(zeile)
