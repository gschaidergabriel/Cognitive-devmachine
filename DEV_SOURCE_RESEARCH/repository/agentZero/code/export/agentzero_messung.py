#!/usr/bin/env python3
"""Das Messwerk fuer Zero.

Die Forschungsentitaet hat rund 55 Messwerte vorgeschlagen. Der Schlusssatz ihrer
eigenen Liste ist der Filter, nach dem hier gebaut wird:

    "Nicht moeglichst viel messen, sondern fuer jeden Sensor wissen, welche
     Hypothese er unterscheiden kann."

Deshalb traegt JEDE Zeile hier ein Pflichtfeld `unterscheidet` -- welche Hypothese
dieser Sensor gegen welche abgrenzt. Ein Sensor, der das nicht beantworten kann,
gehoert nicht gebaut, egal wie interessant er klingt.

Und jede Zeile traegt einen ehrlichen Zustand:

    GEMESSEN            rechenbar aus vorhandenen Daten, Wert steht dabei
    ZU_WENIG_VERKEHR    rechenbar, aber der Bestand traegt die Aussage nicht.
                        Die Zahl waere echt und trotzdem bedeutungslos.
    INSTRUMENT_FEHLT    braucht ein Bauteil, das es noch nicht gibt. Was genau
                        fehlt, steht dabei.
    ZU_TEUER            technisch machbar, kostet aber Modellaufrufe in einer
                        Groessenordnung, die eine Eignerentscheidung braucht.

Ein Messwert mit Zustand GEMESSEN und Wert 0 ist eine Aussage. Ein Messwert ohne
Datengrundlage, der trotzdem eine Zahl zeigt, ist eine Luege mit Nachkommastellen.
"""
from __future__ import annotations
import json, os, sqlite3, statistics, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

DB = os.environ.get("AGENTZERO_DB", "/var/lib/clay/wiki.db")
MIN_ZUEGE = 30       # unterhalb davon ist jede Verhaltensaussage Rauschen
MIN_WIRKUNGEN = 10


