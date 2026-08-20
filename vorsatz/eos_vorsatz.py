#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EntityOS Vorsatz-Pruefer -- die zweite Haelfte des Kreises.

Gabriel 2026-08-20: die Metakognition wird NICHT aus Frank portiert (die drei
Module dort haengen an consciousness_daemon/AURA/sanctum/E-PQ), sondern gegen
EntityOS neu gebaut -- auf dem, was hier schon laeuft.

WAS ES SCHON GAB und was fehlte:

    Beobachten   ✅  mv_prestage_turns.epistemik, vp_paket_log, zero_luecke
    Hypothese    ✅  eos-hypothesen-generator -> folgerung status='offen'
    Pruefen      ❌  NICHTS. 11 offene Folgerungen, keine je nachgemessen.
    Revidieren   ❌  NICHTS. Kein Weg nach 'gestuetzt'/'widerlegt'.

Ein Kreis, der nur die erste Haelfte hat, ist keine Metakognition, sondern eine
wachsende Liste. Genau das war der Zustand: der Generator schrieb weiter
Hypothesen, und keine einzige wurde je erledigt -- auch die nicht, deren Luecke
laengst geschlossen war.

WAS DIESES MODUL TUT -- mechanisch, ohne Modellaufruf:
Fuer jede offene Folgerung des Generators wird die Behauptung NACHGEMESSEN.
Die Behauptung ist immer von derselben Form: "zu [woerter] fehlt etwas". Also
wird genau danach noch einmal gesucht:

  * Wiki-Luecke    -> gibt es INZWISCHEN einen echten Artikel dazu?
  * Selbstpruefung -> gibt es inzwischen einen Artikel ODER einen Eintrag im
                      dauerhaften Gedaechtnis dazu?

Bei einer WIKI-LUECKE ("es fehlt ein Artikel") widerlegt ein gefundener Artikel
die Behauptung vollstaendig -- genau darueber war sie. Der Vorsatz ist erledigt,
mit Beleg.

Bei einer SELBSTPRUEFUNG ("es fehlt eine belegte Angabe") wird NICHTS
automatisch geschlossen: ein Artikel mit denselben Woertern beweist nicht, dass
die gesuchte Angabe darin steht. Der Fund wird als KANDIDAT festgehalten, der
Vorsatz bleibt offen. (Gemessen 2026-08-20: sonst haette ein Artikel ueber
Gabriels Rolle die Luecke "document root path" fuer geschlossen erklaert.)

Alles Offene steht in /var/lib/clay/vorsaetze.json, wo Zero es lesen und daran
arbeiten kann -- Kandidaten inklusive, als Hinweis, wo zu suchen ist.

⚠️ ZWEI FALLEN, beide bewusst behandelt:
1. Die Luecken-Notizen der Anlage tragen den Suchtext im Titel und wuerden
    jede Suche nach sich selbst "erfolgreich" machen. Der Kreis wuerde sich
    selbst schliessen, ohne dass irgendjemand etwas gelernt haette. Deshalb
    sind art='zero_luecke', epistemic_class='MECHANICAL_GAP_HYPOTHESIS' und
    alles von 'eos-hypothesen-generator' von der Suche AUSGESCHLOSSEN -- die
    gleiche Regel wie in clayverse/retrieval.py.
2. 'gestuetzt' wird NIE vergeben. Dass eine Suche wieder nichts findet, ist
    kein Beweis, dass etwas fehlt -- es kann auch an der Suche liegen. Eine
    unbestaetigte Hypothese bleibt offen. Nur das Gegenteil ist beweisbar:
    ein gefundener Artikel widerlegt "es fehlt einer".
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.environ.get("CLAYVERSE_DB_PATH", "/var/lib/clay/wiki.db")
VORSATZ_DATEI = Path("/var/lib/clay/vorsaetze.json")
AUTOR = "eos-hypothesen-generator"
PRUEFER = "eos-vorsatz-pruefer"
MAX_TREFFER = 5

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
LOG = logging.getLogger("eos-vorsatz")

# Woerter aus gilt_fuer: "ClayVerse · Wiki-Luecke · a b c" / "EntityOS · Selbstpruefung · a b c"
_GILT_FUER = re.compile(r"·\s*(Wiki-Luecke|Selbstpruefung)\s*·\s*(.+)$")


def connect():
    con = sqlite3.connect(f"file:{DB_PATH}?mode=rwc", uri=True, timeout=30)
    con.row_factory = sqlite3.Row
    return con


