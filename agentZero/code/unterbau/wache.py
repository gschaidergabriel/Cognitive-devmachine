#!/usr/bin/env python3
"""wache.py — Live-Wachhund fuer alle Agenten auf dieser VPS (F5-Auftrag, 2026-08-15).

Owner-Auftrag: "Always know LIVE what all agents on the VPS are doing." Anlass:
zwei Hintergrund-Worker starben an Server-Fehlern, gemerkt hat es nur ein Mensch,
der zufaellig eine Meldung las. Nichts scheiterte laut.

ZWEI FEHLERARTEN, die zweite ist die gefaehrliche:
  TOD             der Worker stirbt. Es gibt wenigstens irgendwo einen Fehler.
  STILLES STEHEN  der Worker LEBT, meldet nichts, sieht beschaeftigt aus. Kein
                  Fehler. Das ist der Fall, den ein Mensch sonst nie findet.

Vorbild (gelesen vor dem Bau, wie verlangt): ~/swarm/ablauf/wache auf diesem
Rechner (tavern-wache.service, "tAvern Lebens-Wachhund (F5): Tode + stilles
Stehen"). Uebernommen: die Zweiteilung tot/still, append-only TSV-artiges Log
(hier: SQLite wa_ereignis), Dedup fuer stille Befunde (dort 30 min, hier siehe
SCHWELLE_MIN unten), "Wache stupst nicht selbst" -> Wache SCHREIBT NICHT in
fremde Systeme, sie berichtet nur. Verworfen: das dortige Bindungsverfahren
(Sessions-Register ~/.claude/sessions/<pid>.json) - existiert auf dieser VPS
nicht; hier gibt es stattdessen sitzungen.json (kern.py) + die taetigkeit-
Tabelle als Bindung.

ZWEI KLASSEN VON AGENTEN AUF DIESER VPS, beide abgedeckt:
  (A) systemd-Einheiten: clayverse-kern.service (Dauerlaeufer), clayverse-*
      (Timer-getriebene Oneshots: github/karte/wirte/eichung), frank-laeufer*
      (GitHub-Actions-ersatzlaeufer), actions.runner.*.service (persistente
      GitHub-Actions-Runner). Dynamisch entdeckt (glob), nicht hart codiert -
      neue Runner werden automatisch mitueberwacht.
  (B) Claude-Code-Sitzungen, die kern.py auf DIESER VPS startet: sitzungen.json
      (Zustand wartet/arbeitet) + taetigkeit-Tabelle gefiltert auf wirt==
      Hostname dieser Maschine (nur was hier lief/laeuft, nicht die anderen
      108 wirt-Werte anderer Rechner - die Tabelle ist zentral, aber diese
      Wache beobachtet nur ihre eigene VPS).

LIVENESS WIRD GEMESSEN, NICHT ANGENOMMEN:
  - Fuer systemd-Dienste: /proc/<pid>/io (rchar/wchar) + /proc/<pid>/stat
    (utime+stime) im Delta. `lage` nimmt zwei Live-Proben (~0.6s auseinander).
    `wacht` (Timer, alle 5 min) nimmt keine Sleep-Probe, sondern vergleicht
    gegen die in wa_snapshot gespeicherte Probe des LETZTEN Laufs - das ist
    derselbe Trick wie /proc/<pid>/io lesen statt einer leeren Ausgabedatei
    zu vertrauen, nur ueber die Zeitachse der Timer-Intervalle gespannt.
  - Fuer Timer-Einheiten zusaetzlich ein zweites, unabhaengiges Signal: wenn
    systemd selbst NextElapseUSecRealtime < jetzt meldet fuer einen Timer im
    Zustand "waiting", hat sein eigener Scheduler nicht gefeuert. Kein
    geratenes Intervall noetig - systemd sagt es direkt.
  - Fuer Claude-Sitzungen: sitzungen.json-Zustand "arbeitet" + juengste Zeile
    in taetigkeit fuer diese sitzung/instanz.

SCHWELLE, GEMESSEN NICHT GERATEN: siehe SCHWELLE_MIN unten - Herleitung aus
der echten Gap-Verteilung von taetigkeit (26.338 Luecken zwischen aufeinander-
folgenden Werkzeugaufrufen derselben wirt+instanz).

EIGENE TABELLEN NUR: wa_ereignis, wa_snapshot, wa_grenze - alles in wiki.db,
demselben Praefix-Muster wie vp_/kb_. Read-only auf allem anderen. WAL +
busy_timeout + Retry, weil mehrere Agenten gleichzeitig in wiki.db schreiben.

Harte Regeln beachtet: keine Modell-Aufrufe, keine Loesch-Shell-Kommandos,
vorprozessor.py/wiki.py/kern.py/tor_hook.py nicht angefasst, kein bau.py,
kein git commit/push.
"""
from __future__ import annotations