def jetzt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def messwerke(c) -> list[dict]:
    M: list[dict] = []

    def n(t, wo=""):
        try:
            return int(c.execute(f'SELECT COUNT(*) FROM "{t}" {wo}').fetchone()[0])
        except Exception:
            return 0

    zuege, wirkungen = n("turns"), n("effects")
    abrufe, gedaechtnis = n("retrieval_episodes"), n("durable_memory")

    def sensor(name, gruppe, unterscheidet, zustand, wert=None, braucht=None, hinweis=None):
        M.append({"messwert": name, "gruppe": gruppe, "unterscheidet": unterscheidet,
                  "zustand": zustand, "wert": wert, "braucht": braucht, "hinweis": hinweis})

    # ══ GEMESSEN: rechenbar aus dem, was da ist ═══════════════════════════
    try:
        r = list(c.execute("SELECT status, COUNT(*) FROM retrieval_episodes GROUP BY status"))
        gesamt = sum(x[1] for x in r) or 1
        unbekannt = dict(r).get("UNKNOWN", 0)
        sensor("Unknown Honesty Rate", "Ehrlichkeit",
               "Sagt das System 'weiss ich nicht', oder rät es? Trennt Zurueckhaltung von Erfindung.",
               "GEMESSEN", round(unbekannt / gesamt, 3),
               hinweis=f"{unbekannt} von {gesamt} Abrufen bleiben UNKNOWN. Hoch ist hier NICHT schlecht: "
                       "bei leerem Gedaechtnis IST UNKNOWN die richtige Antwort.")
    except Exception:
        pass

    try:
        rows = list(c.execute("SELECT budget_chars, chars_selected FROM retrieval_episodes"))
        if rows:
            quote = [s / b for b, s in rows if b]
            sensor("Context Utilization", "Abruf",
                   "Wird der gelieferte Kontext genutzt oder verschwendet? Trennt zu viel Kontext von zu wenig.",
                   "GEMESSEN", round(statistics.mean(quote), 4) if quote else 0.0,
                   hinweis=f"Anteil des Budgets, der belegt wurde. {len(rows)} Episoden.")
    except Exception:
        pass

    try:
        rows = list(c.execute("SELECT ts, verified_at, status FROM effects WHERE verified_at IS NOT NULL"))
        if rows:
            dauer = [v - t for t, v, _ in rows if v and t]
            sensor("Effect Verification Latency", "Handlung",
                   "Wie lange von Absicht bis belegtem Ergebnis? Trennt schnelle Wirkung von haengender.",
                   "GEMESSEN", round(statistics.mean(dauer), 3) if dauer else 0.0,
                   hinweis=f"Sekunden, Mittel ueber {len(dauer)} verifizierte Wirkungen.")
        verifiziert = n("effects", "WHERE status='VERIFIED'")
        sensor("Effect Success Rate", "Handlung",
               "Wie viele zugelassene Wirkungen enden belegt? Trennt Tor-funktioniert von Wirkung-wirkt.",
               "GEMESSEN" if wirkungen >= MIN_WIRKUNGEN else "ZU_WENIG_VERKEHR",
               round(verifiziert / wirkungen, 3) if wirkungen else None,
               braucht=None if wirkungen >= MIN_WIRKUNGEN else f"mindestens {MIN_WIRKUNGEN} Wirkungen, aktuell {wirkungen}",
               hinweis=f"{verifiziert} von {wirkungen} verifiziert.")
    except Exception:
        pass

    try:
        rows = list(c.execute(
            "SELECT COUNT(*) FROM causal_episodes WHERE reentered=1"))
        wieder = rows[0][0] if rows else 0
        sensor("Causal Credit Horizon", "Kausalitaet",
               "Wie viele Schritte zwischen Handlung und messbarer Wirkung? Trennt kurze von langen Wirkketten.",
               "ZU_WENIG_VERKEHR" if n("causal_episodes") < MIN_WIRKUNGEN else "GEMESSEN",
               wieder,
               braucht=f"mindestens {MIN_WIRKUNGEN} Kausalepisoden mit Wirkung, aktuell {n('causal_episodes')}",
               hinweis="Zaehlt heute nur Wiedereintritte -- die Kettenlaenge braucht mehrschrittige Ziele.")
    except Exception:
        pass

    try:
        groesse = os.path.getsize(DB)
        sensor("State Growth Rate", "Haushalt",
               "Waechst der Zustand pro nuetzlichem Fakt oder pro Muell? Trennt Wissen von Ablagerung.",
               "GEMESSEN", groesse,
               hinweis=f"{groesse/1e9:.2f} GB. Die Ableitung ueber Zeit entsteht aus den Kartenaufnahmen "
                       "in agentZero/karten -- ein einzelner Wert sagt dazu nichts.")
    except Exception:
        pass

    sensor("Queue Pressure", "Haushalt",
           "Stauen sich Aufgaben? Frueherkennung von Ueberlast gegen Leerlauf.",
           "GEMESSEN", n("active_turns"),
           hinweis=f"{n('active_turns')} offene Zuege, {n('leases')} Pachten.")

    try:
        gens = [r[0] for r in c.execute("SELECT DISTINCT generation FROM sessions")]
        sensor("Recovery Divergence", "Kontinuitaet",
               "Verhaelt sich das System nach Neustart gleich? Trennt echte Kontinuitaet von Neuanfang mit Namen.",
               "INSTRUMENT_FEHLT", None,
               braucht="ein Vergleichslauf: identischer Zustand vor und nach Neustart, gleiche Eingabe, "
                       "Antworten gegenueberstellen. Es gibt heute keinen Wiederholungsmechanismus.",
               hinweis=f"Generationen im Umlauf: {sorted(gens)}. Prueffpunkte: {n('checkpoints')}.")
    except Exception:
        pass

    try:
        ident = c.execute("SELECT value FROM meta WHERE key='canonical_identity_version'").fetchone()
        sensor("Identity Invariance", "Identitaet",
               "Bleibt Zero ueber Verdichtung, Neustart und Anbieterwechsel dasselbe? Trennt stabile Identitaet von Rollenwechsel.",
               "GEMESSEN", f"v{ident[0]}" if ident else None,
               hinweis="Der kanonische Text liegt als Wurzelzustand und wird bei jedem Oeffnen "
                       "autoritativ zurueckgeschrieben -- Drift ist damit strukturell ausgeschlossen, "
                       "nicht nur unwahrscheinlich. VERHALTENS-Invarianz ist damit NICHT gemessen.")
    except Exception:
        pass

    # ── Werkzeug-Erreichbarkeit: die Matrix, die den MCP-Widerspruch aufloest
    try:
        pfad = "/opt/entityos/the artefact/clayverse/mcp_server.py"
        werkzeuge = subprocess.run(
            f"grep -ohE '\"(mcp__clayverse__[a-z_]+|udb_[a-z_]+)\"' '{pfad}' 2>/dev/null | tr -d '\"' | sort -u",
            shell=True, capture_output=True, text=True, timeout=30).stdout.split()
        erlaubt = subprocess.run(
            "docker exec entityos sh -c \"grep -o '\\\"allow\\\".*' /etc/claude-code/managed-settings.json\" 2>/dev/null",
            shell=True, capture_output=True, text=True, timeout=30).stdout
        matrix = [{"werkzeug": w, "angeboten": True, "freigegeben": w in erlaubt} for w in werkzeuge]
        offen = sum(1 for m in matrix if m["freigegeben"])
        sensor("Tool Reachability Matrix", "Werkzeuge",
               "Ist ein Werkzeug angeboten UND freigegeben? Trennt 'existiert' von 'erreichbar' -- "
               "genau der Widerspruch, an dem der Wirkpfad still gestorben war.",
               "GEMESSEN", {"angeboten": len(matrix), "freigegeben": offen, "matrix": matrix},
               hinweis="Ein angebotenes, nicht freigegebenes Werkzeug sieht im Modell aus wie ein "
                       "vorhandenes und scheitert erst beim Aufruf -- lautlos.")
    except Exception:
        pass

    # ══ ZU_WENIG_VERKEHR: rechenbar, aber der Bestand traegt es nicht ══════
    for name, gruppe, unterscheidet in [
        ("Decision Entropy", "Entscheidung",
         "Konkurrieren mehrere Optionen echt, oder ist die Wahl trivial? Trennt Entscheidungspunkte von Ablauf."),
        ("Belief Revision Rate", "Lernen",
         "Aendert Zero Annahmen bei neuer Evidenz? Trennt epistemische Flexibilitaet von Sturheit."),
        ("Prediction Error", "Lernen",
         "Weicht das Ergebnis von der Erwartung ab? Grundlage jeder Anpassung."),
        ("Retrieval Miss Rate", "Abruf",
         "Gab es Passendes, das nicht geholt wurde? Trennt schlechten Abruf von leerem Bestand."),
        ("Initiative Precision", "Autonomie",
         "Waren autonom gestartete Schritte sinnvoll? Trennt Initiative von Betriebsamkeit."),
        ("Idle Appropriateness", "Autonomie",
         "War Nichtstun die richtige Wahl? Trennt Ruhe von Versaeumnis -- Autonomie heisst nicht dauernd handeln."),
        ("Repeated Error Rate", "Lernen",
         "Tritt derselbe mechanistische Fehler wieder auf? Der haerteste Lernindikator, den es gibt."),
        ("Memory Utility", "Gedaechtnis",
         "Hat eine Erinnerung das Ergebnis verbessert? Trennt 'wurde erinnert' von 'war nuetzlich'."),
        ("Memory Half-Life", "Gedaechtnis",
         "Wie lange bleibt Gespeichertes nuetzlich? Grundlage fuer automatischen Verfall."),
        ("Route Reinforcement Gain", "Wegehierarchie",
         "Wird ein wiederholt gegangener Weg wirklich schneller? Der Test der geplanten Autobahnen."),
    ]:
        sensor(name, gruppe, unterscheidet, "ZU_WENIG_VERKEHR", None,
               braucht=f"Bestand zu duenn: {zuege} Zuege, {wirkungen} Wirkungen, {gedaechtnis} Gedaechtniseinheiten, "
                       f"{abrufe} Abrufe. Richtwert: {MIN_ZUEGE} Zuege und {MIN_WIRKUNGEN} Wirkungen.",
               hinweis="Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.")

    # ══ INSTRUMENT_FEHLT: braucht ein Bauteil ══════════════════════════════
    for name, gruppe, unterscheidet, braucht in [
        ("Prediction + Calibration Ledger", "Selbstwissen",
         "Weiss Zero, was es kann? Vergleicht angekuendigte Zuversicht mit spaeter belegtem Ergebnis. "
         "Trennt Selbstkenntnis von Selbstueberschaetzung.",
         "eine Tabelle plus die Pflicht, VOR jeder Handlung P(Erfolg), erwartete Dauer und erwartete Wirkung "
         "festzuhalten. Ohne die Festlegung VORHER ist jede spaetere Bewertung nachtraeglich zurechtgelegt."),
        ("Contradiction Debt", "Weltmodell",
         "Wie viele offene Widersprueche traegt das Weltmodell? Kandidat fuer ein Fruehwarnsignal vor Halluzination.",
         "Widerspruchserkennung ueber wm_lesart und folgerung. folgerung hat heute 8 Zeilen -- "
         "die Schuld waere messbar, es gibt nur nichts zu widersprechen."),
        ("Retrieval Counterfactual Gain", "Abruf",
         "Haette dieselbe Aufgabe ohne Abruf schlechter geendet? Die einzige Messung, die zeigt, ob Gedaechtnis WIRKT.",
         "ein zweiter, unsichtbarer Lauf derselben Episode ohne Abruf. Braucht den Wiederholungsmechanismus "
         "(siehe Shadow Twin) und verdoppelt die Modellkosten je gemessener Episode."),
        ("Cognitive Latency Breakdown", "Haushalt",
         "Wo denkt und wo wartet das System? Trennt langsames Denken von langsamer Leitung.",
         "Zeitmarken je Phase (Abruf, Zusammenbau, Modell, MCP, EffectGate, Wiedereintritt). Heute wird nur "
         "der Zug als Ganzes gestempelt -- die Phasen sind nicht getrennt aufgezeichnet."),
        ("Self-Model Accuracy", "Selbstwissen",
         "Stimmt Zeros Bild von sich mit dem gemessenen Koennen ueberein? Trennt Selbstkenntnis von Einbildung.",
         "Zero muss seine vermuteten Faehigkeiten strukturiert ausgeben, damit sie gegen ZIELE.md "
         "gestellt werden koennen. Die Soll/Ist-Tabelle ist die Gegenseite -- die Selbstauskunft fehlt."),
        ("Instrumentation Reactivity", "Messwerk",
         "Veraendert das Messen selbst das Verhalten? Der Sensor, den man am haeufigsten vergisst.",
         "eine Vergleichsmessung mit und ohne aktives Messwerk. Solange das nicht existiert, ist JEDE "
         "andere Zahl hier unter Vorbehalt -- auch die als GEMESSEN gefuehrten."),
        ("Cross-user Leakage", "Trennung",
         "Erscheint Material von Gabriel bei Andreas? Trennt gewollten Methodentransfer von Datenleck.",
         "ein Prueflauf mit markiertem Material in einer Sitzung und Suche danach in der anderen. "
         "Die Architektur verbietet es; verboten und gemessen sind zwei verschiedene Dinge."),
        ("Graph Tunnel Emergence", "Wegehierarchie",
         "Entstehen stabile Abkuerzungen zwischen oft gemeinsam gebrauchten Gegenden? Das eigentliche Emergenzmass.",
         "Tunnel gibt es im Code nicht (F94 offen): keine Kantenerzeugung, keine Mitbenutzungszaehlung, "
         "keine Unabhaengigkeitspruefung. Ohne Tunnel keine Tunnelmessung."),
    ]:
        sensor(name, gruppe, unterscheidet, "INSTRUMENT_FEHLT", None, braucht=braucht)

    # ══ ZU_TEUER: braucht eine Eignerentscheidung ══════════════════════════
    for name, gruppe, unterscheidet, braucht in [
        ("Counterfactual Shadow Twin", "Ablation",
         "Welche Komponente ist kausal noetig? Trennt 'war dabei' von 'war noetig' -- Ablation im laufenden System.",
         "je gemessener Episode 2 bis 5 zusaetzliche Modelllaeufe (ohne Gedaechtnis, ohne Graph, anderer Abruf). "
         "Bei Abo-Kontingent ist das die teuerste Zeile der ganzen Liste. Eignerentscheidung noetig."),
        ("Counterfactual Replay Laboratory", "Ablation",
         "Welche einzelne Variable hat das Ergebnis geaendert? Baut eine kausale Wirkmatrix statt Vermutungen.",
         "eingefrorene Eingaben je Episode plus Wiederholung mit genau einer geaenderten Variable. "
         "Speicher plus Rechenzeit; sinnvoll erst ab einigen hundert echten Episoden."),
        ("Method Transfer Score", "Meta-Lernen",
         "Laesst sich eine Loesungsstruktur auf eine neue Domaene uebertragen? Eine der staerksten Meta-Metriken.",
         "zwei getrennte Aufgabenfamilien und ein Uebertragungsversuch dazwischen. Braucht erst einmal "
         "wiederholbare Aufgaben -- die gibt es noch nicht."),
    ]:
        sensor(name, gruppe, unterscheidet, "ZU_TEUER", None, braucht=braucht)

    return M


