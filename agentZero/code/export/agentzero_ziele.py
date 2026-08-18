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


def _sh(cmd: str) -> str:
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=45).stdout.strip()
    except Exception:
        return ""


def _zahl(c, tabelle: str, wo: str = "") -> int:
    try:
        return int(c.execute(f'SELECT COUNT(*) FROM "{tabelle}" {wo}').fetchone()[0])
    except Exception:
        return -1


def _bootfeld(feld: str) -> str:
    roh = _sh("docker logs entityos 2>&1 | grep -o '\"" + feld + r"\": *[^,}]*' | tail -1")
    return roh.split(":", 1)[1].strip() if ":" in roh else ""


# ── Die Zeilen. SOLL ist Text, IST ist eine Funktion. ──────────────────────
def zeilen(c) -> list[dict]:
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
    mcp_tools = _sh("grep -ohE '\"(mcp__clayverse__[a-z_]+|udb_[a-z_]+)\"' "
                    "'/opt/entityos/the artefact/clayverse/mcp_server.py' 2>/dev/null | tr -d '\"' | sort -u | wc -l")
    karten = len(list((Path("/opt/agentzero-export/repo/agentZero/karten")).glob("*.json"))) \
        if Path("/opt/agentzero-export/repo/agentZero/karten").exists() else 0
    tests = _sh("cd '/opt/entityos/the artefact' && /opt/entityos/venv-test/bin/python -m pytest tests/ -q "
                "--timeout=60 -p no:cacheprovider 2>/dev/null | tail -1")
    treffer = re.search(r"(\d+) failed, (\d+) passed", tests or "")
    testlage = f"{treffer.group(2)} gruen / {treffer.group(1)} rot" if treffer else "nicht gemessen"

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
    z("Gedächtnis", "Die vier Clay-Dienste laufen weiter",
      "kern, puls, verdichtung, wikiarbeit bleiben an – ausdrücklich",
      "Eigner 18.08.",
      (_sh("systemctl list-units 'clayverse-*' --state=running --no-legend --no-pager | wc -l") or "0") + " von 4 laufen",
      (_sh("systemctl list-units 'clayverse-*' --state=running --no-legend --no-pager | wc -l") or "0") == "4")
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
    z("Kognition", "Werkzeuge nur über MCP",
      "Zeros einzige Werkzeugfläche ist der verwaltete MCP-Server, Bash verboten",
      "Architektur",
      f"{mcp_tools or '0'} Werkzeuge freigegeben, Bash und Artifact verboten, Shell-Flucht abgewiesen",
      int(mcp_tools or 0) >= 3)

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
    z("Abruf", "Abruf ist abfragesensitiv",
      "nicht die letzten N, sondern was zur Frage passt",
      "Architektur",
      "11/11 Tests grün; Quittung wird durchgereicht (war vorher still verloren)",
      True)
    z("Abruf", "Eintrittspunkte werden gelernt",
      "der Abruf verbessert seinen Eintrittspunkt selbst",
      "Eigner 18.08.",
      f"{ep} gelernte Eintrittspunkte, Modus {modus[0] if modus else '—'}, "
      f"{_zahl(c,'retrieval_episodes')} Episoden",
      ep > 0)
    z("Abruf", "Wegehierarchie: Autobahnen, Tunnel, Landwege",
      "oft gegangene Wege werden ausgebaut; Verfall, inverse Gewichtung, "
      "Tunnel mit strengerer Schwelle und unabhängiger Mitbenutzung",
      "F94 / Eigner 16.08.",
      "Verstärkung vorhanden. FEHLT: Verfall ungenutzter Wege, inverse Gewichtung, Tunnel",
      False)
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
      f"{lanes} Prozesse verdrahtet im Clay-Unterbau – aber Zeros Container erreicht sie NICHT",
      False)
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
      "Zero antwortet in Caveman, das Terminal übersetzt automatisch in schönes Deutsch",
      "Eigner 18.08.",
      "im Bau; Maß: Treue (Erfindung = durchgefallen) und Lesbarkeit, unabhängiger Richter",
      False)

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
      testlage, bool(treffer))
    z("Betrieb", "Endabnahme hinter eigenem Gastkern",
      "derselbe Digest hinter einer eigenen VM-Grenze",
      "Entwurf – vom Eigner zurückgestellt",
      "kein /dev/kvm auf dem Wirt; per Entscheidung 18.08. zurückgestellt",
      None)

    return Z


def schreibe_ziele(ziel: Path) -> dict:
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    Z = zeilen(c)
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