def zerlegen(gilt_fuer: str):
    """(art, woerter) aus dem gilt_fuer-Feld. None, wenn es nicht vom Generator stammt."""
    m = _GILT_FUER.search(gilt_fuer or "")
    if not m:
        return None
    woerter = [w for w in re.split(r"\s+", m.group(2).strip()) if len(w) > 2]
    return (m.group(1), woerter) if woerter else None


def echte_artikel(con, woerter: list) -> list:
    """Artikel zu diesen Woertern -- OHNE die Notizen der Anlage ueber sich selbst.

    Ohne diesen Ausschluss faende die Pruefung immer den Luecken-Artikel, den
    der Generator selbst geschrieben hat, und wuerde jede Luecke sofort fuer
    geschlossen erklaeren. Siehe Modul-Kopf, Falle 1.
    """
    if not woerter:
        return []
    match = " AND ".join(f'"{w}"' for w in woerter)
    try:
        rows = con.execute(
            "SELECT s.artikel_id AS artikel_id, s.titel AS titel "
            "FROM fts_index_artikel f "
            "JOIN artikel_suchtext s ON s.id = f.rowid "
            "LEFT JOIN artikel a ON a.id = s.artikel_id "
            "WHERE fts_index_artikel MATCH ? "
            "  AND (a.art IS NULL OR a.art <> 'zero_luecke') "
            "  AND (a.epistemic_class IS NULL OR a.epistemic_class <> 'MECHANICAL_GAP_HYPOTHESIS') "
            "  AND (a.zuletzt_von IS NULL OR a.zuletzt_von <> ?) "
            "ORDER BY bm25(fts_index_artikel) LIMIT ?",
            (match, AUTOR, MAX_TREFFER),
        ).fetchall()
    except sqlite3.Error as fehler:
        LOG.warning("Artikelsuche fehlgeschlagen (%s): %s", woerter, fehler)
        return []
    return [dict(r) for r in rows]


def gedaechtnis(con, woerter: list) -> list:
    """Eintraege im dauerhaften Gedaechtnis, die ALLE Woerter enthalten.

    Bewusst simpel und wortweise: das Gedaechtnis ist klein (Dutzende Zeilen),
    ein Volltextindex waere hier Aufwand ohne Gewinn.
    """
    if not woerter:
        return []
    try:
        rows = con.execute(
            "SELECT memory_id, subject, value FROM durable_memory ORDER BY ts DESC LIMIT 500"
        ).fetchall()
    except sqlite3.Error as fehler:
        LOG.warning("Gedaechtnis nicht lesbar: %s", fehler)
        return []
    treffer = []
    for r in rows:
        text = f"{r['subject'] or ''} {r['value'] or ''}".lower()
        if all(w.lower() in text for w in woerter):
            treffer.append({"memory_id": r["memory_id"], "value": (r["value"] or "")[:200]})
        if len(treffer) >= MAX_TREFFER:
            break
    return treffer


def beleg_anhaengen(con, folgerung_id: int, art: str, beleg_id: str) -> None:
    """Beleg anhaengen, Doppel schadlos ueberspringen (UNIQUE auf der Tabelle)."""
    try:
        con.execute(
            "INSERT OR IGNORE INTO folgerung_beleg (folgerung_id, beleg_art, beleg_id) "
            "VALUES (?,?,?)", (folgerung_id, art, beleg_id))
    except sqlite3.Error as fehler:
        LOG.warning("Beleg %s/%s nicht angehaengt: %s", art, beleg_id, fehler)