import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

WIKI_DB = os.environ.get("WACHE_DB", "/var/lib/clay/wiki.db")
SITZUNGEN = Path(os.environ.get("WACHE_SITZUNGEN", "/var/lib/clay/sitzungen.json"))
HOSTNAME = socket.gethostname()

# Gemessen aus taetigkeit (26.338 Luecken, sortiert), 2026-08-15:
#   p50=9.8s  p75=20.6s  p90=40.8s  p95=73.9s  p99=402.3s(6.7min)
#   p99.5=1097.7s(18.3min)  p99.9=17776.8s(296min)  max=315601.6s
# >=20min trifft nur 120/26338=0.456% aller je gemessenen Luecken (>=30min:
# 0.376%). Schwelle liegt also knapp UEBER dem 99.5-Perzentil realer,
# legitimer Pausen (lange find/ssh-Kommandos eingeschlossen) - genug Abstand,
# dass sie kein Rauschen erzeugt, aber nah genug, um echtes Stillstehen in
# vertretbarer Zeit zu fangen. Gleicher Wert wie ~/swarm/ablauf/wache
# (dort auch 20min Default) - hier zusaetzlich an echten Daten geprueft,
# nicht nur uebernommen.
SCHWELLE_MIN = 20
SCHWELLE_S = SCHWELLE_MIN * 60

# Dedup fuer 'stille'-Befunde: dieselbe Einheit hoechstens alle 30 min neu
# melden (identisch zu ~/swarm/ablauf/wache Zeile 112).
STILLE_DEDUP_S = 1800

AGENT_UNIT_GLOBS = ["clayverse-*.service", "actions.runner.*.service", "frank-laeufer*.service"]


# --------------------------------------------------------------------- Basis

def _jetzt_iso():
    return datetime.now(timezone.utc).isoformat()


def _db():
    """WAL + busy_timeout + Retry - mehrere Agenten schreiben gleichzeitig
    in wiki.db (vp_*, kb_*, taetigkeit kommen von anderen Prozessen)."""
    for versuch in range(5):
        try:
            c = sqlite3.connect(WIKI_DB, timeout=10)
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA busy_timeout=5000")
            return c
        except sqlite3.OperationalError:
            if versuch == 4:
                raise
            time.sleep(0.3 * (versuch + 1))


def _init_tabellen(c):
    c.execute("""CREATE TABLE IF NOT EXISTS wa_ereignis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit TEXT, art TEXT, ziel TEXT, detail TEXT, quelle TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS wa_snapshot (
        ziel TEXT PRIMARY KEY,
        zeit TEXT, rchar INTEGER, wchar INTEGER, cpu_ticks INTEGER,
        active_enter TEXT, active_state TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS wa_grenze (
        id INTEGER PRIMARY KEY AUTOINCREMENT, zeit TEXT, detail TEXT
    )""")
    c.commit()


def _retry(fn, *a, **kw):
    for versuch in range(5):
        try:
            return fn(*a, **kw)
        except sqlite3.OperationalError as e:
            if "locked" not in str(e) and "busy" not in str(e):
                raise
            if versuch == 4:
                raise
            time.sleep(0.3 * (versuch + 1))


