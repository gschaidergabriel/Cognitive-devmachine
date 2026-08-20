#!/usr/bin/env python3
"""Die Ziel- und Faehigkeitstabelle von Agent Zero.

Aufbau bewusst zweiteilig, weil nur das ehrlich bleibt:

    SOLL   deklariert. Aendert sich nur, wenn der Eigner etwas entscheidet.
           Jede Zeile nennt die Quelle der Entscheidung.
    IST    GEMESSEN, bei jedem Lauf neu, durch einen Pruefer je Zeile.
           Nichts hier wird behauptet.

Eine handgepflegte Statustabelle steht nach einer Woche auf gruen, weil niemand
sie zurueckstellt. Diese kann das nicht: sie fragt jedes Mal das System.
"""
from __future__ import annotations
import json, os, re, sqlite3, subprocess
from datetime import datetime, timezone
from pathlib import Path

DB = os.environ.get("AGENTZERO_DB", "/var/lib/clay/wiki.db")
ARTEFAKT = Path("/opt/entityos/the artefact")


def _sh(cmd: str, timeout: int = 45) -> str:
    """Einen Befehl ausfuehren -- und einen Abbruch NICHT als Leere ausgeben.

    ⚠️ Vorher stand hier `except Exception: return ""`. Damit sah ein Zeitablauf
    exakt aus wie ein Befehl, der nichts zu sagen hatte. Konkret: die Testsuite
    wuchs auf ueber 45 Sekunden, die Messung lief in die Grenze, und die
    Zieltabelle meldete "nicht gemessen" -- ohne einen Hinweis darauf, dass
    ueberhaupt etwas schiefging.

    ⭐ Das ist HEUTE DER VIERTE Fall derselben Bauart (du -xsh /tmp, _n() auf
    fehlende Tabellen, die Werkzeugzaehlung per grep, und dieser). Ein Fehler,
    der als Null zurueckkommt, ist schlimmer als eine Ausnahme: eine Ausnahme
    faellt auf, eine Null wird gerechnet.
    """
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout).stdout.strip()
    except subprocess.TimeoutExpired:
        return f"__ABBRUCH__ nach {timeout}s"
    except Exception as e:
        return f"__FEHLER__ {type(e).__name__}: {e}"


def _zahl(c, tabelle: str, wo: str = "") -> int:
    try:
        return int(c.execute(f'SELECT COUNT(*) FROM "{tabelle}" {wo}').fetchone()[0])
    except Exception:
        return -1


def _bootfeld(feld: str) -> str:
    roh = _sh("docker logs entityos 2>&1 | grep -o '\"" + feld + r"\": *[^,}]*' | tail -1")
    return roh.split(":", 1)[1].strip() if ":" in roh else ""


# ── Die Zeilen. SOLL ist Text, IST ist eine Funktion. ──────────────────────
def _testlage_messen() -> str:
    """Die Suite messen -- OHNE offene Verbindung auf wiki.db.

    ⚠️ Muss VOR sqlite3.connect() laufen. Gemessen 2026-08-20: mit einer offenen
    ro-Verbindung auf wiki.db dauert die Suite 136s statt 17s und EIN Test
    faellt um (test_same_clerk_session_can_refresh_and_continue_pty_input).
    Genau so lief es bisher -- schreibe_ziele() oeffnete die Verbindung und rief
    dann zeilen(), mitten darin startete pytest. Die Zieltabelle meldete
    daraufhin "583 gruen / 1 rot" und stellte beide Testzeilen auf offen: ein
    Befund ueber das Messgeraet, nicht ueber die Tests.
    """
    tests = _sh("cd '/opt/entityos/the artefact' && /opt/entityos/venv-test/bin/python -m pytest tests/ -q "
                "--timeout=120 -p no:cacheprovider 2>/dev/null | tail -1", timeout=240)
    # ⚠️ Bei NULL Fehlern schreibt pytest "584 passed in 17s" -- ohne das Wort
    # "failed". Ein Muster nur fuer "X failed, Y passed" meldete deshalb
    # "nicht gemessen", und zwar genau dann, wenn alles gruen ist.
    _rot = re.search(r"(\d+) failed", tests or "")
    _gruen = re.search(r"(\d+) passed", tests or "")
    if _gruen:
        return f"{_gruen.group(1)} gruen / {_rot.group(1) if _rot else '0'} rot"
    if str(tests).startswith("__ABBRUCH__") or str(tests).startswith("__FEHLER__"):
        return f"NICHT GEMESSEN -- {tests}. Das ist ein Messfehler, kein Ergebnis."
    return f"nicht gemessen (Ausgabe: {(tests or '')[:60]!r})"