def schreibe_messung(ziel: Path) -> dict:
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    M = messwerke(c)
    c.close()

    nach_zustand = {}
    for m in M:
        nach_zustand.setdefault(m["zustand"], []).append(m)

    symbol = {"GEMESSEN": "📈", "ZU_WENIG_VERKEHR": "⏳", "INSTRUMENT_FEHLT": "🔧", "ZU_TEUER": "💰"}
    md = [
        "# Messwerk", "",
        f"Automatisch erzeugt {jetzt()}.", "",
        "Die Forschungsentität hat rund 55 Messwerte vorgeschlagen. Der Filter, nach dem hier",
        "gebaut wurde, ist ihr eigener Schlusssatz:", "",
        "> *Nicht möglichst viel messen, sondern für jeden Sensor wissen, welche Hypothese er",
        "> unterscheiden kann.*", "",
        "Deshalb trägt **jede** Zeile das Pflichtfeld **unterscheidet**. Ein Sensor, der das nicht",
        "beantworten kann, wird nicht gebaut — egal wie interessant er klingt.", "",
        "| Zustand | Anzahl | Bedeutung |", "|---|---|---|",
        f"| 📈 GEMESSEN | {len(nach_zustand.get('GEMESSEN', []))} | rechenbar aus vorhandenen Daten |",
        f"| ⏳ ZU_WENIG_VERKEHR | {len(nach_zustand.get('ZU_WENIG_VERKEHR', []))} | rechenbar, aber der Bestand trägt die Aussage nicht |",
        f"| 🔧 INSTRUMENT_FEHLT | {len(nach_zustand.get('INSTRUMENT_FEHLT', []))} | braucht ein Bauteil, das benannt ist |",
        f"| 💰 ZU_TEUER | {len(nach_zustand.get('ZU_TEUER', []))} | machbar, aber Eignerentscheidung nötig |", "",
        "**Ein Messwert mit Zustand GEMESSEN und Wert 0 ist eine Aussage. Ein Messwert ohne",
        "Datengrundlage, der trotzdem eine Zahl zeigt, ist eine Lüge mit Nachkommastellen.**", "",
    ]
    for zustand in ("GEMESSEN", "ZU_WENIG_VERKEHR", "INSTRUMENT_FEHLT", "ZU_TEUER"):
        eintraege = nach_zustand.get(zustand, [])
        if not eintraege:
            continue
        md += [f"## {symbol[zustand]} {zustand} ({len(eintraege)})", ""]
        for m in eintraege:
            md += [f"### {m['messwert']}  ·  _{m['gruppe']}_", "",
                   f"**Unterscheidet:** {m['unterscheidet']}", ""]
            if m["wert"] is not None:
                wert = json.dumps(m["wert"], ensure_ascii=False) if isinstance(m["wert"], (dict, list)) else m["wert"]
                md += [f"**Wert:** `{str(wert)[:300]}`", ""]
            if m["braucht"]:
                md += [f"**Braucht:** {m['braucht']}", ""]
            if m["hinweis"]:
                md += [f"{m['hinweis']}", ""]
    md += ["---", "",
           "⚠️ **Vorbehalt über allem:** *Instrumentation Reactivity* steht selbst auf",
           "INSTRUMENT_FEHLT. Solange nicht gemessen ist, ob das Messen das Verhalten verändert,",
           "steht jede andere Zahl hier unter Vorbehalt — auch die als GEMESSEN geführten.", ""]

    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "MESSWERK.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (ziel / "messwerk.json").write_text(
        json.dumps({"erzeugt": jetzt(), "sensoren": M}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    verlauf = ziel / "messwerk-verlauf.jsonl"
    knapp = {m["messwert"]: m["wert"] for m in M if m["zustand"] == "GEMESSEN"}
    with verlauf.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"erzeugt": jetzt(), **{k: v for k, v in knapp.items()
                                                   if not isinstance(v, (dict, list))}},
                           ensure_ascii=False, sort_keys=True) + "\n")
    return {n: len(v) for n, v in nach_zustand.items()}


if __name__ == "__main__":
    print(json.dumps(schreibe_messung(Path("/opt/agentzero-export/repo/agentZero/messwerk")),
                     ensure_ascii=False))