def _schon_gemeldet(c, art, ziel, dedup_s):
    row = c.execute(
        "SELECT zeit FROM wa_ereignis WHERE art=? AND ziel=? ORDER BY id DESC LIMIT 1",
        (art, ziel),
    ).fetchone()
    if not row:
        return False
    try:
        letzte = datetime.fromisoformat(row[0])
    except Exception:
        return False
    return (datetime.now(timezone.utc) - letzte).total_seconds() < dedup_s


def _protokoll(c, art, ziel, detail):
    c.execute(
        "INSERT INTO wa_ereignis (zeit, art, ziel, detail, quelle) VALUES (?,?,?,?,?)",
        (_jetzt_iso(), art, ziel, detail, HOSTNAME),
    )
    c.commit()


# --------------------------------------------------------------- systemd IO

def _sh(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except Exception:
        return ""


def _systemctl_show(unit, props):
    out = _sh(["systemctl", "show", unit, "-p", ",".join(props)])
    d = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k] = v
    return d


def _agent_units():
    units = []
    for glob in AGENT_UNIT_GLOBS:
        out = _sh(["systemctl", "list-units", "--all", "--plain", "--no-legend", glob])
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            name = line.split()[0]
            if name.endswith(".service"):
                units.append(name)
    return sorted(set(units))


def _agent_timers():
    out = _sh(["systemctl", "list-units", "--all", "--plain", "--no-legend", "clayverse-*.timer"])
    return sorted({line.split()[0] for line in out.splitlines() if line.strip()})


def _proc_io(pid):
    try:
        io = {}
        for line in Path(f"/proc/{pid}/io").read_text().splitlines():
            k, v = line.split(":")
            io[k.strip()] = int(v.strip())
        return io.get("rchar", 0), io.get("wchar", 0)
    except Exception:
        return None, None


def _proc_cpu_ticks(pid):
    try:
        parts = Path(f"/proc/{pid}/stat").read_text().split()
        return int(parts[13]) + int(parts[14])  # utime + stime
    except Exception:
        return None


def _journal_letzte_zeile(unit, seit="today"):
    out = _sh(["journalctl", "-u", unit, "--since", seit, "-n", "3", "--no-pager", "-o", "short-iso"])
    zeilen = [l for l in out.splitlines() if l.strip()]
    return zeilen[-1] if zeilen else ""


def _journal_alter_s(unit):
    """Alter (Sekunden) der letzten journald-Zeile dieser Einheit, oder None
    wenn keine Zeile in den letzten 2 Tagen existiert. journald schreibt den
    eigenen ISO-Zeitstempel als erstes Feld jeder -o short-iso Zeile - das
    ist unabhaengig vom Text, den der Dienst selbst loggt."""
    out = _sh(["journalctl", "-u", unit, "--since", "-2days", "-n", "1", "--no-pager", "-o", "short-iso"])
    zeilen = [l for l in out.splitlines() if l.strip()]
    if not zeilen:
        return None
    tok = zeilen[-1].split(" ", 1)[0]
    try:
        t = datetime.fromisoformat(tok)
        return (datetime.now(timezone.utc) - t).total_seconds()
    except Exception:
        return None


# ----------------------------------------------------------- Klassifizierung

class Befund:
    def __init__(self, ziel, art_gruppe, seit, letzte_aktivitaet, alter_s, status, detail):
        self.ziel = ziel
        self.art_gruppe = art_gruppe  # "dienst" | "sitzung"
        self.seit = seit
        self.letzte_aktivitaet = letzte_aktivitaet
        self.alter_s = alter_s
        self.status = status  # "tot" | "still" | "arbeitet" | "ruht"
        self.detail = detail