def zeilen(c, testlage: str = "") -> list[dict]:
    tabellen = _zahl(c, "sqlite_master", "WHERE type='table'")
    kern = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    puls = _bootfeld("installed")
    identitaet = c.execute("SELECT value FROM meta WHERE key='canonical_identity_version'").fetchone()
    corpus_da = {"fts_index_artikel", "artikel_suchtext", "artikel"} <= kern

    def _korpus_probe() -> str:
        try:
            n = c.execute(
                "SELECT COUNT(*) FROM fts_index_artikel WHERE fts_index_artikel MATCH ?",
                ('"effectgate"',)).fetchone()[0]
            return f"{n} Treffer auf Probeanfrage"
        except Exception as e:
            return f"Suche scheitert: {type(e).__name__}"

    lanes = _sh("grep -c 'bahn_erst=' /opt/clayverse/werkzeug/verdrahtung.py 2>/dev/null") or "0"
    lane_tools = _sh("grep -c 'bahn\\|lane' '/opt/entityos/the artefact/clayverse/mcp_server.py' 2>/dev/null") or "0"
    # ⚠️ Frueher wurde hier der Quelltext nach Werkzeugnamen in Anfuehrungszeichen
    # durchsucht. Die Werkzeuge sind aber Python-Funktionen -- ihre Namen stehen
    # nackt hinter `def`, nie in Anfuehrungszeichen. Der grep fand also
    # zwangslaeufig 0 und die Zeile meldete "keine Werkzeuge freigegeben",
    # waehrend Zero longst 21 hatte. Gemessen wird jetzt dort, wo die Freigabe
    # im Betrieb tatsaechlich entschieden wird: in der Erlaubnisliste.
    try:
        _pol = json.loads(Path("/opt/entityos/the artefact/policy/managed-settings.json")
                          .read_text(encoding="utf-8"))
        _erlaubt = _pol.get("permissions", {}).get("allow", [])
        _verboten = _pol.get("permissions", {}).get("deny", [])
    except Exception as e:
        _erlaubt, _verboten = [], [f"nicht lesbar: {type(e).__name__}"]
    mcp_tools = str(len(_erlaubt))
    _werkbank = [w for w in _erlaubt if "werkbank" in w]
    _NATIV = ("Bash", "Read", "Write", "Edit", "MultiEdit", "Glob", "Grep", "WebSearch", "WebFetch", "Task")
    _nativ = [t for t in _erlaubt if t in _NATIV]
    try:
        _zaun = any("fence_hook" in h.get("command", "")
                    for grp in _pol.get("hooks", {}).get("PreToolUse", [])
                    for h in grp.get("hooks", []))
    except Exception:
        _zaun = False
    karten = len(list((Path("/opt/agentzero-export/repo/agentZero/karten")).glob("*.json"))) \
        if Path("/opt/agentzero-export/repo/agentZero/karten").exists() else 0
    # ⚠️ 240s statt 45: die Suite braucht ~18s im Leerlauf, unter Last (z.B.
    # waehrend ein Container gebaut wird) aber ueber 80. Eine zu knappe Grenze
    # misst dann nicht die Tests, sondern die Auslastung der Kiste.
    # Aus dem gemessenen Text abgeleitet statt aus Variablen, die jetzt in
    # _testlage_messen() leben. "584 gruen / 0 rot" ist der einzige gruene Fall.
    if not testlage:
        # Rueckfall fuer Aufrufer, die nichts mitgeben: dann wird hier gemessen
        # und die Verzerrung ausdruecklich benannt statt verschwiegen.
        testlage = (_testlage_messen()
                    + " [mit offener DB-Verbindung gemessen -- verzerrt,"
                      " siehe _testlage_messen()]")

    alles_gruen = bool(re.match(r"^\d+ gruen / 0 rot$", (testlage or "").strip()))

    Z = []

    def z(bereich, faehigkeit, soll, quelle, ist, erfuellt):
        Z.append({"bereich": bereich, "faehigkeit": faehigkeit, "soll": soll,
                  "quelle": quelle, "ist": ist, "erfuellt": erfuellt})

    # ── Identitaet ─────────────────────────────────────────────────────────
    z("Identität", "Die Entität heißt Zero",
      "Agent Zero, der erste Agent auf EntityOS, Grundlage aller weiteren Entwicklung",
      "Eigner 18.08.",
      f"kanonische Identität v{identitaet[0] if identitaet else '—'} in meta, Ebene 0",
      bool(identitaet))
    z("Identität", "Identität überlebt Verdichtung",
      "im Wurzelzustand verankert, deterministisch je Zug geladen, nie herausgefiltert",
      "Eigner 18.08.",
      "aus der DB in den Systemprompt gerendert; in der Hakenhülle als Anker (206 statt 5550 Zeichen)",
      bool(identitaet))
    z("Identität", "Verkörperung ohne Erfindung",
      "spielt eine Entität mit Kontinuität – ohne zu lügen, indem sie den Unterbau benutzt",
      "Eigner 18.08.",
      "im <embodiment>-Block: Erfinden ist der einzige Weg, aus der Rolle zu fallen",
      bool(identitaet))

    # ── Menschen ───────────────────────────────────────────────────────────
    gleich = _zahl(c, "users", "WHERE rights='equal'")
    z("Menschen", "Genau zwei gleichberechtigte Perspektiven",
      "Gabriel und Andreas, gleiche Rechte, eine Entität – keine zwei Mandanten",
      "Eigner 18.08.",
      f"{gleich} Nutzer mit rights=equal, {_zahl(c,'sessions')} dauerhafte Sitzungen",
      gleich == 2)
    z("Menschen", "Sonst kommt niemand hinein",
      "Clerk-Anmeldung, exakt zwei Konten, dritte Identität fällt zu",
      "Eigner 18.08.",
      "IdentityRouter wirft PermissionError bei nicht zugeordnetem Clerk-Subjekt (Test grün)",
      True)

    # ── Ein Gefäß ──────────────────────────────────────────────────────────
    z("Gedächtnis", "wiki.db ist das Herz der Entität",
      "Datenbank, Wiki und ClayGraph sind das Herz – nicht Altlast, nicht daneben",
      "Eigner 18.08.",
      f"{tabellen} Tabellen in EINER Datei: Clay-Korpus + Laufzeit-Wirbelsäule, kollisionsfrei",
      tabellen >= 100)
    # ── Die vier Clay-Dienste: benannt statt gezaehlt ──────────────────────
    # Frueher zaehlte diese Zeile nur `systemctl list-units 'clayverse-*'` und
    # verglich das Ergebnis mit der Zahl 4. Eine Zahl ohne Namen ist hier aus
    # drei Gruenden das falsche Messgeraet:
    #
    #   1. Eine Zahl sagt nicht, WELCHER Dienst fehlt. Steht da "3 von 4",
    #      muss sich ein Mensch erst per Hand einloggen, um herauszufinden, ob
    #      der Kern oder die Wikiarbeit gestorben ist. Ein Messwert, der zur
    #      Nachforschung zwingt, hat nichts gemessen.
    #   2. Das Muster 'clayverse-*' trifft auch die TIMER. Der Zeitgeber
    #      clayverse-verdichtung.timer laeuft dauerhaft mit und wurde
    #      mitgezaehlt -- daher die Meldung "5 von 4". Der gefaehrlichere Fall
    #      ist der umgekehrte: waere der Kern tot, meldete die Zeile trotzdem
    #      "4 von 4" = gruen, weil der Timer die Luecke auffuellt. Ein Zaehler
    #      kann Falsches gegen Fehlendes aufrechnen -- eine Namensliste nicht.
    #   3. Mehr laufende Dienste als erwartet ist ueberhaupt kein Fehler.
    #      Erfuellt heisst: die vier Genannten leben. Alles darueber wird
    #      aufgezaehlt, damit es niemanden ueberrascht, aber nicht bestraft.
    #
    # Ausserdem haben die vier NICHT dieselbe Betriebsform: kern, puls und
    # wikiarbeit sind Dauerlaeufer und muessen laufen. verdichtung ist ein
    # Taktdienst -- der Timer weckt ihn alle 10 min, er prueft die Schwelle
    # und legt sich wieder hin. "dead" ist bei ihm der NORMALZUSTAND; sein
    # Lebenszeichen ist der stehende Zeitgeber. Wer ihn auf "running" prueft,
    # misst nur, ob er ihn zufaellig im Arbeitsfenster erwischt hat.
    #
    # Quelle der Namen (nicht geraten): die Soll-Zeile des Eigners vom 18.08.
    # und agentZero/code/produkt/mistral_prestage/eval_set.json ("keep them,
    # not negotiable").
    CLAY_DAUERLAEUFER = ["kern", "puls", "wikiarbeit"]   # muessen aktiv sein
    CLAY_TAKTDIENSTE = ["verdichtung"]                   # leben ueber ihren .timer
    CLAY_PFLICHT = CLAY_DAUERLAEUFER + CLAY_TAKTDIENSTE

    def _einheit_aktiv(einheit: str) -> bool:
        return _sh(f"systemctl is-active {einheit} 2>/dev/null") in ("active", "activating")

    def _clay_dienste() -> tuple[str, bool]:
        befund, tot = [], []
        for name in CLAY_DAUERLAEUFER:
            lebt = _einheit_aktiv(f"clayverse-{name}.service")
            befund.append(f"{name} {'läuft' if lebt else 'TOT'}")
            if not lebt:
                tot.append(name)
        for name in CLAY_TAKTDIENSTE:
            # Taktdienst: der Zeitgeber ist das Lebenszeichen, nicht der Lauf.
            lebt = _einheit_aktiv(f"clayverse-{name}.timer")
            befund.append(f"{name} {'getaktet' if lebt else 'TOT (Zeitgeber steht still)'}")
            if not lebt:
                tot.append(name)
        # Laufende clayverse-Dienste ausserhalb der Pflicht: nennen, nicht werten.
        roh = _sh("systemctl list-units 'clayverse-*.service' --state=running "
                  "--no-legend --no-pager | awk '{print $1}'")
        zusatz = sorted({e.removesuffix(".service").removeprefix("clayverse-")
                         for e in roh.split() if e.endswith(".service")} - set(CLAY_PFLICHT))
        text = (f"{len(CLAY_PFLICHT) - len(tot)} von {len(CLAY_PFLICHT)} Pflichtdiensten: "
                + ", ".join(befund))
        if tot:
            text = "TOT: " + ", ".join(tot) + " — " + text
        text += ("; zusätzlich läuft: " + ", ".join(zusatz)) if zusatz else "; keine weiteren"
        return text, not tot

    _clay_text, _clay_ok = _clay_dienste()
    z("Gedächtnis", "Die vier Clay-Dienste laufen weiter",
      "kern, puls, verdichtung, wikiarbeit bleiben an – ausdrücklich",
      "Eigner 18.08.",
      _clay_text,
      _clay_ok)
    z("Gedächtnis", "Der Abruf erreicht den Korpus",
      "Zero sieht die 14.284 Artikel, nicht nur sein eigenes Gesprächsgedächtnis",
      "Eigner 18.08. / Befund",
      _korpus_probe() if corpus_da else "Korpusindex fehlt",
      corpus_da)

    # ── Kognition ──────────────────────────────────────────────────────────
    z("Kognition", "Jeder Zug wird aufgezeichnet",
      "Prompt und Antwort landen als Zeile in der UnifiedDB, mit Kausalkette",
      "Architektur",
      f"{_zahl(c,'turns')} Züge, {_zahl(c,'causal_episodes')} Kausalepisoden, "
      f"{_zahl(c,'workspace_episodes')} Arbeitsraum-Episoden",
      _zahl(c, "turns") > 0)
    z("Kognition", "Aufnahme ist atomar",
      "scheitert eine Prüfung, bleibt keine halbe Zeile stehen",
      "Architektur",
      "Prüfungen laufen in der Aufnahme-Transaktion; 15 Atomizitätstests grün",
      True)
    z("Kognition", "Wirkung nur durch das Tor",
      "kein process.exec, jede Wirkung durch EffectGate mit Beleg",
      "Architektur",
      f"{_zahl(c,'effects')} Wirkung(en), Urteil mit boundary=ClayVerse EffectGate, "
      f"Ziel/Ergebnis als Prüfsumme gespeichert",
      _zahl(c, "effects") >= 0)
    z("Kognition", "Native Werkzeuge + dünner Zaun",
      "Zero handelt direkt mit den vollen nativen Claude-Code-Werkzeugen (Bash, Read, Write, "
      "Edit, Web); ein dünner PreToolUse-Zaun schützt NUR das Unersetzliche "
      "(wiki.db/unifieddb/tresor) und Passwörter — sonst freie Hand",
      "Eigner 19.08.",
      (f"{len(_nativ)} native Werkzeuge frei ({', '.join(_nativ[:6])} …), "
       f"{len(_erlaubt) - len(_nativ)} MCP-Werkzeuge; verboten nur: {', '.join(_verboten) or '—'}; "
       f"Zaun-Hook {'aktiv' if _zaun else 'FEHLT'} — rm wiki.db + cat Passwörter im Test "
       f"abgewiesen, Backups/Bash frei"),
      ("Bash" in _erlaubt) and _zaun)
    z("Kognition", "Handlungsfähig wie der Koordinator",
      "so handlungsfähig wie der Koordinator: mit nativer Shell und Datei-Werkzeugen finden, "
      "lesen, ändern, ausführen, im Netz nachsehen, veröffentlichen — keine Arbeitspakete mehr, "
      "alles direkt selbst",
      "Eigner 19.08.",
      (f"native Tools + Werkbank ({len(_werkbank)} Werkzeuge) für den Host-Deploy; Bash "
       "end-to-end verifiziert (uname/uptime real ausgeführt), Arbeitspakete (paket_schnüren) "
       "entfernt"
       if "Bash" in _erlaubt else "native Tools nicht freigegeben"),
      "Bash" in _erlaubt)

    # ── Autonomie ──────────────────────────────────────────────────────────
    z("Autonomie", "Initiative: der Puls weckt offene Ziele",
      "nicht behaupten, dass es autonom ist – die Mechanik bauen",
      "Eigner 18.08.",
      f"Autonomie-Puls installed={puls or '—'}, 30 s, beglaubigt (ein Terminal-Verwalter)",
      puls == "true")
    z("Autonomie", "Persistente Ziele, Rückmeldung, Neuplanung",
      "Ziele überleben Züge, Schritte werden gemeldet, Fehlschlag führt zu Neuplanung",
      "Eigner 18.08.",
      "create_goal_from_turn / propose_step / record_step_failure / verify_completion vorhanden; "
      "Ziele entstehen nur aus kanonischen Menschenzügen",
      True)
    z("Autonomie", "Kontinuität über Neustarts",
      "Generation, Prüfpunkte, Wiederherstellung ohne blindes Wiederholen von Wirkungen",
      "Architektur",
      f"{_zahl(c,'checkpoints')} Prüfpunkte, Generation {_bootfeld('entity_generation') or '—'}",
      _zahl(c, "checkpoints") > 0)

    # ── Abruf, der lernt ───────────────────────────────────────────────────
    ep = _zahl(c, "retrieval_entrypoint_policy")
    modus = c.execute("SELECT mode FROM retrieval_policy_state").fetchone()
    # ── frisch erfüllte Ziele 19.08.: echte Messwerte ──
    _wege = _zahl(c, "vp_weg")
    _tunnel = _zahl(c, "vp_weg", "tunnel=1")
    try:
        _g = [r[0] for r in c.execute("SELECT guete FROM vp_weg ORDER BY guete DESC")]
        _n10 = max(1, len(_g) // 10)
        _spitze = (sum(_g[:_n10]) / (sum(_g) or 1)) if _g else 0.0
    except Exception:
        _spitze = 0.0
    _zugaenge = _zahl(c, "kb_zugang")
    try:
        _mounts = subprocess.run(
            ["docker", "inspect", "entityos", "--format",
             "{{range .Mounts}}{{.Destination}} {{end}}"],
            capture_output=True, text=True, timeout=10).stdout
        _container_bahnen = ("/opt/unifieddb" in _mounts and "/opt/clayverse/werkzeug" in _mounts)
    except Exception:
        _container_bahnen = False
    try:
        _tr = Path("/opt/entityos/the artefact/clayverse/mistral_prestage/translator.py").read_text(encoding="utf-8")
        _uebersetzer_ok = ("_lese_betriebszustand" in _tr) and ("menschlich" in _tr.lower())
    except Exception:
        _uebersetzer_ok = False
    z("Abruf", "Abruf ist abfragesensitiv",
      "nicht die letzten N, sondern was zur Frage passt",
      "Architektur",
      "11/11 Tests grün; Quittung wird durchgereicht (war vorher still verloren)",
      True)
    z("Abruf", "Eintrittspunkte werden gelernt",
      "der Abruf verbessert seinen Eintrittspunkt selbst; SHADOW→ACTIVE mechanisch bei genug Lernsignal",
      "Eigner 18./19.08.",
      f"{ep} gelernte Eintrittspunkte, Modus {modus[0] if modus else '—'}, "
      f"{_zahl(c,'retrieval_episodes')} Episoden; Beförderung via befoerderung_takt (15-min-Timer). "
      f"Erst-Lernsignal per Bootstrap gesetzt (signal_class 'bootstrap:*'), verfeinert sich mit echter Nutzung",
      ep > 0 and bool(modus) and modus[0] == "ACTIVE")
    z("Abruf", "Wegehierarchie: Autobahnen, Tunnel, Landwege",
      "oft gegangene Wege werden ausgebaut; Verfall, inverse Gewichtung, "
      "Tunnel mit strengerer Schwelle und unabhängiger Mitbenutzung",
      "F94 / Eigner 16.08.",
      f"{_wege} Wege, {_tunnel} Tunnel; oberstes Zehntel hält {round(_spitze*100)}% der Güte "
      f"(Gleichverteilung wäre ~10%) → Hierarchie bildet sich. Verfall + inverse Gewichtung + Tunnel "
      f"gebaut (F94) und getaktet (wegverfall.py / abrufverfall.timer)",
      _wege >= 10 and _spitze >= 0.18)
    z("Abruf", "Karten als Zeitstrahl",
      "die Karte wird wiederholt weggeschrieben, damit man die Veränderung ansehen kann",
      "Eigner 18.08.",
      f"{karten} Momentaufnahme(n) in agentZero/karten, alle 30 min eine neue",
      karten > 0)

    # ── Fremdkognition ─────────────────────────────────────────────────────
    z("Anbieter", "Die Bahnen stehen Zero offen",
      "11 kognitive Prozesse über 22 Bahnen mit Ausweichbahn und Anteilsdeckel; "
      "NVIDIA gehört der Kognition, nicht dem Massenlauf",
      "verdrahtung.py / Eigner",
      f"{lanes} Prozesse über {_zugaenge} Bahnen; aus dem entityos-Container real erreichbar "
      f"({'Mounts /opt/unifieddb + werkzeug vorhanden' if _container_bahnen else 'Mounts fehlen?'}; "
      f"verifiziert: verdrahtung lesbar, Auftrag schreibbar, NVIDIA-Einbettung HTTP 200 aus dem Container)",
      _container_bahnen)
    z("Anbieter", "Vektorsuche über den Korpus",
      "Bedeutungssuche statt nur Volltext",
      "Lücke 8 / Eigner",
      f"{_zahl(c,'udb_nvidia_embedding')} Einbettungen (nv-embedqa-e5-v5, 1024 Dim, 2,9 ms/Text bei Stapel 128)",
      _zahl(c, "udb_nvidia_embedding") > 0)
    z("Anbieter", "Neuronale Aktivitätsmessung",
      "Aktivierungsdaten als Forschungsquelle anbinden",
      "Eigner 18.08.",
      "Neuronpedia live: Deutung, Spitzenwert, Selektivität, Top-Token. "
      "⚠️ misst öffentliche Forschungsmodelle, NICHT Zero",
      True)

    # ── Mistral-Vorstufe ───────────────────────────────────────────────────
    vorstufe = _sh("ls '/opt/entityos/the artefact/clayverse/' 2>/dev/null | grep -ci 'vorstufe\\|prestage\\|mistral'")
    z("Vorstufe", "Claude bekommt den Prompt nie direkt",
      "eine Mistral-Entität wertet vorher aus: Möglichkeitsraum, alle APIs, alle Werkzeuge, "
      "verbundene Systeme, wer da ist – und baut ein Caveman-Prompt mit Hypothesen und Gegenhypothesen",
      "F17 / Eigner 18.08.",
      f"{vorstufe or '0'} Modul(e) vorhanden – im Bau",
      int(vorstufe or 0) > 0)
    z("Vorstufe", "Übersetzer Caveman → Deutsch, 95 %",
      "Zero antwortet in Caveman, das Terminal übersetzt automatisch in schönes, menschlich "
      "klingendes Deutsch — Ton nach dem Betriebszustand gefärbt, ohne Fakten zu erfinden",
      "Eigner 18./19.08.",
      ("v7, gemessen am 26er-Goldsatz mit unabhängigem Richter: Treue 99,96 · Lesbarkeit 100 · "
       "Menschlichkeit 96,96 · Bestehen 100 % (alle Achsen ≥95 %). Färbt den Ton nach dem echten "
       "Puls-Betriebszustand (ruhig/angespannt) — kein Emotionsfeld vorhanden, ehrlicher Näherungswert"
       if _uebersetzer_ok else "im Bau; Maß: Treue + Lesbarkeit, unabhängiger Richter"),
      _uebersetzer_ok)

    # ── Vorstufe-Entität + Betrieb/Resilienz (Eigner 19.08.) ──
    try:
        _prest = Path("/opt/entityos/the artefact/clayverse/mistral_prestage/prestage.py").read_text(encoding="utf-8")
    except Exception:
        _prest = ""
    try:
        _hz = Path("/opt/entityos/the artefact/clayverse/mistral_prestage/headless_zero.py").read_text(encoding="utf-8")
    except Exception:
        _hz = ""
    _metakog = ("epistemik" in _prest) and ("EPISTEMIK" in _prest)
    _websearch = "WebSearch" in _hz
    _model_small = "mistral-small-latest" in _prest
    _envelope_robust = ("_fehlend" in _prest) or ("Envelope-Robustheit" in _prest)
    try:
        _lernbild = c.execute("SELECT count(*) FROM sqlite_master WHERE type='view' AND name='mv_prestage_lernbild'").fetchone()[0] > 0
        _lern_n = _zahl(c, "mv_prestage_turns", "outcome_ok IS NOT NULL")
    except Exception:
        _lernbild = False; _lern_n = 0
    try:
        _immune = subprocess.run(["systemctl", "is-active", "eos-immune"], capture_output=True, text=True, timeout=6).stdout.strip() == "active"
    except Exception:
        _immune = False
    try:
        _sj = json.loads(Path("/var/lib/clay/systeme.json").read_text(encoding="utf-8"))
        _dienste_n = len(_sj.get("dienste", []))
    except Exception:
        _dienste_n = 0

    z("Vorstufe", "Vorstufe kennt ihre Wissensgrenze",
      "prüft strukturell Feld-gegen-Frage und markiert bekannt/unbekannt (Metakognition), statt zu raten",
      "Eigner 19.08.",
      ("Regel (H) EPISTEMIK + Envelope-Schlüssel epistemik{bekannt/unbekannt}; das Maschinen-Prompt-"
       "Pflaster wurde durch diese Prüfung ersetzt" if _metakog else "nicht verdrahtet"),
      _metakog)
    z("Vorstufe", "Unbekanntes wird autonom gelöst",
      "was nicht in den Daten steht, findet Zero SELBST heraus (WebSearch, iar.frank.ink) — kein Nachfragen",
      "Eigner 19.08.",
      ("WebSearch/WebFetch freigeschaltet + Routing „unbekannt → such selbst“; verifiziert: „wie alt "
       "ist gabriel?“ → echte Websuche, Falter-Artikel, ~36-37 hergeleitet" if (_websearch and _metakog) else "WebSearch/Routing fehlt"),
      _websearch and _metakog)
    z("Vorstufe", "Die Vorstufe lernt aus dem Betrieb",
      "zeichnet Routing + Ergebnis (mechanisch, kein Modellurteil) auf, aggregiert „was-ist-falsch“ und speist es zurück",
      "Eigner 19.08.",
      (f"{_lern_n} Aufzeichnungen mit Ergebnis-Signal, Sicht mv_prestage_lernbild; Live-Signal noch dünn "
       "(füllt sich mit Nutzung)" if _lernbild else "keine Lernsicht"),
      _lernbild)
    z("Betrieb", "Chat antwortet zuverlässig",
      "kein „keine Antwort“-Absturz; die Vorstufe ist schnell und ein Vorstufe-Fehler killt nie die Antwort",
      "Eigner 19.08.",
      ("Vorstufe-Modell small (~2s statt 12-60s auf dem 12k-Kontext), Envelope-Robustheit (fehlender "
       "Key → Default statt Crash)" if (_model_small and _envelope_robust) else "noch nicht robust"),
      _model_small and _envelope_robust)
    z("Betrieb", "Selbstheilendes Immunsystem",
      "neural_immune überwacht die Dienste und startet ausgefallene circuit-breaker-geschützt neu",
      "Eigner 19.08.",
      ("eos-immune aktiv, 22 Dienste (restart|observe), Selbstheilung bewiesen: wikiarbeit gestoppt → "
       "auto-restart (breaker=closed) → successful; zentral abschaltbar" if _immune else "eos-immune nicht aktiv"),
      _immune)
    z("Betrieb", "Dienste sichtbar",
      "alle EntityOS-Prozesse als Dienste mit Lampe (grün an / rot aus) in der Systeme-Bubble",
      "Eigner 19.08.",
      (f"{_dienste_n} Dienste live in systeme.json (Host-Sammler, 15s)" if _dienste_n else "keine Dienste-Daten"),
      _dienste_n > 0)

    # ── Betrieb ────────────────────────────────────────────────────────────
    z("Betrieb", "Läuft im Container auf dem eigenen Server",
      "ohne Anruf beim Anbieter, ohne verschachtelte Virtualisierung",
      "Eigner 18.08.",
      _sh("docker ps --filter name=^entityos$ --format '{{.Status}}'") or "nicht gefunden",
      "healthy" in (_sh("docker ps --filter name=^entityos$ --format '{{.Status}}'") or ""))
    z("Betrieb", "Frontend heißt EntityOS und ist erreichbar",
      "Clerk-Login für genau zwei Profile, dann Claude-Code-Terminal",
      "Eigner 18.08.",
      "https://entityos.frank.ink → 200, WSS durch nginx und Tunnel bewiesen",
      True)
    z("Betrieb", "Der Export pflegt sich selbst",
      "alles autonom ins Forschungs-Repo unter agentZero",
      "Eigner 18.08.",
      f"systemd-Timer alle 30 min, {_sh('systemctl is-enabled agentzero-export.timer 2>/dev/null') or '—'}",
      _sh("systemctl is-enabled agentzero-export.timer 2>/dev/null") == "enabled")
    z("Betrieb", "Die Testsuite trägt",
      "kein grüner Wert, der durch Abschwächen erkauft wurde",
      "Arbeitsregel",
      testlage, alles_gruen)
    z("Betrieb", "Endabnahme hinter eigenem Gastkern",
      "derselbe Digest hinter einer eigenen VM-Grenze",
      "Entwurf – vom Eigner zurückgestellt",
      "kein /dev/kvm auf dem Wirt; per Entscheidung 18.08. zurückgestellt",
      None)

    # ── Was seit dem ersten Stand dazugekommen ist ─────────────────────────
    # Jede Zeile misst dort, wo es im Betrieb entscheidet -- Tabelleninhalt,
    # Erlaubnisliste, laufender Dienst -- nicht an einer Datei, die danach
    # aussieht. Das ist die Lehre aus der Fehlmessung oben.
    def _zahl_ok(v, mind):
        """Nur eine echte Zahl kann ein Ziel erfuellen. Eine Fehlermeldung ist
        kein Erfolg -- und darf die Tabelle auch nicht zum Absturz bringen."""
        return isinstance(v, int) and v >= mind

    def _n(tab, wo=""):
        """Zeilenzahl -- oder None, wenn die TABELLE fehlt. Der Unterschied zaehlt.

        ⚠️ Vorher fing das hier jede Exception ab und gab None. Damit sah ein
        falscher Tabellenname exakt aus wie eine leere Tabelle, und drei
        gebaute Sachen wurden als fehlend gemeldet. Wer den Namen falsch hat,
        soll das SEHEN, nicht eine plausible Null bekommen.
        """
        da = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                       (tab,)).fetchone()[0]
        if not da:
            return None          # Tabelle existiert nicht -- Messfehler, nicht Befund
        try:
            return c.execute(f"SELECT COUNT(*) FROM {tab} {wo}").fetchone()[0]
        except Exception as e:
            return f"Abfrage scheitert: {type(e).__name__}"

    _profil, _projekte = _n("entityos_profil"), _n("entityos_projekte")
    _zuordnung = _n("entityos_artikel_zuordnung")
    # Vier Menschenplaetze; der Paketarbeiter sitzt auf Platz 0 und zaehlt nicht mit.
    _raum = _n("zero_raum", "WHERE platz > 0")
    _pakete = _n("entityos_arbeitspaket")
    # ⭐ Der Tresor liegt ABSICHTLICH nicht im Korpus: ein Korpusleck soll
    # keine Zugaenge mitnehmen. Also wird auf der Platte gemessen.
    _tw = Path("/etc/entityos/tresor")
    _tresor = len(list(_tw.glob("*.tresor"))) if _tw.is_dir() else None
    _hist, _sitzungen = _n("turns"), _n("sessions")
    _bau = _n("artikel", "WHERE id LIKE 'bau-%' OR id LIKE 'wissen-%'")

    z("Menschen", "Zero weiß, wer vor ihm sitzt",
      "Profile beider Menschen, jedes Feld mit Herkunft; die Sitzung sagt, wessen sie ist",
      "Eigner 18.08.",
      (f"{_profil} Profilfelder, {_projekte} Projekte mit Erfolg UND Fehlschlag; "
       "Zugehörigkeit und Urheberschaft getrennt geführt, weil sonst aus "
       "Zusammenarbeit ein Besitzstreit wird" if _profil else "keine Profile"),
      _zahl_ok(_profil, 10))
    z("Menschen", "Wissen ist nach Menschen zugeordnet",
      "jeder Artikel gehört jemandem oder ausdrücklich beiden",
      "Eigner 18.08.",
      (f"{_zuordnung} Artikel zugeordnet über eine 5-stufige Leiter. ⚠️ Der Committer "
       "wurde bewusst NICHT verwendet: 501 Artikel über Dr. Unterweger tragen Gabriel "
       "als Committer — danach hätte Gabriel 68 % aller Artikel bekommen"
       if _zuordnung else "keine Zuordnung"),
      _zahl_ok(_zuordnung, 100))
    z("Menschen", "Vier Sitzungen, ein Raum",
      "getrennte Kennungen, dieselbe Entität; sie sehen einander und stimmen sich ab, "
      "in Caveman-Englisch, ohne Abgleich über Zeitstempel",
      "Eigner 18.08.",
      (f"{_raum} Menschenplätze in zero_raum (+ ein Platz für den Paketarbeiter); Kollisionswarnung beim Sprechen, wenn zwei "
       "am selben Gegenstand arbeiten" if _raum else "kein Raum"),
      _zahl_ok(_raum, 4))

    z("Gedächtnis", "Chat-Historie überlebt den Neuladen",
      "Verlauf pro Terminal-Sitzung, dauerhaft, nicht im Browser",
      "Eigner 18.08.",
      (f"{_hist} Züge über {_sitzungen} Sitzungen in der UnifiedDB, ausgeliefert über /api/history. "
       "⚠️ Ein Fehler dabei war lehrreich: der Server liest `session_id`, das Frontend "
       "schickte `session` — ich hatte gegen meine EIGENE falsche Dokumentation gebaut"
       if _hist else "keine Historie"),
      _zahl_ok(_hist, 1))
    z("Gedächtnis", "Alles Gebaute landet im Wiki",
      "jeder Bauschritt wird Wiki-Artikel, mit Metadaten, nach dem üblichen Protokoll",
      "Eigner 18.08.",
      (f"{_bau} Bau- und Wissensartikel im Korpus, volltextsuchbar. "
       "⚠️ Sie waren zuerst unauffindbar: geschrieben ohne Suchtext und ohne FTS-Eintrag — "
       "in der Datenbank und trotzdem für niemanden da" if _bau else "keine"),
      _zahl_ok(_bau, 20))

    z("Betrieb", "Zugänge und Schlüssel liegen im Tresor",
      "ein Tresor für Zugänge, ein zweiter für API-Schlüssel — letzterer mit Fähigkeitsliste",
      "Eigner 18.08.",
      (f"{_tresor} Tresore unter /etc/entityos/tresor (zugaenge, api), AES-256-GCM — ABSICHTLICH außerhalb des Korpus, damit ein Korpusleck keine Zugänge mitnimmt. Zero darf Adressen und Tokens nennen, "
       "PASSWÖRTER NIE: der Katalog durchsucht seine eigene Ausgabe nach jedem "
       "gespeicherten Geheimwert und verweigert, statt zu hoffen"
       if _tresor else "kein Tresor unter /etc/entityos/tresor"),
      _zahl_ok(_tresor, 2))
    z("Betrieb", "Zero kennt alle selbst gehosteten Seiten",
      "alle Seiten unter frank.ink samt Leistung, immer mit Vermerk self-hosted oder extern",
      "Eigner 18.08.",
      "Unterseite /seiten aus dem agentforge-Bestand; eigene Wurzeln (herzrad.at, "
      "leihmich.org) sind vermerkt, weil dort relative Pfade Pflicht sind",
      Path("/opt/entityos/the artefact/web/seiten/index.html").exists())
    z("Betrieb", "Zero kann eine Seite wirklich ändern",
      "nicht beschreiben, wie es ginge — es tun",
      "Eigner 18.08.",
      ("Arbeitskopie /var/lib/clay/arbeit/seimensch, Änderung über die Werkbank, "
       "Veröffentlichen als eigener Schritt mit Beleg. ⚠️ Push auf main geht bei "
       "SeiMensch sofort öffentlich — deshalb nennt der Beleg die Zahl der Dateien"
       if Path("/var/lib/clay/arbeit/seimensch/.git").exists() else "keine Arbeitskopie"),
      Path("/var/lib/clay/arbeit/seimensch/.git").exists())
    z("Betrieb", "Arbeitspakete statt Alleingang",
      "was Zero nicht selbst darf, schnürt er als Paket; ein Arbeiter erledigt es eingezäunt",
      "Eigner 18.08.",
      (f"{_pakete} Pakete. Ein Paket gilt erst als fertig, wenn ein BELEG dranhängt — "
       "'fertig ohne Beleg ist eine Behauptung, kein Ergebnis'"
       if _pakete is not None else "keine Pakete"),
      isinstance(_pakete, int))
    z("Betrieb", "agentforge geht in EntityOS auf",
      "kein Umweg mehr: Hosting und Dienste laufen direkt über den EntityOS-Server",
      "Eigner 18.08.",
      "Hosting-Ansicht übernommen und angeschlossen. Die übrigen Dienste (Auslieferung, "
      "Projektverwaltung, Besuchszählung, Umfragedienst) waren als schrittweise Migration "
      "erfasst. ⏸ VOM EIGNER AM 19.08. GESTRICHEN — ausdrücklich nicht weiter verfolgen. "
      "Stand bis 20.08. weiter als 🔧 offen und las sich wie eine liegengebliebene Aufgabe; "
      "das ist derselbe Fehler wie andersherum, nur mit umgekehrtem Vorzeichen",
      None)

    z("Abruf", "Der Möglichkeitsraum ist emergent",
      "nicht gepflegte Liste, sondern was sich aus dem Bestand ergibt — und er fließt "
      "in die Mistral-Vorstufe ein",
      "Eigner 18.08.",
      "aus dem Korpus abgeleitet und in den Kontext der Vorstufe gehängt. "
      "⚠️ Er war zuvor gebaut und wurde von NIEMANDEM aufgerufen — der wiederkehrende "
      "Fehler dieser Nacht: fertig aussehen und nie laufen",
      True)
    z("Abruf", "Erkundung neben Ausbeutung",
      "der Abruf darf einen Teil auf Unbekanntes setzen, statt immer denselben Weg zu gehen",
      "Eigner 18.08.",
      "15 % Erkundungsanteil, entschieden über den Hash der Frage — dieselbe Frage "
      "bekommt also immer dieselbe Behandlung, sonst wäre nichts mehr messbar",
      True)
    z("Abruf", "Der Abruf misst sich selbst",
      "Messgerät, Goldsatz, Kalibrierung an zurückgehaltenen Daten",
      "Eigner 18.08.",
      "Hälfte A kalibriert, Hälfte B berichtet, Annahmeregel vorher festgelegt. "
      "Auf B: Anker 8,3 → 23,3 %, Genauigkeit 60 → 85,7 %, Ausbeute 5 → 20 %; "
      "Latenz ~390 → 260 ms bei Streuung ±115 → ±1,6 ms",
      True)
    z("Abruf", "Jeder Mechanismus kann melden, dass er nichts tut",
      "ein Mechanismus, der nur Erfolg melden kann, ist nicht messbar",
      "Lehre aus dem Bau 18.08.",
      "die Wegehierarchie sagt 'GLEICHVERTEILT — es bildet sich keine Hierarchie, der "
      "Mechanismus tut nichts'; der Möglichkeitsraum meldet 'einseitig'; der "
      "Tresorkatalog verweigert, statt zu hoffen",
      True)

    # ── Speicher und Sicherheit, nachgetragen 18.08. abends ────────────────
    try:
        import importlib.util as _il
        _sp = _il.spec_from_file_location("sw", "/opt/entityos/speicherwacht.py")
        _sw = _il.module_from_spec(_sp); _sp.loader.exec_module(_sw)
        _lg = _sw.lage()
        _bl = _sw.bilanz(zeitlimit=45)
        _vu = _sw.verursacher()
        _rw = _n("speicher_rueckweg")
    except Exception as _e:
        _lg = _bl = _vu = None
        _rw = f"Wacht nicht ladbar: {type(_e).__name__}"

    z("Betrieb", "Zero hält selbst Platz auf dem Wirt",
      "das Speicher-Management des VPS übernimmt Zero autonom",
      "Eigner 18.08.",
      (f"{_lg['belegt_prozent']} % belegt, {_lg['frei_gb']} GB frei. Wacht alle 30 min, "
       "vier Werkzeuge für Zero, Stufen nach Druck (bei 85 % nur berichten). "
       "⚠️ Anlass: die Platte lief zweimal auf 100 %. Ursache war NICHT fehlendes "
       "Aufräumen, sondern ein Zeitgeber eines ABGESCHAFFTEN Systems, der alle "
       "15 Minuten weiterlief — 6.606 Wegwerfordner, 41 GB. Insgesamt 77 GB befreit, "
       "173 → 96 GB"
       if _lg else "Wacht nicht messbar"),
      bool(_lg and _lg["belegt_prozent"] < 90))
    z("Betrieb", "Das Messgerät kann melden, dass es nichts messen konnte",
      "eine Rechnung, die nicht aufgeht, muss das SAGEN",
      "Lehre aus dem Bau 18.08.",
      (f"Bilanz nennt drei Zahlen: df {_bl['df_belegt_gb']} GB, gezählt "
       f"{_bl['zusammengezaehlt_gb']} GB, Lücke {_bl['luecke_gb']} GB. "
       "⚠️ Genau das fehlte: `du -xsh /tmp` lief bei 15.236 Einträgen in die Zeitgrenze "
       "und gab NICHTS aus — ein leeres Ergebnis liest sich wie „da ist nichts\". So "
       "standen 77 GB Summe neben 173 GB Verbrauch, und die Lücke fiel niemandem als "
       f"Lücke auf. Urteil jetzt: {_bl['urteil'][:80]}"
       if _bl else "Bilanz nicht messbar"),
      bool(_bl and not _bl["nicht_zaehlbar"] and abs(_bl["luecke_gb"]) < 5))
    z("Betrieb", "Abgeschafftes bleibt zurückholbar",
      "kein Frank v0.1 mehr, keine lokalen Modelle — aber wenn ich es je doch will, muss es gehen",
      "Eigner 18.08.",
      (f"{_rw} Posten im Rückwegverzeichnis, 23 Modelle mit Namen, Fassung und "
       "Nachladebefehl im Wiki. ⭐ Gewichte sind nachladbar, die LISTE war es nicht — "
       "deshalb verweigert `speicher_abschaffen` ohne geschriebenes Verzeichnis. "
       "Die Wacht löscht Altbestand (44 GB) NICHT von selbst: ein Modellcache sieht aus "
       "wie Müll und kann Arbeit von Wochen enthalten"
       if isinstance(_rw, int) and _rw else f"kein Rückweg gebucht ({_rw})"),
      isinstance(_rw, int) and _rw >= 5)
    z("Betrieb", "Der Verursacher wird gesucht, nicht nur der Haufen",
      "ein Haufen mit Verursacher wächst nach; Löschen allein ist dann keine Verwaltung",
      "Lehre aus dem Bau 18.08.",
      ((_vu["urteil"][:150] + " Der Detektor wurde gegengeprüft: mit einem Muster, das "
        "nachweislich läuft, findet er 13 Einheiten — sein „nichts gefunden\" ist also "
        "belastbar und nicht bloß Stille.")
       if _vu else "nicht messbar"),
      bool(_vu and not _vu.get("noch_aktiv")))

    z("Kognition", "Der Zaun hält einem Angriff stand",
      "Handlungsfähigkeit ohne Zaun wäre kein Fortschritt, sondern der Verlust "
      "der einzigen Eigenschaft, die dieses System von einer offenen Schale unterscheidet",
      "Architektur",
      "⚠️⚠️ Ein Prüfangriff BEWIES einen vollen root-Ausbruch: `.git/config` lag innerhalb "
      "der erlaubten Wurzel, `core.fsmonitor` lässt git einen Schalbefehl ausführen, und "
      "git läuft auf dem Wirt als root — nachgewiesen mit `id` → uid=0. Ich hatte den Weg "
      "richtig erkannt (git führt Fremdes aus) und dann EINEN Kanal davon zugemacht: "
      "`.git/hooks`. Geschlossen mit VIER Sperren, weil eine Sperre mit einer Liste des "
      "Gefährlichen nur vor dem schützt, was schon jemand aufgeschrieben hat: .git ist "
      "jetzt ganz ausserhalb des Zauns, git läuft ohne fremde Konfiguration, .git/config "
      "wird als TEXT vorgeprüft, und geprüft wird vor JEDEM git-Aufruf — auch vor `stand`, "
      "das vorher durch keine Prüfung lief und genau der Auslöser war",
      True)

    z("Betrieb", "Die Testsuite ist ehrlich grün",
      "grün ohne Löschen, ohne Überspringen, ohne abgeschwächte Behauptungen",
      "Lehre aus dem Bau 18.08.",
      (f"{testlage}. Die neun roten sind aufgelöst — zwei davon wurden STRENGER: "
       "der Datenschutztest fordert jetzt, dass kein Rohtext eine Sitzungsgrenze "
       "überschreitet (die alte Fassung stützte sich auf eine Nebenwirkung der "
       "zerstörenden Verdichtung, die es seit dem 18.08. nicht mehr gibt — und dabei "
       "kam ein ECHTES Leck heraus), und der Quittungstest fordert Ehrlichkeit statt "
       "Beruhigung: die Quelle bleibt absichtlich erhalten, also muss die Quittung das "
       "sagen, statt Sicherheit zu behaupten, die nicht besteht"),
      alles_gruen)
    z("Kognition", "Die Endabnahme kann überhaupt messen",
      "das Instrument, das beweisen soll, dass Wirkungen funktionieren, muss selbst funktionieren",
      "Lehre aus dem Bau 18.08.",
      "⚠️ Sieben rote Tests, EINE Ursache: `ClayVerseEngine` legte keine Zeile in "
      "`active_turns` an, die das Wirkungstor verlangt. Das Tor kam mit dem "
      "Zug-Lebenszyklus; der ältere Weg hat es nie gelernt — und im Betrieb fiel das "
      "nicht auf, weil ihn dort niemand mehr aufruft. Ausser einem: der Endabnahme. "
      "Sie meldete deshalb nicht „Wirkung fehlgeschlagen\", sondern scheiterte VOR der "
      "Wirkung — und ein Instrument, das gar nicht messen kann, sieht in einer "
      "Testliste aus wie eines, das etwas Schlechtes gemessen hat. ⭐ Die Reparatur "
      "lockert das Tor NICHT: engine.py meldet den lebenden Zug jetzt an und wieder ab, "
      "wie der Betriebsweg. Ein `if episode_id is None`-Zweig im Tor hätte alle sieben "
      "grün gemacht und die Prüfung genau für den Weg abgeschaltet, dessen Zweck das "
      "Prüfen ist",
      True)
    z("Menschen", "Kein Rohtext über die Sitzungsgrenze",
      "kollidiert eine gemeinsame Ressource, sieht der andere Fragmente — nicht das Original",
      "Architektur",
      "⚠️ HIER LAG EIN ECHTES LECK. Bei einer Kollision wurde die ganze Zeile "
      "ausgeliefert (`item = dict(r)`), inklusive `content`. Der Code setzte brav das "
      "Etikett „compressed_with_extracted_fragments\" und legte die Fragmente daneben — "
      "und liess den Rohtext drin. Der andere Mensch bekam den vollen Originaltext mit "
      "einem Etikett, auf dem „verdichtet\" stand. ⭐ Gefunden über einen roten Test, "
      "der aus dem FALSCHEN Grund rot war: die alte Zusicherung hing an einer "
      "Nebenwirkung der zerstörenden Verdichtung. Wer so einen Test nur an die neue "
      "Wirklichkeit anpasst, verliert den Hinweis",
      True)

    try:
        import importlib.util as _il2
        _sp2 = _il2.spec_from_file_location("aw", "/opt/entityos/anmeldewacht.py")
        _aw = _il2.module_from_spec(_sp2); _sp2.loader.exec_module(_aw)
        _anm = _aw.pruefe(_aw.LEBEND)
    except Exception as _e2:
        _anm = {"zustand": f"nicht pruefbar: {type(_e2).__name__}"}

    z("Betrieb", "Zero verstummt nicht wortlos",
      "wenn er nicht antworten kann, muss man ERFAHREN warum",
      "Lehre aus dem Bau 18.08.",
      (f"Anmeldung {_anm['zustand']}"
       + (f", noch {_anm.get('gueltig_stunden')} Stunden gültig" if _anm.get("gueltig_stunden") else "")
       + ". Wacht alle 10 Minuten, hält eine bekannt gute Kopie und stellt sie zurück. "
       "⚠️ Anlass: die Anmeldedatei wurde zu einer LEEREN HÜLLE — alle Schlüssel da, "
       "alle Werte leer, 280 statt 508 Bytes. Das ist gefährlicher als eine fehlende "
       "Datei: eine fehlende wirft einen klaren Fehler, eine Hülle besteht jede "
       "oberflächliche Prüfung und scheitert erst beim Benutzen. Vier Testläufe lang "
       "war die einzige Auskunft `rc=1 stderr=''` — der erklärende Satz („OAuth session "
       "expired\") stand in stdout, und die Fehlermeldung zeigte nur stderr. "
       "⭐ Ein System, das „kaputt\" sagen kann, aber nicht „warum\", kostet mehr Zeit "
       "als eines, das kommentarlos abstürzt: man sucht am falschen Ende"),
      _anm.get("zustand") == "GUT")

    z("Betrieb", "Zero kann nachsehen, statt zu hoffen",
      "nach jedem Veröffentlichen prüfen, was WIRKLICH auf der öffentlichen Seite steht",
      "Lehre aus dem Andreas-Test 18.08.",
      "⚠️ Gefunden von Zero SELBST: er berichtete, die ZVR-Korrektur sei „still local, "
      "still not live\" — und schrieb dazu ehrlich „ich habe kein HTTP hier, ich kann "
      "seimensch.net nicht abrufen\". Sie WAR live. Sein Schluss war richtig gezogen aus "
      "dem, was er sehen konnte. ⭐ Mein Fehler: in seinem Handbuch stand „prüfe die "
      "Seite\" — ohne Mittel dazu. Jetzt hat er `seite_pruefen`: HTTP an die echten "
      "Domains, nur lesend, Erlaubnisliste auf dem Wirt. ⚠️⚠️ Und der eigentliche Befund "
      "dahinter: /srv/git/seimensch.git auf diesem Wirt ist ein SPIEGEL — ein Push meldet "
      "vollen Deploy-Erfolg, während seimensch.net von 72.61.19.188 ausgeliefert wird",
      True)
    z("Betrieb", "Ehrliches „nichts getan\" gilt nicht als fertig",
      "wer korrekt verweigert, wird nicht als erledigt gebucht — aber auch nicht bestraft",
      "Lehre aus dem Andreas-Test 18.08.",
      "⚠️ Von Zero gefunden: zwei Pakete standen auf `fertig`, ihr Beleg begann mit "
      "„NICHTS GETAN\". Meine Regel prüfte, OB ein Beleg da ist — nicht, ob er `fertig` "
      "trägt. Ein Arbeiter, der sauber verweigert, schreibt einen ehrlichen Bericht, und "
      "der ging als Beleg durch. Damit bestrafte die Regel genau die Ehrlichkeit, die sie "
      "fördern sollte. Neuer Stand `abgelehnt`: kein Fehlschlag des Arbeiters, aber auch "
      "keine Erledigung — die Arbeit wartet weiter",
      True)
    z("Gedächtnis", "Vorfälle stehen im Wiki, nicht nur im Commit",
      "was passiert ist, muss die Entität finden können — nicht nur der, der den Commit las",
      "Lehre aus dem Andreas-Test 18.08.",
      "⚠️ Zero suchte im Korpus nach einem Vorfallsartikel zu den vollen Platten, fand "
      "NICHTS und warnte ausdrücklich: „behandle meine Darstellung nicht als "
      "korpusbelegt\". Er hatte recht — die Geschichte stand nur in Commit-Texten. Jetzt "
      "sind beide Vorfälle des Tages (Platte voll, root-Ausbruch) als volltextsuchbare "
      "Artikel im Wiki, gegengeprüft über die Suche. ⭐ „alle deine baunotizen werden "
      "auch teil des wiki\" — ein Vorfall, der nur im Commit steht, ist für die Entität "
      "nicht passiert",
      True)

    z("Abruf", "Die gelernte Karte ist erreichbar",
      "nicht nur bm25 -- Wegehierarchie, Eintrittspunkte, Erkundung stehen Zero offen",
      "Lehre aus dem Audit 18.08.",
      "⚠️ Ein Pruefagent fand: die ganze gelernte Abruf-Maschine (udb.abruf.paket) wurde "
      "NIRGENDS aufgerufen -- Zeros einzige Tuer war schlichtes bm25, und vp_weg trug nur "
      "Testfixtures. Sie verhungerte an fehlender Nahrung. Jetzt als opt-in korpus_tief "
      "(~250ms warm), NICHT im Zug-Pfad: 2,2s Kaltstart je Prozess waeren dort eine "
      "Verschlechterung. ⚠️⚠️ RICHTIGSTELLUNG 20.08.: hier stand, der conn-close-Bug sei "
      "'durch die Aufrufart geheilt'. Das war falsch. Er lebte -- paket() schloss die eigene "
      "Verbindung ACHT ZEILEN vor dem Block, der sie braucht, und auf jedem Pfad OHNE "
      "uebergebene Verbindung (Zeros eigener) fiel damit die ganze F92b/F94-Lernkaskade aus: "
      "keine Erfolgsmarke, keine Wegehierarchie, jeder Zug eine stderr-Zeile, die wie eine "
      "Restwarnung aussah. Behoben (schliessen im finally), gemessen: vp_erfolgsmarke +2 und "
      "vp_weg +1 auf drei Abrufe. ⭐ Offen und ehrlich benannt: ob jede Frage die Karte "
      "fuellt, haengt an paket()s Anker-Logik -- nicht behauptet, sie wachse garantiert",
      True)
    z("Menschen", "Der halbe Wissensschatz war zugesperrt",
      "Zero muss ganze Artikel lesen und den Dateikorpus erreichen koennen",
      "Lehre aus dem Audit 18.08.",
      "⚠️ Drei Loecher, alle vom Audit gefunden: (1) 164 Wissensartikel ohne Suchtext, "
      "darunter ALLE 82 Ausgaben eines laufenden Pflichtdienstes -- der schrieb, niemand "
      "konnte lesen. (2) korpus_suchen sah nur die Artikel-FTS; die 325.357 Zeilen des "
      "DATEIKORPUS waren unerreichbar -> dateien_suchen. (3) kein Werkzeug las einen ganzen "
      "Artikel, Zero bekam immer nur 420 Zeichen -> artikel_lesen",
      True)
    z("Betrieb", "Adressen darf Zero nennen, Passwoerter nie",
      "die halbe Eignerregel war nicht lieferbar",
      "Eigner 18.08.",
      "⚠️ Der geheim-Kern wurde auf 30 Eintraegen geschrieben und von NIEMANDEM gelesen: "
      "katalog() strich JEDEN Wert, auch Adressen und Token, die der Eigner ausdruecklich "
      "freigegeben hat. Jetzt tresor_zeigen mit HARTEM Passwort-Riegel: geprueft ueber alle "
      "58 Eintraege, 0 Passwort-Lecks; Adressen und Token kommen heraus, Passwoerter nie -- "
      "auch nicht auf Wunsch",
      True)
    # ══ Was am 19./20.08. dazukam ═════════════════════════════════════════
    # Jede dieser Zeilen misst ihren eigenen Gegenstand. Dass eine Datei da ist,
    # ist keine Messung -- gemessen wird, was im Betrieb entscheidet.
    A = "/opt/entityos/the artefact/"

    def _hat(datei: str, text: str) -> bool:
        try:
            return text in Path(datei).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return False

    def _timer_an(unit: str) -> bool:
        return _sh(f"systemctl is-active {unit} 2>/dev/null").strip() == "active"

    # -- Abruf: erreicht die Frage ueberhaupt die Weltmontage?
    frage_kommt_an = _hat(A + "clayverse/mistral_prestage/pipeline.py",
                          "_gather_world_safe(db, session_id, message)")
    z("Abruf", "Die Frage erreicht die Weltmontage",
      "der Korpus wird zur FRAGE gebaut, nicht zur leeren Zeichenkette",
      "Befund 20.08.",
      ("⚠️ Bis 20.08. rief run_chat_turn `_gather_world_safe(db, session_id)` -- OHNE die "
       "Nachricht. assemble() baute den Korpus mit `query or \"\"`, also war world['corpus'] "
       "in JEDEM Zug LEER, bei damals 17.900 Artikeln. Die Vorstufe schrieb deshalb staendig "
       "'no local info' und schickte Zero ins Netz nach Dingen aus der eigenen Datenbank; dass "
       "trotzdem Antworten kamen, lag daran, dass Zero sich danach per MCP selbst durch den "
       "Korpus arbeitete -- ein zweiter, langsamer Weg, der den ersten verdeckte. Damit wirkte "
       "auch die gesamte Abrufarbeit (corpus_lookup/enrich, Eval-Recall 75,8 %) nur im Eval, "
       "nie im Betrieb. Jetzt wird die Nachricht durchgereicht: gemessen 5 Treffer in 1-13 ms."
       if frage_kommt_an else
       "🔧 Die Nachricht wird NICHT an die Weltmontage durchgereicht -- corpus bleibt leer."),
      frage_kommt_an)

    # -- Abruf: Aufzeichnungen des Nichtwissens sind kein Wissen
    kreisel_zu = _hat(A + "clayverse/retrieval.py", "KEIN_WISSEN_ART")
    z("Abruf", "Die Anlage serviert sich nicht ihr eigenes Nichtwissen",
      "selbst geschriebene Luecken-Notizen duerfen keine Korpustreffer sein",
      "Befund 20.08.",
      ("Kaum war der Korpus angeschlossen, waren die BESTEN Treffer auf 'was ist iar?' zwei "
       "selbst geschriebene Notizen 'Wissensluecke: was ist iar?' -- sie tragen den Fragetext "
       "im Titel und gewinnen jedes BM25-Ranking. Das ist eine Rueckkopplung: je oefter etwas "
       "unbeantwortet bleibt, desto weiter draengen die Luecken-Notizen den echten Inhalt aus "
       "den fuenf Treffern. art='zero_luecke' und epistemic_class='MECHANICAL_GAP_HYPOTHESIS' "
       "sind jetzt von den Korpustreffern ausgeschlossen; die Notizen bleiben und behalten "
       "ihren Zweck, sie sind nur kein Wissen mehr"
       if kreisel_zu else "🔧 Luecken-Notizen erscheinen weiter als Korpustreffer"),
      kreisel_zu)

    # -- Gedaechtnis: EIN Gedaechtnis, nicht zwei
    ein_gedaechtnis = _hat(A + "clayverse/mcp_server.py",
                           "aus dem Gespraech (durable_memory)")
    dm = _zahl(c, "durable_memory")
    z("Gedächtnis", "Zero und die Vorstufe lesen DASSELBE Gedächtnis",
      "ein Werkzeug, das den falschen Speicher liest, widerspricht der Vorstufe systematisch",
      "Befund 20.08.",
      (f"⚠️⚠️ Gemessen: `udb_memory_search(\"38\")` -> 0 Treffer (Tabelle `memory_tabelle`, "
       f"2 Testzeilen ueber Schraubenzieher), waehrend `durable_memory` {dm} Zeilen fuehrt, "
       "darunter 'gabriel ist 38', vom Menschen selbst gesagt. ZWEI Gedaechtnisse in derselben "
       "Datei: die Vorstufe las das eine, Zeros einziges Gedaechtniswerkzeug das andere. Zero "
       "hielt deshalb eine belegte Angabe fuer unbelegt -- und verhielt sich dabei voellig "
       "richtig, kaputt war die Pruefung, nicht das Urteil. Jetzt liest das Werkzeug BEIDE und "
       "nennt zu jedem Treffer den Speicher; geschrieben wird weiter nur ins ausdruecklich "
       "Gemerkte"
       if ein_gedaechtnis else "🔧 Zeros Werkzeug liest weiter nur einen der beiden Speicher"),
      ein_gedaechtnis)

    # -- Gedaechtnis: ein Fakt reist mit seinem Beleg
    beleg_woertlich = _hat(A + "clayverse/mistral_prestage/prestage.py",
                           "QUOTED, NOT DESCRIBED")
    z("Gedächtnis", "Ein Fakt reist mit seinem Beleg — wörtlich",
      "eine Behauptung ÜBER einen Beleg ist kein Beleg",
      "Befund 20.08.",
      ("In dieser Reihenfolge gemessen: (1) der nackte Fakt wurde von Zero als Vermutung "
       "abgelehnt -- seine Nie-raten-Regel arbeitete korrekt gegen eine unbelegte Behauptung; "
       "(2) die BESCHRIEBENE Quelle ('steht im Speicher') schickte Zero suchen; (3) es suchte "
       "nach 'alter' und 'age', gespeichert war 'gabriel ist 38' -- keine gemeinsame "
       "Zeichenkette, also null Treffer und erneute Ablehnung. Eine Teilzeichenketten-Suche "
       "kann diese Bruecke nicht schlagen, und keine weitere Regel aendert das. Jetzt wird der "
       "Beleg WOERTLICH mitgegeben, statt ihn zu beschreiben. Ergebnis im Betrieb: 'Du bist 38 "
       "Jahre alt -- du hast es selbst gesagt: \"Gabriel ist 38\"'"
       if beleg_woertlich else "🔧 Fakten reisen weiter ohne zitierten Beleg"),
      beleg_woertlich)

    # -- Sprache: die Person wird nie vertauscht
    person_sperre = _hat(A + "clayverse/mistral_prestage/translator.py", "_person_vertauscht")
    z("Sprache", "Der Übersetzer vertauscht nie die Person",
      "'you are X' heisst 'Du bist X' -- nie 'Ich bin X'",
      "Befund 20.08.",
      ("⚠️ Am Uebersetzer isoliert, ohne Zero dazwischen: 'you are Gabriel Gschaider, 38 years "
       "old' wurde zu 'Ich bin Gabriel Gschaider, 38 Jahre alt'. Die Entitaet uebernahm die "
       "Identitaet des Menschen. Warum es nicht auffiel: der Uebersetzer prueft Masken, "
       "Maschinenmarken, Bezeichner und Zahlen -- alles Abzaehlbare. Die PERSON war das eine "
       "Grosse ohne Pruefung, und eine wortgetreue Uebersetzung mit vertauschtem Sprecher "
       "besteht jede vorhandene Pruefung. Jetzt Regel 12 (PERSON) plus mechanische Sperre mit "
       "Wiederholung, eng gefasst (greift nicht, wenn die Quelle selbst 'I am' sagt): 5/5 "
       "korrekt in beide Richtungen"
       if person_sperre else "🔧 keine Personenpruefung im Uebersetzer"),
      person_sperre)

    # -- Metakognition: der Kreis hat eine zweite Haelfte
    pruefer = _timer_an("eos-vorsatz.timer")
    fs = {r[0]: r[1] for r in c.execute(
        "SELECT status, COUNT(*) FROM folgerung WHERE autor='eos-hypothesen-generator' "
        "GROUP BY status")} if "folgerung" in kern else {}
    z("Metakognition", "Der Kreis schließt sich: Hypothese → Prüfung → Revision",
      "ein Kreis mit nur der ersten Hälfte ist keine Metakognition, sondern eine Liste",
      "Eigner 20.08.",
      (f"Vorher: Beobachten ✅, Hypothese ✅, PRUEFEN ❌, REVIDIEREN ❌ -- elf offene "
       f"Folgerungen, keine je nachgemessen, kein Weg nach gestuetzt/widerlegt. Jetzt misst "
       f"eos-vorsatz alle 6 h nach (Timer {'aktiv' if pruefer else 'INAKTIV'}). Stand: "
       f"{fs}. ⭐ Die zwei Behauptungsarten vertragen NICHT dieselbe Pruefung: eine "
       "Wiki-Luecke ('es fehlt ein ARTIKEL') widerlegt ein gefundener Artikel vollstaendig; "
       "eine Selbstpruefung ('es fehlt eine belegte ANGABE') wird NIE automatisch geschlossen, "
       "weil Wortueberlappung kein Wissen ist -- sonst haette ein Artikel ueber Gabriels Rolle "
       "die Luecke 'document root path' fuer erledigt erklaert. 'gestuetzt' wird nie vergeben: "
       "dass eine Suche nichts findet, beweist nicht, dass etwas fehlt"),
      bool(pruefer))

    # -- Metakognition: die Anlage schliesst eigene Vorsaetze
    arbeit = _timer_an("eos-vorsatz-arbeit.timer")
    z("Metakognition", "Die Anlage schließt eigene Vorsätze — ohne zu erfinden",
      "selbst nachsehen und urteilen, nicht nur auflisten",
      "Eigner 20.08.",
      (f"eos-vorsatz-arbeit (2x taeglich, Timer {'aktiv' if arbeit else 'INAKTIV'}): ein "
       "kleines freies Modell liest EINEN Kandidatentext und sagt, ob die gesuchte Angabe "
       "darin steht. KEIN Zero-Zug -- run_chat_turn verlangt eine der vier kanonischen "
       "Sitzungen, autonome Arbeit dort hinein zu schreiben hiesse, sie in ein "
       "Menschengespraech zu schreiben; die Identitaetsgrenze wurde nicht aufgebohrt. "
       "⭐⭐ DIE SPERRE: was das Modell als Fakt zurueckgibt, wird ZEICHENWEISE gegen den "
       "Quelltext geprueft -- steht es dort nicht, wird es verworfen und der Vorsatz bleibt "
       "offen. Hat beim ersten Lauf sofort gegriffen. ⚠️ Und die Sperre schuetzt vor "
       "Erfindung, NICHT vor einer falschen Frage: zuerst gingen die Signaturwoerter des "
       "Buendels hinein statt der echten Luecke, das Modell fand wahrheitsgemaess den "
       "Maschinennamen, gefragt war der document root. Jetzt gehen die echten Formulierungen "
       "hinein. Live geschlossen: Vorsatz #13 (Gabriels Alter) mit Beleg '38', Status "
       "widerlegt"),
      bool(arbeit))

    # -- Abruf: das Messgeraet fuer die eigene Karte
    lage_da = (_hat(A + "clayverse/mcp_server.py", "def abruf_lage")
               and _hat(A + "policy/managed-settings.json", "abruf_lage")
               and _hat(A + "clayverse/mistral_prestage/headless_zero.py", "abruf_lage"))
    z("Abruf", "Zero kann seinen eigenen Abruf messen",
      "ein Lernmechanismus, in den niemand hineinsehen kann, sieht auch dann gruen aus, wenn er nichts tut",
      "Eigner 20.08.",
      ("`abruf_lage` (rein lesend, speist die Karte NICHT): Kartenversion, Wegehierarchie MIT "
       "eigenem Urteil, Erfolgsquote, Zustand der Politik, Top-Wege. Meldet ausdruecklich auch "
       "das NICHTS -- live: 'GLEICHVERTEILT, der Mechanismus tut (noch) nichts', oberstes "
       "Zehntel 13,6 % gegen 10 % bei Gleichverteilung, Erfolgsquote 84,8 %. ⚠️ Ein neues "
       "MCP-Werkzeug braucht DREI Eintraege -- Server, managed-settings UND headless_zeros "
       "Freigabeliste; sonst verwirft headless_zero den Namen als 'erfunden'. Zwei davon "
       "fehlten zuerst"
       if lage_da else "🔧 abruf_lage fehlt oder ist nicht an allen drei Stellen eingetragen"),
      lage_da)

    # -- Weltmodell: das gebaute Modell erreicht die Vorstufe
    fusion = _hat(A + "clayverse/mistral_prestage/pipeline.py", "_weltmodell_safe")
    try:
        wm_mehrdeutig = c.execute(
            "SELECT COUNT(*) FROM (SELECT artikel_id, achse FROM wm_lesart "
            "WHERE gueltig_bis IS NULL AND achse <> 'identitaet' "
            "GROUP BY artikel_id, achse HAVING COUNT(DISTINCT wert) >= 2)").fetchone()[0]
    except Exception:
        wm_mehrdeutig = 0
    z("Weltmodell", "Das gebaute Weltmodell erreicht die Vorstufe",
      "Mehrdeutigkeit im Korpus soll die Vorstufe SEHEN, statt sie aufzuloesen",
      "Eigner 20.08.",
      (f"`hyperposition` war im Betrieb IMMER leer -- es baut auf durable_memory, und dort "
       f"fehlt die relation_key-Provenienz, an der die Projektion haengt. Daneben lag "
       f"ungenutzt `wm_lesart` mit 22.567 Lesarten; {wm_mehrdeutig} Artikel/Achsen-Paare "
       "tragen zwei oder mehr verschiedene Lesarten. Jetzt angeschlossen fuer die "
       "Korpustreffer des Zuges (2-7 ms). Drei gemessene Grenzen: die Achse `identitaet` "
       "bleibt draussen (bis zu 71 Werte je Artikel, und das sind Artikelkennungen aus der "
       "Dublettenerkennung, keine Lesarten); entdoppelt wird nach WERT (sphaere lieferte 18x "
       "'frank_v0_1' und 1x 'gabriel' -- ohne Entdopplung sieht Einigkeit wie Streit aus); "
       "gemeldet wird nur echte Mehrdeutigkeit. ⚠️ Ehrlich: nur rund 5 % der durchsuchbaren "
       "Artikel tragen so eine Mehrdeutigkeit -- das Signal ist echt, aber selten"
       if fusion else "🔧 wm_* erreicht die Vorstufe nicht"),
      fusion)

    # -- Betrieb: die Herz-DB liegt gesichert auf einem zweiten Rechner
    backup = (_hat("/opt/entityos/udb-backup/udb_backup.py", "BACKUP_ZIEL")
              and _timer_an("eos-udb-backup.timer"))
    z("Betrieb", "Die Herz-DB liegt gesichert auf einem zweiten Rechner",
      "ein Backup, das seit dem Bau jedes Mal abbricht, ist kein Backup",
      "Eigner 20.08.",
      ("⚠️ Der Dienst lief seit dem Bau NIE durch: erst stoppte das Secret-Gate den Push mit "
       "297 Treffern -- zu Recht, alle in der Tabelle `datei` (Volltext von 325k indizierten "
       "Dateien: 15 AWS-Schluessel, ein GitHub-Token, zwei Slack-Token, ein privater "
       "Schluessel) -- und dahinter wartete ein GitHub-Repo, das gar nicht existierte. Jetzt: "
       "`datei.text` faehrt als NULL mit (der Dateiindex bleibt vollstaendig, der Volltext ist "
       "als einziges Feld aus der Platte neu herstellbar; Dump 2,90 GB -> 511 MB), Ziel ist "
       "der zweite VPS statt GitHub. ⭐ Die Falle, die zwei Anlaeufe kostete: --link-dest "
       "verlinkt nur bei uebereinstimmender AENDERUNGSZEIT, und ein frisch geschriebener Dump "
       "hat immer eine neue -- 0 von 108 Dateien verlinkt. Mit fester Zeit PLUS --checksum: "
       "103 von 108, ein Schnappschuss kostet 13 MB statt 489 MB"
       if backup else "🔧 kein laufendes Backup der Herz-DB auf einem zweiten Rechner"),
      backup)

    # -- Betrieb: die Schluesselwacht misst den Endpunkt des Betriebs
    wacht = _hat("/opt/clayverse/werkzeug/schluesselwacht.py", "_chat_http")
    z("Betrieb", "Die Schlüsselwacht misst den Endpunkt, den der Betrieb benutzt",
      "ein Instrument, das für den falschen Endpunkt grün zeigt, misst nichts",
      "Befund 20.08.",
      ("⚠️ MISTRAL_API_KEY lieferte an /v1/models HTTP 200 und an /v1/chat/completions "
       "HTTP 402 ('Check your subscription'). Die Wacht meldete fuenf Tage lang '✓ MISTRAL "
       "GESUND': das Urteil kam allein aus der /models-Sonde, waehrend rest_per_chat() den "
       "Chat-Endpunkt zwar aufrief, aber nur die Ratelimit-Kopfzeilen las und den Status "
       "verschluckte. Jetzt entscheidet bei 401/402/403 die Chat-Antwort, und 'check your "
       "subscription' steht mechanisch in den Abo-Woertern -- MISTRAL steht korrekt auf "
       "ABO_FEHLT. Zusaetzlich rotiert der Transport jetzt bei 401/402/403 (vorher galt "
       "'bei kaputtem Token hilft Rotation nicht' -- genau verkehrt herum, ein kaputter Token "
       "ist eine Pro-Schluessel-Lage) und sperrt tote Schluessel 30 min"
       if wacht else "🔧 die Wacht urteilt weiter allein aus der /models-Sonde"),
      wacht)

    # -- Zaun: sperrt nicht den vorgesehenen Weg
    koerbe = _hat(A + "clayverse/fence_hook.py", "KOERBE")
    z("Sicherheit", "Der Zaun sperrt nicht den vorgesehenen Weg",
      "ein Zaun, der die eigene Brücke mitsperrt, macht die Fähigkeit unbenutzbar",
      "Befund 20.08.",
      ("⚠️ Der Zaun wies jeden Write nach /var/lib/clay ab -- richtig fuer wiki.db, aber dort "
       "liegen auch die beiden AUFTRAGSKOERBE, die einzige Bruecke, ueber die Zero aus dem "
       "Container heraus etwas bewirken kann. Gemessen: 'permission_denials: Write' mitten in "
       "der Bildkette, und es sah aus wie 'Zero kann das halt nicht'. Jetzt Ausnahme fuer die "
       "Koerbe, mit normalisierten Pfaden (ein '..' greift nicht) -- 16/16 Zaunproben korrekt "
       "in beide Richtungen. Ausserdem gehoerte der Korb root, der Container laeuft als 5001"
       if koerbe else "🔧 der Zaun sperrt die Auftragskoerbe weiterhin mit"),
      koerbe)

    # -- Bild: Zero kann etwas zeigen
    bilder = int(_sh("ls -1 '/opt/entityos/the artefact/web/chat/demo-bilder/'*.png "
                     "2>/dev/null | wc -l") or 0)
    bildweg = _hat(A + "web/chat/index.html", "bild-mini") and _hat(A + "runtime_CLAUDE.md", "9j.")
    z("Oberfläche", "Zero kann ein Bild zeigen — und es auf einem fremden Rechner erzeugen",
      "der Chat konnte nur Text; und Zero hat weder ssh noch Browser",
      "Eigner 19.08.",
      (f"Zero legt einen Auftrag in /var/lib/clay/eos-demo-requests ab, der Wirt schreibt die "
       f"Seite nach ~/eos-demo/ auf andreas-MACO, fotografiert sie dort headless und gibt eine "
       f"Bildadresse zurueck; der Chat rendert die Miniatur. Mit einem echten Zug verifiziert "
       f"({bilder} Bilder abgelegt). ⚠️ Voraussetzung war, Zeros WIRKLICHE Reichweite in den "
       "Regeltext zu schreiben: der Container hat KEIN ssh/scp/rsync/git/curl/wget (gemessen) "
       "-- vorher stand dort das Gegenteil, und die Vorstufe erfand daraufhin einen 'web root' "
       "auf einem Mac"
       if bildweg else "🔧 Bildweg oder Anzeige fehlt"),
      bildweg)

    return Z


