#!/usr/bin/env python3
"""pool_wache.py -- unabhaengiger Free-Pool-Ueberwachungs-/Verwaltungsdienst.

paket-1789144122619-ec428c (Gabriel-Auftrag 2026-09-11, Nacht). Baut auf
~/last-resort/llm.py (TIERS-Kaskade Groq -> NVIDIA Nemotron -> Mistral ->
OpenRouter) und ~/.claude/star/harness_aider.py (bereits bestehender,
kontrollierter Aider-Aufrufweg) auf -- OHNE beide Dateien zu aendern.

⚠️ HARTE GRENZE: dieses Modul importiert/berührt NICHTS unter
~/clay-global-research-entity/ oder ~/rae-arbeitskopie/ (Gabriel-Sperre
2026-08-27, "trigger3: quarantine Frankenstein provider loops", bleibt
gesperrt -- explizit von Gabriel heute Nacht bestaetigt). Diese Datei ist
bewusst NEU und unabhaengig, nicht von den dort gesperrten Orchestrator-
Skripten abgeschaut.

Standing Authorization (Gabriel, 2026-09-11, mehrfach woertlich diese
Nacht): "der GRID soll die Free Tokens frei verwalten und verwenden --
maximal intelligent und vorsichtig, aber er hat ALLE Freigaben." Deshalb
KEIN Freigabe-Abfrageschritt vor Pool-Nutzung in diesem Modul -- die
einzige Schranke ist Sorgfalt (echte Werte, keine erfundene Quote, keine
Verschwendung), nicht ein Bestaetigungs-Dialog.

WAS "VERWALTEN" HIER KONKRET HEISST:
  1. Zustand JEDES Tiers ueber Prozessgrenzen hinweg persistieren (sqlite),
     nicht nur im laufenden Prozess -- ueberlebt Neustarts.
  2. Zwei Wege, Zustand zu erfahren:
       a) record() -- EREIGNIS-basiert, kostenlos: jeder eh schon
          stattfindende Aufruf gegen llm.chat()/chat_stream() meldet sein
          echtes Ergebnis hier. Das ist der eigentlich vorgesehene Weg --
          kein einziger zusaetzlicher API-Call fuer die Ueberwachung selbst.
       b) probe() -- AKTIV, kostet echtes Kontingent (max_tokens=1 Anfrage
          pro getestetem Tier). Nur auf Wunsch/CLI, NIE automatisch im
          Hintergrund -- Ueberwachung darf das ueberwachte Kontingent nicht
          selbst aufbrauchen.
  3. Cooldown-Heuristik aus echten 429/5xx-Ereignissen (kein Raten): erster
     Fehlschlag 60s, danach verdoppelnd bis 900s Deckel, zurueckgesetzt auf
     0 bei jedem folgenden Erfolg. Alles in _tier_zustand persistiert.
  4. all_exhausted()/viable_tiers() als klare Abfragefunktionen -- das ist
     die Schnittstelle, die eskalation_freepool.py (Anforderung B) und die
     GRID-Routing-Weiche (paralleles Paket paket-1789143924381-8e19a8)
     nutzen sollen, statt selbst zu raten.

NIE erfundene Quote/Kapazitaetszahlen -- wo nichts echtes bekannt ist, gibt
dieses Modul None/unbekannt zurueck, nie eine geschaetzte Zahl als sicher.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.expanduser("~/last-resort"))
import llm  # ~/last-resort/llm.py -- TIERS, _tiers(), chat_stream() (ungeaendert)

DB_PATH = os.path.expanduser("~/.claude/star/daten/pool_wache.db")

# Cooldown-Heuristik-Parameter (real begruendet, siehe Modul-Docstring).
_COOLDOWN_START_S = 60.0
_COOLDOWN_CAP_S = 900.0
_COOLDOWN_FAKTOR = 2.0

# Reihenfolge = llm.py-Kaskaden-Prioritaet (dort TIERS-Liste, NICHT hier
# dupliziert erfunden -- direkt aus dem Modul abgeleitet).
def prioritaets_reihenfolge() -> list:
    return [label for label, _url, _model, _keys in llm.TIERS]


_DDL = """
CREATE TABLE IF NOT EXISTS tier_events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    tier TEXT NOT NULL,
    ok INTEGER NOT NULL,
    http_status INTEGER,
    err TEXT,
    latency_ms REAL,
    quelle TEXT
);
CREATE INDEX IF NOT EXISTS idx_tier_events_tier_ts ON tier_events(tier, ts);