def _dienst_befund(unit, live_probe=True):
    d = _systemctl_show(unit, ["ActiveState", "SubState", "Result", "MainPID",
                                "ActiveEnterTimestamp", "ExecMainStartTimestamp",
                                "ExecMainExitTimestamp", "InvocationID"])
    active = d.get("ActiveState", "")
    sub = d.get("SubState", "")
    result = d.get("Result", "")
    pid = d.get("MainPID", "0")
    seit = d.get("ActiveEnterTimestamp", "") or d.get("ExecMainStartTimestamp", "") or "?"

    if active == "failed" or (result not in ("success", "") and active != "active"):
        letzte = _journal_letzte_zeile(unit)
        return Befund(unit, "dienst", seit, "-", None, "tot",
                       f"ActiveState={active} Result={result} — {letzte[-160:]}")

    if active != "active" or pid in ("0", ""):
        # normal ruhend zwischen Timer-Laeufen (oneshot), solange Result=success.
        # Ob der TIMER selbst ueberfaellig ist, prueft _timer_befund separat.
        return Befund(unit, "dienst", d.get("ExecMainStartTimestamp", "?") or "?",
                       d.get("ExecMainExitTimestamp", "?") or "?", None,
                       "ruht", f"ActiveState={active} SubState={sub} Result={result or 'success'}")

    pid = int(pid)
    if not live_probe:
        return Befund(unit, "dienst", seit, "?", None, "arbeitet?", "kein Live-Check angefragt")

    r0, w0 = _proc_io(pid)
    cpu0 = _proc_cpu_ticks(pid)
    time.sleep(0.6)
    r1, w1 = _proc_io(pid)
    cpu1 = _proc_cpu_ticks(pid)
    if r0 is None:
        # pid verschwand waehrend der Probe -> zwischen den zwei Signalen gestorben
        letzte = _journal_letzte_zeile(unit)
        return Befund(unit, "dienst", seit, "-", None, "tot",
                       f"pid {pid} verschwand waehrend der Probe — {letzte[-160:]}")
    io_delta = (r1 - r0) + (w1 - w0)
    cpu_delta = (cpu1 - cpu0) if (cpu0 is not None and cpu1 is not None) else 0
    if io_delta > 0 or cpu_delta > 0:
        return Befund(unit, "dienst", seit, "jetzt", 0, "arbeitet",
                       f"pid {pid}: io_delta={io_delta}B cpu_delta={cpu_delta} Takte / 0.6s")
    # Keine Bewegung in der 0.6s-Probe ALLEIN beweist nichts - ein
    # ereignisgetriebener Daemon (Runner zwischen Jobs, kern.service ohne
    # Anfrage) ist die meiste Zeit legitim ohne IO. Zweites, unabhaengiges
    # Signal noetig: Alter der letzten journald-Zeile. Nur wenn BEIDE
    # schweigen (keine IO-Bewegung UND kein Log seit der Schwelle), ist es
    # ein echter Befund - sonst ist es normales Idle.
    alter = _journal_alter_s(unit)
    letzte = _journal_letzte_zeile(unit)
    if alter is not None and alter < SCHWELLE_S:
        return Befund(unit, "dienst", seit, f"vor {alter:.0f}s (Log)", alter, "ruht",
                       f"pid {pid}: 0.6s ohne IO/CPU, aber Log vor {alter:.0f}s — normales Idle, kein Befund")
    return Befund(unit, "dienst", seit, letzte.split(" ", 1)[0] if letzte else "?", alter, "still",
                   f"pid {pid}: 0.6s ohne IO/CPU UND "
                   + (f"letztes Log vor {alter/60:.0f} min" if alter is not None else "kein Log in 2 Tagen")
                   + f" (Schwelle {SCHWELLE_MIN} min) — {letzte[-100:]}")


def _timer_befund(timer):
    d = _systemctl_show(timer, ["ActiveState", "NextElapseUSecRealtime", "LastTriggerUSec"])
    active = d.get("ActiveState", "")
    next_us = d.get("NextElapseUSecRealtime", "")
    if active != "waiting" or not next_us or next_us in ("0", "n/a"):
        return None
    try:
        next_epoch = int(next_us) / 1_000_000
    except ValueError:
        return None
    verzug = time.time() - next_epoch
    if verzug > 60:  # systemd selbst haette laengst neu geplant
        return Befund(timer, "dienst", "-", d.get("LastTriggerUSec", "?"), verzug, "still",
                       f"eigener naechster Feuerzeitpunkt liegt {verzug:.0f}s in der Vergangenheit "
                       f"— systemds Scheduler fuer diesen Timer haengt")
    return None


