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


_FORMULIERUNGEN = re.compile(r"Formulierungen:\s*(.+?)\)", re.S)


def _formulierungen(aussage: str) -> list:
    """Die echten Luecken-Etiketten aus der Aussage der Folgerung.

    Der Hypothesen-Generator schreibt sie dort als "(Formulierungen: a; b; c)".
    Fehlt der Teil (aeltere Folgerung), bleibt die Liste leer -- dann faellt
    die Arbeit auf die Signaturwoerter zurueck, was schlechter, aber nicht
    falsch ist.
    """
    m = _FORMULIERUNGEN.search(aussage or "")
    if not m:
        return []
    return [t.strip() for t in m.group(1).split(";") if t.strip()][:4]


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


_NUR_HEX = re.compile(r"^[0-9a-f]{32,}$")


def _unlesbar(wert: str) -> bool:
    """Ein Wert, der nur eine Pruefsumme ist, taugt nicht als Kandidat."""
    w = (wert or "").strip()
    return bool(w) and " " not in w and bool(_NUR_HEX.match(w.lower()))


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
    klein = [w.lower() for w in woerter]
    genau, subjekt_exakt, subjekt_teil = [], [], []
    for r in rows:
        wert = (r["value"] or "")
        if _unlesbar(wert):
            continue   # nackte Pruefsumme -- belegt einen Platz und sagt nichts
        subjekt = (r["subject"] or "").lower()
        text = f"{subjekt} {wert}".lower()
        eintrag = {"memory_id": r["memory_id"], "value": wert[:200]}
        if all(w in text for w in klein):
            genau.append({**eintrag, "warum": "alle Woerter kommen vor"})
        elif subjekt and any(w == subjekt for w in klein):
            # Ueber das SUBJEKT -- siehe Modul-Historie 2026-08-20. Zwischen
            # "age" und "gabriel ist 38" liegen zwei Sprachen und ein Zahlwort;
            # Wortabgleich ueberbrueckt das nie, ein gemeinsames Subjekt schon.
            subjekt_exakt.append({**eintrag,
                                  "warum": f"betrifft dasselbe Subjekt ({r['subject']})"})
        elif subjekt and any(w in subjekt for w in klein):
            subjekt_teil.append({**eintrag,
                                 "warum": f"Subjekt enthaelt das Wort ({r['subject']})"})
    return (genau + subjekt_exakt + subjekt_teil)[:MAX_TREFFER]


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
                              "formulierungen": _formulierungen(r["aussage"]),
                              "seit": r["zeit"]})
                continue

            if quelle_art == "Selbstpruefung":
                # KEIN automatisches Urteil -- siehe Modul-Historie 2026-08-20.
                # Die Behauptung ist ueber eine TATSACHE, gemessen wird nur
                # Wortueberlappung. Der Fund ist ein Hinweis, wo zu suchen ist.
                offen.append({
                    "folgerung_id": r["id"], "art": quelle_art,
                    "woerter": woerter, "aussage": r["aussage"][:300],
                    # Was WIRKLICH fehlt, im Wortlaut -- die Signaturwoerter
                    # sind nur das Ordnungsmerkmal. Siehe Modul-Historie.
                    "formulierungen": _formulierungen(r["aussage"]),
                    "seit": r["zeit"],
                    "kandidaten": {
                        "artikel": [a["artikel_id"] for a in artikel],
                        "gedaechtnis": [{"id": m["memory_id"], "wert": m["value"],
                                          "warum": m["warum"]} for m in erinnert],
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
                for m in erinnert:   # bei Wiki-Luecken immer leer, siehe oben
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


ARBEIT_MAX_PRO_LAUF = 2
ARBEIT_MAX_KANDIDATEN = 3
ARBEIT_MODELL = "mistral-small-latest"
ZUGAENGE = "/etc/clayverse/freie-zugaenge.env"


def _schluessel() -> str:
    """Erster lebender Mistral-Schluessel. Wert wird nie geloggt.

    Reihenfolge wie in clayverse/mistral_prestage/secrets.py. Dass Schluessel 1
    ein totes Abo hat, faellt hier nicht auf -- die Antwort ist dann einfach
    ein Fehler und der Vorsatz bleibt offen. Das ist der richtige Ausgang:
    lieber nichts schliessen als falsch schliessen.
    """
    try:
        werte = {}
        with open(ZUGAENGE, encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if not zeile or zeile.startswith("#") or "=" not in zeile:
                    continue
                k, v = zeile.split("=", 1)
                werte[k.strip()] = v.strip().strip('"').strip("'")
        for name in ("MISTRAL2_API_KEY", "MISTRAL3_API_KEY", "MISTRAL_API_KEY"):
            if werte.get(name):
                return werte[name]
        LOG.warning("Zugangsdatei gelesen, aber kein MISTRAL*_API_KEY darin")
    except Exception as fehler:
        # NICHT verschweigen: ein stiller Fehler hier sieht exakt aus wie
        # "es ist kein Schluessel hinterlegt". Genau so verschluckte ein
        # NameError (io nicht importiert) drei vorhandene Schluessel.
        LOG.warning("Zugangsdatei nicht lesbar (%s: %s)", type(fehler).__name__, fehler)
    return ""


def _normal(t: str) -> str:
    """Fuer den Beleg-Abgleich: Kleinschreibung, nur Buchstaben und Ziffern."""
    return "".join(c for c in (t or "").lower() if c.isalnum())


def _fragt_modell(frage: str, quelltext: str, schluessel: str) -> dict:
    """Ein Aufruf, JSON zurueck. Kein Kontext, kein Gedaechtnis."""
    import json as _j
    import urllib.request, urllib.error
    system = (
        "Du bekommst EINEN Quelltext und EINE gesuchte Angabe. Antworte NUR mit JSON: "
        '{"gefunden": true|false, "fakt": "<die Angabe, woertlich aus dem Quelltext>", '
        '"beleg": "<der Satz aus dem Quelltext, in dem sie steht>"}. '
        "Steht die Angabe nicht im Quelltext, ist gefunden=false und fakt/beleg sind leer. "
        "Rate NIE, ergaenze NIE eigenes Wissen -- nur was woertlich dasteht zaehlt."
    )
    koerper = _j.dumps({
        "model": ARBEIT_MODELL,
        "temperature": 0.0,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"GESUCHTE ANGABE: {frage}\n\nQUELLTEXT:\n{quelltext[:6000]}"},
        ],
    }).encode("utf-8")
    anfrage = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions", data=koerper,
        headers={"Authorization": f"Bearer {schluessel}", "Content-Type": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=60) as antwort:
        umschlag = _j.loads(antwort.read(200000))
    return _j.loads(umschlag["choices"][0]["message"]["content"])


def _kandidatentexte(con, kandidaten: dict) -> list:
    """(kennung, art, text) je Kandidat -- Artikel wie Gedaechtnis."""
    raus = []
    for aid in (kandidaten.get("artikel") or [])[:ARBEIT_MAX_KANDIDATEN]:
        try:
            r = con.execute("SELECT titel, text FROM artikel_suchtext WHERE artikel_id=?",
                            (aid,)).fetchone()
        except sqlite3.Error:
            r = None
        if r:
            raus.append((aid, "artikel", f"{r['titel'] or ''}\n{r['text'] or ''}"))
    for g in (kandidaten.get("gedaechtnis") or [])[:ARBEIT_MAX_KANDIDATEN]:
        if isinstance(g, dict) and g.get("wert"):
            raus.append((g.get("id") or "", "protokoll", g["wert"]))
    return raus[:ARBEIT_MAX_KANDIDATEN]


def arbeiten(dry_run: bool = False) -> dict:
    """Offene Selbstpruefungs-Vorsaetze mit Kandidaten wirklich nachlesen."""
    if not VORSATZ_DATEI.exists():
        return {"fehler": "kein Vorsatzzettel -- erst 'pruefen' laufen lassen"}
    zettel = json.loads(VORSATZ_DATEI.read_text(encoding="utf-8"))
    kandidaten_vorsaetze = [v for v in (zettel.get("vorsaetze") or [])
                            if v.get("art") == "Selbstpruefung" and v.get("kandidaten")]
    if not kandidaten_vorsaetze:
        return {"geprueft": 0, "geschlossen": 0, "hinweis": "kein Vorsatz mit Kandidaten"}

    schluessel = _schluessel()
    if not schluessel:
        return {"fehler": "kein Mistral-Schluessel hinterlegt -- nichts getan"}

    con = connect()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
    geschlossen, verworfen, gelesen = [], [], 0
    try:
        for v in kandidaten_vorsaetze[:ARBEIT_MAX_PRO_LAUF]:
            # Die echten Etiketten, nicht die Signatur -- siehe Modul-Historie.
            etiketten = v.get("formulierungen") or []
            frage = "; ".join(etiketten) if etiketten else " ".join(v.get("woerter") or [])
            for kennung, art, text in _kandidatentexte(con, v["kandidaten"]):
                gelesen += 1
                try:
                    antwort = _fragt_modell(frage, text, schluessel)
                except Exception as fehler:
                    LOG.warning("Modellaufruf fehlgeschlagen: %s: %s",
                                type(fehler).__name__, fehler)
                    continue
                if not antwort.get("gefunden"):
                    continue
                fakt = str(antwort.get("fakt") or "").strip()
                beleg = str(antwort.get("beleg") or "").strip()
                # ⭐ DIE SPERRE: was nicht im Quelltext steht, zaehlt nicht.
                if not fakt or _normal(fakt) not in _normal(text):
                    verworfen.append({"folgerung_id": v["folgerung_id"], "kennung": kennung,
                                      "grund": "Angabe steht so nicht im Quelltext",
                                      "behauptet": fakt[:120]})
                    LOG.warning("#%s: Antwort verworfen -- '%s' steht nicht in %s",
                                v["folgerung_id"], fakt[:60], kennung)
                    continue
                vermerk = (f" [{now} vom {PRUEFER} geschlossen: die gesuchte Angabe zu "
                           f"[{frage}] steht in {art} {kennung}: \"{fakt[:160]}\". "
                           f"Beleg: \"{beleg[:200]}\". Zeichenweise gegen den Quelltext "
                           f"geprueft -- eine Angabe, die dort nicht steht, wird verworfen.]")
                if dry_run:
                    LOG.info("[DRY-RUN] #%s wuerde schliessen: %s", v["folgerung_id"], fakt[:80])
                else:
                    con.execute(
                        "UPDATE folgerung SET status='widerlegt', "
                        "begruendung = COALESCE(begruendung,'') || ? "
                        "WHERE id=? AND status='offen'", (vermerk, v["folgerung_id"]))
                    beleg_anhaengen(con, v["folgerung_id"], art, kennung)
                    con.commit()
                    LOG.info("#%s geschlossen: %s (aus %s)", v["folgerung_id"],
                             fakt[:80], kennung)
                geschlossen.append({"folgerung_id": v["folgerung_id"], "fakt": fakt[:160],
                                    "quelle": f"{art}:{kennung}"})
                break   # dieser Vorsatz ist erledigt
        if geschlossen and not dry_run:
            # Den Zettel sofort neu schreiben. Ohne das liest Zero weiter die
            # alte Liste und nennt eine soeben belegte Angabe "ungeprueft"
            # (gemessen 2026-08-20). Der Prueflauf ist billig und rein lesend.
            try:
                con.close()
                pruefen(dry_run=False)
            except Exception as fehler:
                LOG.warning("Zettel nicht erneuert (%s: %s) -- er ist jetzt veraltet",
                            type(fehler).__name__, fehler)
            finally:
                con = connect()
        return {"geprueft": len(kandidaten_vorsaetze[:ARBEIT_MAX_PRO_LAUF]),
                "kandidaten_gelesen": gelesen,
                "geschlossen": len(geschlossen), "details": geschlossen,
                "verworfen": verworfen,
                "hinweis": ("Ein Modell liest EINEN Kandidatentext und sagt, ob die "
                            "gesuchte Angabe darin steht. Was es behauptet, wird gegen "
                            "den Quelltext geprueft -- steht es dort nicht, wird es "
                            "verworfen und der Vorsatz bleibt offen.")}
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
    p.add_argument("befehl", nargs="?", default="pruefen",
                   choices=["pruefen", "stand", "arbeit"])
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if a.befehl == "stand":
        print(json.dumps(cmd_stand(), ensure_ascii=False, indent=2))
        return 0
    if a.befehl == "arbeit":
        print(json.dumps(arbeiten(dry_run=a.dry_run), ensure_ascii=False, indent=2))
        return 0
    ergebnis = pruefen(dry_run=a.dry_run)
    print(json.dumps({k: v for k, v in ergebnis.items() if k != "vorsaetze"},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