CREATE TABLE IF NOT EXISTS tier_zustand(
    tier TEXT PRIMARY KEY,
    konsekutive_fehler INTEGER NOT NULL DEFAULT 0,
    cooldown_bis REAL NOT NULL DEFAULT 0,
    letzter_erfolg REAL,
    letzter_fehler REAL,
    aktualisiert REAL NOT NULL
);
"""


def _verbindung() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=10.0)
    c.execute("PRAGMA busy_timeout=10000")
    c.executescript(_DDL)
    return c


def record(tier: str, ok: bool, http_status: Optional[int] = None,
           err: Optional[str] = None, latency_ms: Optional[float] = None,
           quelle: str = "unbekannt") -> dict:
    """Event-basierte Meldung -- der eigentlich vorgesehene, kostenlose Weg
    (siehe Docstring Punkt 2a). Jeder Aufrufer von llm.chat()/chat_stream()
    kann (sollte) sein echtes Ergebnis hier melden. `quelle` = freier Text,
    wer gemeldet hat (z.B. 'harness_aider:nvidia-nemotron', 'grid-routing').
    Aktualisiert die persistente Cooldown-Heuristik. Gibt den neuen
    tier_state(tier) zurueck."""
    now = time.time()
    c = _verbindung()
    try:
        c.execute(
            "INSERT INTO tier_events(ts, tier, ok, http_status, err, latency_ms, quelle) "
            "VALUES (?,?,?,?,?,?,?)",
            (now, tier, 1 if ok else 0, http_status, (err or "")[:500], latency_ms, quelle),
        )
        row = c.execute("SELECT konsekutive_fehler, cooldown_bis FROM tier_zustand WHERE tier=?",
                         (tier,)).fetchone()
        konsek, cooldown_bis = (row if row else (0, 0.0))
        if ok:
            konsek = 0
            cooldown_bis = 0.0
            letzter_erfolg, letzter_fehler = now, None
        else:
            letzter_erfolg = None
            letzter_fehler = now
            konsek += 1
            dauer = min(_COOLDOWN_CAP_S, _COOLDOWN_START_S * (_COOLDOWN_FAKTOR ** (konsek - 1)))
            cooldown_bis = now + dauer
        c.execute(
            "INSERT INTO tier_zustand(tier, konsekutive_fehler, cooldown_bis, letzter_erfolg, "
            "letzter_fehler, aktualisiert) VALUES (?,?,?,?,?,?) "
            "ON CONFLICT(tier) DO UPDATE SET konsekutive_fehler=excluded.konsekutive_fehler, "
            "cooldown_bis=excluded.cooldown_bis, "
            "letzter_erfolg=COALESCE(excluded.letzter_erfolg, tier_zustand.letzter_erfolg), "
            "letzter_fehler=COALESCE(excluded.letzter_fehler, tier_zustand.letzter_fehler), "
            "aktualisiert=excluded.aktualisiert",
            (tier, konsek, cooldown_bis, letzter_erfolg, letzter_fehler, now),
        )
        c.commit()
    finally:
        c.close()
    return tier_state(tier)


def tier_state(tier: str) -> dict:
    c = _verbindung()
    try:
        row = c.execute(
            "SELECT konsekutive_fehler, cooldown_bis, letzter_erfolg, letzter_fehler, aktualisiert "
            "FROM tier_zustand WHERE tier=?", (tier,)).fetchone()
    finally:
        c.close()
    now = time.time()
    if not row:
        return {"tier": tier, "bekannt": False, "in_cooldown": False, "cooldown_bis": None,
                "konsekutive_fehler": 0, "letzter_erfolg": None, "letzter_fehler": None}
    konsek, cooldown_bis, letzter_erfolg, letzter_fehler, _akt = row
    return {
        "tier": tier, "bekannt": True,
        "in_cooldown": bool(cooldown_bis and cooldown_bis > now),
        "cooldown_bis": cooldown_bis or None,
        "cooldown_rest_s": max(0.0, (cooldown_bis or 0) - now),
        "konsekutive_fehler": konsek,
        "letzter_erfolg": letzter_erfolg,
        "letzter_fehler": letzter_fehler,
    }


def status() -> dict:
    """Voller Ueberblick, in llm.py-Kaskaden-Reihenfolge. Fuer CLI/Dashboard
    UND fuer andere Module (eskalation_freepool.py, GRID-Routing)."""
    return {t: tier_state(t) for t in prioritaets_reihenfolge()}


def viable_tiers() -> list:
    """Tiers, die JETZT nicht in Cooldown sind, in Kaskaden-Prioritaet.
    Beruecksichtigt NUR Tiers, fuer die ueberhaupt ein Schluessel geladen
    ist (llm._tiers()) -- ein Tier ohne Schluessel ist nie 'viable', auch
    wenn nie ein Fehler gemeldet wurde."""
    geladene = {label for label, _u, _m, _k in llm._tiers()}
    out = []
    for t in prioritaets_reihenfolge():
        if t not in geladene:
            continue
        st = tier_state(t)
        if not st["in_cooldown"]:
            out.append(t)
    return out


def all_exhausted() -> bool:
    """True nur wenn ALLE Tiers, fuer die ueberhaupt ein Schluessel existiert,
    aktuell in Cooldown sind. Kein Schluessel geladen -> das zaehlt als
    'nicht verfuegbar', nicht als 'unbekannt/optimistisch verfuegbar'."""
    geladene = {label for label, _u, _m, _k in llm._tiers()}
    if not geladene:
        return True
    return len(viable_tiers()) == 0


def probe(tier: Optional[str] = None) -> dict:
    """AKTIVER Test -- kostet echtes Kontingent (max_tokens=1). Nur auf
    Wunsch (CLI/manueller Aufruf), NIE als Hintergrund-Poller. Testet
    entweder ein einzelnes Tier oder (tier=None) alle geladenen Tiers.
    Nutzt echte HTTP-Calls gegen die jeweilige API -- exakt dieselben
    Endpunkte/Modelle wie llm.py (llm.TIERS), aber non-streaming und mit
    Timing, damit jedes Tier EINZELN (nicht nur der Kaskaden-Gewinner)
    bewertet werden kann -- llm.chat_stream() selbst gibt bei Erfolg nur den
    ERSTEN erfolgreichen Tier zurueck, nicht den Zustand der uebrigen."""
    import requests
    keys_by_tier = {label: api_keys for label, _u, _m, api_keys in llm._tiers()}
    ziel_tiers = [tier] if tier else list(keys_by_tier.keys())
    ergebnisse = {}
    tiers_by_label = {label: (url, model) for label, url, model, _k in llm.TIERS}
    for t in ziel_tiers:
        if t not in keys_by_tier:
            ergebnisse[t] = {"ok": False, "grund": "kein Schluessel geladen"}
            continue
        url, model = tiers_by_label[t]
        key = keys_by_tier[t][0]
        t0 = time.time()
        try:
            r = requests.post(
                url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": "ping"}],
                      "max_tokens": 1, "temperature": 0},
                timeout=30,
            )
            latenz_ms = (time.time() - t0) * 1000.0
            ok = r.status_code == 200
            ergebnisse[t] = {"ok": ok, "http_status": r.status_code, "latenz_ms": round(latenz_ms, 1)}
            record(t, ok, http_status=r.status_code,
                   err=(None if ok else r.text[:300]), latency_ms=latenz_ms, quelle="probe")
        except requests.RequestException as e:
            latenz_ms = (time.time() - t0) * 1000.0
            ergebnisse[t] = {"ok": False, "grund": str(e), "latenz_ms": round(latenz_ms, 1)}
            record(t, False, err=str(e)[:300], latency_ms=latenz_ms, quelle="probe")
    return ergebnisse


def _cli():
    p = argparse.ArgumentParser(description="Free-Pool-Ueberwachung (pool_wache.py)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Zustand aller Tiers (aus persistenten Ereignissen)")

    p_probe = sub.add_parser("probe", help="AKTIVER Test (kostet echtes Kontingent!)")
    p_probe.add_argument("--tier", default=None, help="nur dieses Tier (sonst: alle geladenen)")

    p_rec = sub.add_parser("record", help="Ereignis melden (fuer andere Aufrufer/Skripte)")
    p_rec.add_argument("--tier", required=True)
    p_rec.add_argument("--ok", action="store_true")
    p_rec.add_argument("--fail", action="store_true")
    p_rec.add_argument("--http-status", type=int, default=None)
    p_rec.add_argument("--err", default=None)
    p_rec.add_argument("--quelle", default="cli")

    args = p.parse_args()
    if args.cmd == "status":
        st = status()
        st["_all_exhausted"] = all_exhausted()
        st["_viable_tiers"] = viable_tiers()
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "probe":
        print(json.dumps(probe(args.tier), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "record":
        if args.ok == args.fail:
            p.error("genau eines von --ok/--fail angeben")
        r = record(args.tier, args.ok, http_status=args.http_status, err=args.err, quelle=args.quelle)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(_cli())