def _sitzungen_befunde(c):
    befunde = []
    if not SITZUNGEN.exists():
        return befunde
    try:
        st = json.loads(SITZUNGEN.read_text())
    except Exception:
        return befunde
    jetzt = datetime.now(timezone.utc)
    for sid, w in st.items():
        zustand = w.get("zustand", "?")
        zuletzt_s = w.get("zuletzt", "")
        try:
            zuletzt = datetime.fromisoformat(zuletzt_s.replace("Z", "+00:00"))
        except Exception:
            zuletzt = None
        # juengste taetigkeit-Zeile fuer diese Sitzung auf DIESER VPS
        row = c.execute(
            "SELECT MAX(zeit) FROM taetigkeit WHERE sitzung=? AND wirt=?",
            (w.get("claude_sitzung", sid), HOSTNAME),
        ).fetchone()
        letzte_taet = row[0] if row and row[0] else None
        letzte_taet_dt = None
        if letzte_taet:
            try:
                letzte_taet_dt = datetime.fromisoformat(letzte_taet.replace("Z", "+00:00"))
            except Exception:
                pass
        bezug = letzte_taet_dt or zuletzt
        alter_s = (jetzt - bezug).total_seconds() if bezug else None
        if zustand == "arbeitet":
            if alter_s is not None and alter_s >= SCHWELLE_S:
                befunde.append(Befund(sid, "sitzung", w.get("angelegt", "?"),
                                       bezug.isoformat() if bezug else "-", alter_s, "still",
                                       f"kern.py meldet zustand=arbeitet, aber {alter_s/60:.0f} min "
                                       f"ohne taetigkeit/Update — Titel: {w.get('titel', '?')}"))
            else:
                befunde.append(Befund(sid, "sitzung", w.get("angelegt", "?"),
                                       bezug.isoformat() if bezug else "-", alter_s or 0, "arbeitet",
                                       f"Titel: {w.get('titel', '?')}"))
        else:
            befunde.append(Befund(sid, "sitzung", w.get("angelegt", "?"),
                                   bezug.isoformat() if bezug else "-", alter_s or 0, "ruht",
                                   f"zustand={zustand} Titel: {w.get('titel', '?')}"))
    return befunde


# --------------------------------------------------------------- Subcommands

def cmd_lage(_args):
    c = _db()
    _init_tabellen(c)
    print(f"wache lage — {_jetzt_iso()} auf {HOSTNAME}, Schwelle {SCHWELLE_MIN} min\n")
    n_arbeitet = n_still = n_tot = n_ruht = 0
    for unit in _agent_units():
        b = _dienst_befund(unit, live_probe=True)
        tag = {"tot": "✘ TOT", "still": "⚠ still", "arbeitet": "✓ arbeitet",
               "ruht": "· ruht"}.get(b.status, b.status)
        print(f"[{tag:12}] {b.ziel:45} seit {b.seit}")
        print(f"             {b.detail}")
        if b.status == "tot":
            n_tot += 1
        elif b.status == "still":
            n_still += 1
        elif b.status == "arbeitet":
            n_arbeitet += 1
        else:
            n_ruht += 1
    for timer in _agent_timers():
        tb = _timer_befund(timer)
        if tb:
            print(f"[⚠ still     ] {tb.ziel:45}")
            print(f"             {tb.detail}")
            n_still += 1
    for b in _sitzungen_befunde(c):
        tag = {"still": "⚠ still", "arbeitet": "✓ arbeitet", "ruht": "· ruht"}.get(b.status, b.status)
        print(f"[{tag:12}] sitzung {b.ziel:37} seit {b.seit}")
        print(f"             {b.detail}")
        if b.status == "still":
            n_still += 1
        elif b.status == "arbeitet":
            n_arbeitet += 1
        else:
            n_ruht += 1
    print(f"\nlage: {n_arbeitet} arbeiten, {n_still} still/verdaechtig, {n_tot} tot, {n_ruht} ruhen — "
          + time.strftime("%H:%M:%S"))
    c.close()