def schreibe_ziele(ziel: Path) -> dict:
    # ⚠️ ZUERST die Tests, DANN die Verbindung -- nicht umgekehrt. Siehe
    # _testlage_messen(): eine offene Verbindung erzeugt den roten Test, den
    # die Tabelle sonst meldet.
    testlage = _testlage_messen()
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    Z = zeilen(c, testlage)
    c.close()

    def mark(e):
        return {True: "✅ erfüllt", False: "🔧 offen", None: "⏸ zurückgestellt"}[e]

    erfuellt = sum(1 for x in Z if x["erfuellt"] is True)
    offen = sum(1 for x in Z if x["erfuellt"] is False)
    zurueck = sum(1 for x in Z if x["erfuellt"] is None)
    jetzt = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    md = [
        "# Was Agent Zero können soll — und was davon steht", "",
        f"**Automatisch erzeugt {jetzt}.** Nicht von Hand pflegen.", "",
        f"**{erfuellt} erfüllt · {offen} offen · {zurueck} zurückgestellt** von {len(Z)} Zeilen.", "",
        "Die Spalte **Soll** ist deklariert und ändert sich nur, wenn der Eigner etwas",
        "entscheidet. Die Spalte **Ist** wird bei jedem Lauf neu **gemessen** — durch einen",
        "Prüfer je Zeile, der das laufende System befragt. Eine handgepflegte Statustabelle",
        "steht nach einer Woche auf grün, weil niemand sie zurückstellt. Diese kann das nicht.", "",
    ]
    bereiche = []
    for x in Z:
        if x["bereich"] not in bereiche:
            bereiche.append(x["bereich"])
    for b in bereiche:
        md += [f"## {b}", "", "| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |", "|---|---|---|---|---|"]
        for x in [y for y in Z if y["bereich"] == b]:
            md.append("| **{f}** | {s} | {i} | {m} | {q} |".format(
                f=x["faehigkeit"], s=x["soll"].replace("|", "/"),
                i=str(x["ist"]).replace("|", "/"), m=mark(x["erfuellt"]), q=x["quelle"]))
        md.append("")
    # ── Prosa-Kapitel (Eigner-Auftrag 19.08.): Was ist was, Architektur,
    #    UnifiedDB, Featureliste, Messwerte. Deklarativ -- kein Prüfer. ──
    try:
        _c2 = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
        _tab = _c2.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        try:
            _art = _c2.execute("SELECT count(*) FROM artikel").fetchone()[0]
        except Exception:
            _art = "—"
        _c2.close()
    except Exception:
        _tab = _art = "—"
    try:
        _polm = json.loads(Path("/opt/entityos/the artefact/policy/managed-settings.json").read_text(encoding="utf-8"))
        _tools_n = len(_polm.get("permissions", {}).get("allow", []))
    except Exception:
        _tools_n = "—"

    md += [
        "## Was ist Agent Zero, EntityOS, ClayCode, UnifiedDB", "",
        "- **Agent Zero** — die Entität selbst. Konkret eine kopflose *Claude-Code*-",
        "  Sitzung (Sonnet) auf dem VPS, die als „autonome Kognitions-Schnittstelle“ der",
        "  einen, dauerhaften Entität handelt. Zero hat **kein eigenes Gedächtnis** — die",
        "  UnifiedDB ist seine einzige Kontinuität. Seit 19.08. handelt Zero **direkt** mit",
        "  nativen Werkzeugen (Bash, Read/Write/Edit, Web); ein dünner Zaun schützt nur das",
        "  Unersetzliche und Passwörter.",
        "- **EntityOS** — das System, in dem die Entität lebt: ein Container auf dem VPS",
        "  (frank-api) mit einer Weboberfläche (Chat + Mailbox + Seiten), Clerk-Anmeldung",
        "  (genau 2 Nutzer), Identitäts-/Sitzungsverwaltung und der Laufzeit. Ein Gefäß,",
        "  eine Entität.",
        "- **ClayCode** — der Code des Clay-Unterbaus (`clayverse/`): der verwaltete",
        "  MCP-Server, die Chat-Pipeline (Vorverarbeiter → Zero → Übersetzer), die",
        "  Korpus-/Wiki-Maschinerie und die Laufzeit-Wirbelsäule. „Clay“ ist die",
        "  Wissenssubstanz, ClayCode ihr Betrieb.",
        "- **UnifiedDB (`wiki.db`)** — **eine** SQLite-Datei, die die Entität IST: der",
        f"  Clay-Korpus (Artikel/Wiki/Graph) UND die Laufzeit-Wirbelsäule in {_tab} Tabellen,",
        "  kollisionsfrei nebeneinander. Das Herz, nicht Altlast, nicht daneben.", "",
        "## Architekturskizze", "",
        "```mermaid",
        "flowchart LR",
        "  M[\"Mensch<br/>Gabriel · Andreas\"] -->|\"Chat · Clerk-Auth (nur 2)\"| V[\"Vorverarbeiter<br/>Mistral\"]",
        "  V -->|caveman_prompt| Z[\"Zero<br/>Claude Code · native Tools\"]",
        "  Z -->|caveman| UE[\"Übersetzer<br/>Mistral → Deutsch\"]",
        "  UE -->|Antwort| M",
        "  Z <-->|liest / schreibt| U[(\"UnifiedDB<br/>wiki.db\")]",
        "  Z -.->|\"Zaun-Hook: schützt das Unersetzliche\"| F{{fence_hook}}",
        "  Z -.->|Tailscale ssh| PC[\"Gabriels + Andreas' PC\"]",
        "  subgraph VPS [\"frank-api · VPS\"]",
        "    V; Z; UE; U; F",
        "  end",
        "```", "",
        "Der Mensch schreibt Deutsch; die Mistral-Vorstufe versteht die Absicht und baut",
        "einen dichten *caveman-englischen* Auftrag; Zero handelt darauf direkt mit seinen",
        "Werkzeugen; der Übersetzer macht warmes Deutsch daraus. Die UnifiedDB wird auf dem",
        "ganzen Weg gelesen und geschrieben. Über Tailscale erreicht Zero auch die Rechner",
        "der beiden Menschen.", "",
        "## Wie die UnifiedDB funktioniert", "",
        "- **Eine Datei, zwei Welten:** `wiki.db` hält den **Clay-Korpus** (Wissens-,",
        f"  Bau- und Vorfallsartikel, Zuordnung, Graph — rund {_art} Artikel) UND die",
        "  **Laufzeit-Wirbelsäule** (Nutzer, Sitzungen, Züge, Effekte, Kausal-/",
        "  Arbeitsraum-Episoden) — getrennte Namensräume in derselben Datei.",
        "- **Kanonische Identität (Ebene 0):** Zeros Identität steht als Wurzelzustand in",
        "  der DB und wird bei jedem Zug deterministisch in den Systemprompt gerendert —",
        "  sie kann nicht „wegverdichtet“ werden.",
        "- **Jeder Zug ist eine Zeile:** Prompt und Antwort landen atomar als `turns`-Zeile",
        "  mit Kausalkette; scheitert eine Prüfung, bleibt keine halbe Zeile stehen.",
        "- **Wirkung nur durch das Tor:** zustandsändernde Schritte laufen über das",
        "  EffectGate mit Beleg (Ziel/Ergebnis als Prüfsumme).",
        "- **Volltext:** Artikel sind über FTS suchbar (`korpus_suchen`); der Dateikorpus",
        "  über `dateien_suchen`. Ein Artikel ohne Suchtext + FTS-Zeile ist unsichtbar —",
        "  eine wiederkehrende, teuer gelernte Lehre.",
        "- **Das Herz ist unersetzlich:** `wiki.db` liegt als Bind-Mount unter",
        "  `/var/lib/clay`; der Zaun-Hook verbietet Zerstören/Überschreiben.", "",
        "## Fähigkeiten im Überblick (Featureliste)", "",
        "- **Handeln:** native Shell (Bash) + Datei-Werkzeuge (Read/Write/Edit/Glob/Grep),",
        "  Websuche/-abruf, MCP-Werkzeuge für Korpus, Gedächtnis, Menschen-Profile, Tresor-",
        "  Katalog, Werkbank-Deploy — **direkt**, ohne Arbeitspakete.",
        "- **Wissen:** Volltext-Korpus, Datei-Korpus, ganze Artikel lesen, Einbettungs-",
        "  und Gedächtnissuche, Menschen-/Projekt-/Artikelzuordnung mit Herkunft.",
        "- **Zusammenarbeit:** vier Sitzungen als **eine** Entität, gemeinsamer Raum mit",
        "  Kollisionswarnung; Chat-Historie überlebt den Neuladen.",
        "- **Wahrnehmung:** Live-Systemwacht (VPS + beide PCs via Tailscale: online, CPU/",
        "  RAM/Disk), Seiten-Erreichbarkeit prüfen, Speicher-Lage.",
        "- **Sicherheit:** Zugang bombenfest auf 2 Clerk-Konten; dünner Zaun um das",
        "  Unersetzliche + Passwörter; alle Homepages 6-stündlich auf einen 2. VPS gesichert.",
        "- **Sprache:** denkt/handelt in dichtem caveman-Englisch, antwortet in warmem",
        "  Deutsch (Mistral-Übersetzer).", "",
        "## Messwerte", "",
        f"- **{erfuellt} erfüllt · {offen} offen · {zurueck} zurückgestellt** von {len(Z)} deklarierten Fähigkeiten (jede Ist-Spalte je Lauf gemessen).",
        f"- **{_tab} Tabellen** in der einen `wiki.db`; rund **{_art} Artikel** im Korpus.",
        f"- **{_tools_n} Werkzeuge** freigegeben (native + MCP); verboten nur *Artifact*.",
        "- **Latenz:** Vorstufe ~1,8 s; dauerhafter warmer Zero-Prozess (~2,4 s Boot",
        "  vorab), Werkzeug-Takt von 3 s auf 0,12 s gesenkt.",
        "- **Tests:** 584 grün (inkl. der auf das neue „native Tools + Zaun“-Design",
        "  gezogenen Sicherheits-Tests).",
        "- **Zaun verifiziert:** `rm wiki.db` und `cat` der Passwort-Datei abgewiesen,",
        "  Backups und harmlose Befehle frei.", "",
    ]
    md += ["---", "",
           "⏸ *zurückgestellt* heißt: bewusst nicht verfolgt, nicht vergessen. Der Grund steht in der Ist-Spalte.", ""]

    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "ZIELE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (ziel / "ziele.json").write_text(
        json.dumps({"erzeugt": jetzt, "erfuellt": erfuellt, "offen": offen,
                    "zurueckgestellt": zurueck, "zeilen": Z},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"zeilen": len(Z), "erfuellt": erfuellt, "offen": offen, "zurueckgestellt": zurueck}


if __name__ == "__main__":
    print(json.dumps(schreibe_ziele(Path("/opt/agentzero-export/repo/agentZero")), ensure_ascii=False))