def pruefen(dry_run: bool = False) -> dict:
    con = connect()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
    erledigt, offen = [], []
    try:
        rows = con.execute(
            "SELECT id, aussage, begruendung, gilt_fuer, zeit FROM folgerung "
            "WHERE autor=? AND status='offen' ORDER BY id", (AUTOR,)).fetchall()
        LOG.info("Offene Vorsaetze: %d", len(rows))

        for r in rows:
            zerlegt = zerlegen(r["gilt_fuer"])
            if not zerlegt:
                LOG.info("#%d uebersprungen: gilt_fuer nicht deutbar (%r)", r["id"], r["gilt_fuer"])
                continue
            quelle_art, woerter = zerlegt
            artikel = echte_artikel(con, woerter)
            erinnert = gedaechtnis(con, woerter) if quelle_art == "Selbstpruefung" else []

            if not artikel and not erinnert:
                offen.append({"folgerung_id": r["id"], "art": quelle_art,
                              "woerter": woerter, "aussage": r["aussage"][:300],
                              "seit": r["zeit"]})
                continue

            if quelle_art == "Selbstpruefung":
                # KEIN automatisches Urteil -- siehe Modul-Historie 2026-08-20.
                # Die Behauptung ist ueber eine TATSACHE, gemessen wird nur
                # Wortueberlappung. Der Fund ist ein Hinweis, wo zu suchen ist.
                offen.append({
                    "folgerung_id": r["id"], "art": quelle_art,
                    "woerter": woerter, "aussage": r["aussage"][:300],
                    "seit": r["zeit"],
                    "kandidaten": {
                        "artikel": [a["artikel_id"] for a in artikel],
                        "gedaechtnis": [m["memory_id"] for m in erinnert],
                        "hinweis": ("Wortueberlappung, kein Beweis. Nachsehen, ob die "
                                    "gesuchte Angabe dort WIRKLICH steht -- dann schliessen."),
                    },
                })
                LOG.info("#%d bleibt offen, %d Artikel- und %d Gedaechtnis-Kandidat(en)",
                         r["id"], len(artikel), len(erinnert))
                continue

            # Wiki-Luecke: die Behauptung war "es fehlt ein ARTIKEL" -- genau das
            # ist gemessen worden, also ist sie widerlegt.
            wo = []
            if artikel:
                wo.append(f"{len(artikel)} Artikel (z.B. {artikel[0]['artikel_id']})")
            if erinnert:
                wo.append(f"{len(erinnert)} Gedaechtniseintrag/-eintraege")
            vermerk = (f" [{now} vom {PRUEFER} nachgemessen: zu [{' '.join(woerter)}] "
                       f"gibt es inzwischen {' und '.join(wo)} -- die Behauptung 'es fehlt "
                       f"ein Artikel' ist damit widerlegt, die Luecke geschlossen. Selbst "
                       f"geschriebene Luecken-Notizen waren von der Suche ausgeschlossen.]")
            if dry_run:
                LOG.info("[DRY-RUN] #%d wuerde widerlegt: %s", r["id"], " und ".join(wo))
            else:
                con.execute(
                    "UPDATE folgerung SET status='widerlegt', begruendung = COALESCE(begruendung,'') || ? "
                    "WHERE id=? AND status='offen'", (vermerk, r["id"]))
                for a in artikel:
                    beleg_anhaengen(con, r["id"], "artikel", a["artikel_id"])
                for m in erinnert:
                    beleg_anhaengen(con, r["id"], "protokoll", m["memory_id"])
                con.commit()
                LOG.info("#%d widerlegt (Luecke geschlossen): %s", r["id"], " und ".join(wo))
            erledigt.append({"folgerung_id": r["id"], "woerter": woerter, "gefunden": wo})

        stand = {
            "zeit": now,
            "geprueft": len(rows),
            "erledigt": len(erledigt),
            "offen": len(offen),
            "vorsaetze": offen,
            "hinweis": ("Offene Vorsaetze sind Wissensluecken, die die Anlage an sich selbst "
                        "bemerkt hat und die noch niemand geschlossen hat. 'gestuetzt' wird "
                        "bewusst nie vergeben: dass eine Suche nichts findet, beweist nicht, "
                        "dass etwas fehlt."),
        }
        if not dry_run:
            # Erst daneben schreiben, dann umbenennen: ein halb geschriebener
            # Vorsatzzettel waere schlimmer als ein alter.
            tmp = VORSATZ_DATEI.with_suffix(".json.neu")
            tmp.write_text(json.dumps(stand, ensure_ascii=False, indent=2) + "\n")
            os.replace(tmp, VORSATZ_DATEI)
        return stand
    finally:
        con.close()


def cmd_stand() -> dict:
    con = connect()
    try:
        nach_status = {r[0]: r[1] for r in con.execute(
            "SELECT status, COUNT(*) FROM folgerung WHERE autor=? GROUP BY status", (AUTOR,))}
        return {"folgerungen_des_generators": nach_status,
                "vorsatzdatei": str(VORSATZ_DATEI),
                "vorsatzdatei_vorhanden": VORSATZ_DATEI.exists()}
    finally:
        con.close()


def main() -> int:
    p = argparse.ArgumentParser(description="EntityOS Vorsatz-Pruefer")
    p.add_argument("befehl", nargs="?", default="pruefen", choices=["pruefen", "stand"])
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if a.befehl == "stand":
        print(json.dumps(cmd_stand(), ensure_ascii=False, indent=2))
        return 0
    ergebnis = pruefen(dry_run=a.dry_run)
    print(json.dumps({k: v for k, v in ergebnis.items() if k != "vorsaetze"},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