def _tote_scan(c, melde):
    treffer = []
    for unit in _agent_units():
        b = _dienst_befund(unit, live_probe=False)
        if b.status == "tot":
            fingerprint = f"{unit}@{b.seit}"  # neuer Fingerprint pro neuem Fehl-Start -> Neustart meldet erneut
            if melde and not _schon_gemeldet(c, "tot", fingerprint, 10**9):  # Tode dedupen nur pro Fingerprint, nicht zeitbasiert
                _retry(_protokoll, c, "tot", fingerprint, b.detail)
            treffer.append(b)
    return treffer


def cmd_tote(args):
    c = _db()
    _init_tabellen(c)
    if getattr(args, "jetzt", False):
        treffer = _tote_scan(c, melde=getattr(args, "melde", False))
        for b in treffer:
            print(f"✘ {b.ziel} (seit {b.seit}): {b.detail}")
        print(f"tote (Live-Scan): {len(treffer)} Befund(e)")
    else:
        tage = getattr(args, "tage", 7)
        cutoff = time.time() - tage * 86400
        rows = c.execute(
            "SELECT zeit, ziel, detail FROM wa_ereignis WHERE art='tot' ORDER BY id DESC LIMIT 200"
        ).fetchall()
        n = 0
        for zeit, ziel, detail in rows:
            try:
                t = datetime.fromisoformat(zeit).timestamp()
            except Exception:
                t = 0
            if t < cutoff:
                continue
            print(f"{zeit}  ✘ {ziel}: {detail}")
            n += 1
        print(f"tote (letzte {tage} Tage aus wa_ereignis): {n} Eintrag/Eintraege")
    c.close()


def _stille_scan(c, melde):
    """NUR die zwei Domaenen mit einer echten, gemessenen "sollte hier
    Fortschritt sehen"-Grundlinie: Timer (systemds eigener Scheduler sagt
    JA/NEIN, keine erfundene Schwelle noetig) und kern.py-Sitzungen (Schwelle
    aus der echten taetigkeit-Gap-Verteilung hergeleitet, siehe SCHWELLE_MIN).

    BEWUSST NICHT hier: der IO/CPU+Log-Stille-Check aus _dienst_befund fuer
    dauerhafte, ereignisgetriebene Daemons (GitHub-Actions-Runner zwischen
    Jobs, kern.service ohne HTTP-Anfrage). Beim Testen dieses Skripts hat
    genau das einen Fehlalarm produziert: alle 5 Runner + kern.service
    schlugen als "still" an, obwohl sie schlicht auf Arbeit warten - legitim
    stundenlang leise. Fuer diese Klasse gibt es (noch) keine gemessene
    "Idle ist normal bis X, danach nicht mehr"-Schwelle; sie erfinden waere
    genau der Fehler, vor dem die Aufgabe warnt ("Do not pick X out of the
    air"). Der Live-Probe bleibt in `lage` als Information sichtbar, wird
    aber NICHT nach wa_ereignis geschrieben - ein Wachhund, der hier Alarm
    schlaegt, wird ignoriert (Fehlalarm-Rate zu hoch), und genau das war
    der Kern des Owner-Auftrags."""
    treffer = []
    for timer in _agent_timers():
        tb = _timer_befund(timer)
        if tb:
            treffer.append(tb)
    for b in _sitzungen_befunde(c):
        if b.status == "still":
            treffer.append(b)
    if melde:
        for b in treffer:
            if not _schon_gemeldet(c, "still", b.ziel, STILLE_DEDUP_S):
                _retry(_protokoll, c, "still", b.ziel, b.detail)
    return treffer


def cmd_stille(args):
    c = _db()
    _init_tabellen(c)
    treffer = _stille_scan(c, melde=getattr(args, "melde", False))
    for b in treffer:
        print(f"⚠ {b.ziel}: {b.detail}")
    print(f"stille: {len(treffer)} Befund(e), Schwelle {SCHWELLE_MIN} min, " + time.strftime("%H:%M:%S"))
    c.close()


def cmd_wacht(_args):
    """Ein Pruefzyklus fuer den Timer: tote-Scan + stille-Scan, IMMER gemeldet
    (schreibt nach wa_ereignis), plus wa_snapshot-Fortschreibung fuer die
    naechste Delta-Messung."""
    c = _db()
    _init_tabellen(c)
    tote = _tote_scan(c, melde=True)
    stille = _stille_scan(c, melde=True)

    # wa_snapshot fortschreiben: IO/CPU-Zaehler pro aktiver Einheit fuer die
    # naechste Delta-Messung (Trick aus der Aufgabe: /proc/<pid>/io lesen,
    # nicht eine leere Ausgabe glauben - hier ueber die Zeitachse der
    # Timer-Intervalle statt einer Sleep-Probe).
    for unit in _agent_units():
        d = _systemctl_show(unit, ["ActiveState", "MainPID", "ActiveEnterTimestamp"])
        pid = d.get("MainPID", "0")
        if d.get("ActiveState") == "active" and pid not in ("0", ""):
            r, w = _proc_io(int(pid))
            cpu = _proc_cpu_ticks(int(pid))
            if r is not None:
                _retry(c.execute,
                       "INSERT INTO wa_snapshot (ziel, zeit, rchar, wchar, cpu_ticks, active_enter, active_state) "
                       "VALUES (?,?,?,?,?,?,?) "
                       "ON CONFLICT(ziel) DO UPDATE SET zeit=excluded.zeit, rchar=excluded.rchar, "
                       "wchar=excluded.wchar, cpu_ticks=excluded.cpu_ticks, "
                       "active_enter=excluded.active_enter, active_state=excluded.active_state",
                       (unit, _jetzt_iso(), r, w, cpu or 0, d.get("ActiveEnterTimestamp", ""), "active"))
    c.commit()
    print(f"wacht: {len(tote)} tot, {len(stille)} still gemeldet — " + time.strftime("%H:%M:%S"))
    c.close()


def cmd_grenze(_args):
    """Setzt einen Cutover-Marker: ab hier zaehlt der PostToolUse-Hook-Strom
    live weiter, der retroaktive Walk (taetigkeit.py scan) war einmalig.
    Verhindert Doppelzaehlung: der Hook hat keine stabile tool_use_id (siehe
    taetigkeit_hook.py Docstring), also KEIN erneuter rueckwirkender Walk
    ueber den Zeitraum nach diesem Marker."""
    c = _db()
    _init_tabellen(c)
    detail = ("Cutover: ab hier live ueber PostToolUse-Hook (taetigkeit_hook.py). "
              "Retroaktiver Walk (taetigkeit.py scan) war einmaliger Backfill bis hierher — "
              "danach NICHT erneut rueckwirkend walken (roh_hash-Kollisionsgefahr mit dem "
              "Hook-Strom ist nicht ausgeschlossen, siehe taetigkeit_hook.py Docstring).")
    c.execute("INSERT INTO wa_grenze (zeit, detail) VALUES (?,?)", (_jetzt_iso(), detail))
    c.commit()
    print(f"grenze gesetzt: {_jetzt_iso()}")
    c.close()


def main():
    import argparse
    p = argparse.ArgumentParser(description="wache — Live-Wachhund fuer Agenten auf dieser VPS")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("lage", help="wer laeuft JETZT, tut was, seit wann")

    pt = sub.add_parser("tote", help="was starb und wann")
    pt.add_argument("--jetzt", action="store_true", help="Live-Scan statt Historie aus wa_ereignis")
    pt.add_argument("--melde", action="store_true", help="mit --jetzt: gefundene Tode auch protokollieren")
    pt.add_argument("--tage", type=int, default=7)

    ps_ = sub.add_parser("stille", help="lebt, aber still ueber der Schwelle")
    ps_.add_argument("--melde", action="store_true", help="gefundene Befunde nach wa_ereignis schreiben")

    sub.add_parser("wacht", help="ein Pruefzyklus fuer den Timer (tote+stille, immer gemeldet)")
    sub.add_parser("grenze", help="Cutover-Marker setzen: Hook-Strom loest retroaktiven Walk ab")

    args = p.parse_args()
    {"lage": cmd_lage, "tote": cmd_tote, "stille": cmd_stille,
     "wacht": cmd_wacht, "grenze": cmd_grenze}[args.cmd](args)


if __name__ == "__main__":
    main()
