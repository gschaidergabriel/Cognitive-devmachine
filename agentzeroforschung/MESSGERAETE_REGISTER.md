# Messgeraete-Register

Stand der Initialisierung: 2026-08-18.

Dieses Register wird bei jedem relevanten `go` gegen den neuesten `agentZero/MANIFEST.json`-Stand abgeglichen. Neue Datenquellen werden nicht stillschweigend interpretiert, sondern zuerst als Instrument beschrieben.

## Bereits beobachtete Instrumente / Datenkanaele

| Instrument/Datenfamilie | Messobjekt | Aktueller Exportcharakter | Bekannte Grenze / Forschungsfrage |
|---|---|---|---|
| `chat/session-*.jsonl` | Interaktionen pro Mensch | turnweise | ungleiche Stichprobengroesse; Andreas initial 0 Zeilen |
| `kognition/causal_episodes.jsonl` | Kausale Re-entry-Ketten | episodisch | kleine Stichprobe; semantische Ursache vs ID-Bindung trennen |
| `kognition/workspace_episodes.jsonl` | Workspace-Zustaende | episodisch | Auswahlmechanismus/Alternativen tiefer messen |
| `kognition/effects.jsonl` | EffectGate/Outcome | ereignisbasiert | initial nur 1 Effect; keine Generalisierung |
| `kognition/checkpoints.jsonl` | persistente Checkpoints | ereignisbasiert | Restart-/Recovery-Grenzen korrelieren |
| `kognition/active_turns.jsonl` | aktive Turns | Snapshot | 0 kann idle oder Messluecke bedeuten |
| `kognition/leases.jsonl` | aktive Leases | Snapshot | 0 kann idle oder Messluecke bedeuten |
| `abruf/retrieval_episodes.jsonl` | Retrieval-Ablauf | episodisch | initial 5 Episoden, geringe Power |
| `abruf/retrieval_entrypoint_policy.jsonl` | gelernte Entry-Points | policy state/events | initial 0; Aktivierungsbedingung klaeren |
| `abruf/retrieval_feedback.jsonl` | Retrieval-Lernsignal | ereignisbasiert | initial 0; Reward-/Outcome-Bindung pruefen |
| `abruf/retrieval_policy_state.jsonl` | Policy-Zustand | Snapshot | Drift ueber Generationen messen |
| `abruf/durable_memory.jsonl` | persistierte Memories | Snapshot/Events | initial 0; Semantik und Admission pruefen |
| `zustand/users.json` | kanonische Nutzer | Snapshot | Rechte-/Identity-Drift pruefen |
| `zustand/sessions.json` | Sessions/Generation | Snapshot | Fork-/Restart-/Stale-Writer-Indikator |
| `zustand/meta.json` | Wurzelzustand/Identitaet | Snapshot | Prompt-/State-Autoritaet getrennt analysieren |
| `zustand/graph_nodes.json` | Graphprojektion Knoten | Snapshot | Export ist Teilprojektion, nicht Vollgraph |
| `zustand/graph_edges.json` | Graphprojektion Kanten | Snapshot | initial leer trotz DB-Kanten; Projektion/Filter erklaeren |
| `karten/*.json` | persistente Snapshot-Karte | Zeitreihe | zentral fuer Laengsschnitt; Clock/Intervalle pruefen |
| `karten/*.meta.json` | Provenienz/Metadaten eines Snapshot-Artefakts | Sidecar | kann von naiven `*.json`-Zaehlern als Snapshot mitgezaehlt werden; Zweck/Zuordnung teils noch unbekannt |
| `puls/puls-letzte500.jsonl` | Autonomie-Puls | Rolling Tail | nur letzte 500; Langzeitstatistik braucht Aggregate |
| `puls/ereignisse-letzte500.jsonl` | Ereignisse | Rolling Tail | nur letzte 500; Zensierung beachten |
| `puls/tor-letzte500.jsonl` | Torentscheidungen | Rolling Tail | Dateiname sagt 500, Quelle kann kleiner sein; nicht automatisch aktuelles EffectGate |
| `wiki/kern.jsonl` | Zero-/EntityOS-Kernkorpus | Snapshot | 800 Artikel; Auswahlregel/Drift messen |
| `wiki/umfeld.jsonl` | semantisches Umfeld | Snapshot | 2635 Artikel; Grenzziehung/Leakage messen |
| `architektur/aenderungen.jsonl` | Code-/Architekturhistorie | kumulativ/exportiert | Systemaenderung ist Confounder fuer Verhaltenszeitreihen |
| `architektur/SKIZZE.md` | abgeleitete Laufzeitarchitektur | Snapshot | abgeleitete Beschreibung, kein unabhaengiges Instrument; Tool-Erreichbarkeit derzeit widerspruechlich zu Chatbeobachtung |
| `bauverlauf/bauverlauf.jsonl` / `BAUVERLAUF.md` | Bauinterventionen, Befunde, Reparaturgruende | kumulativ/exportiert | 700 Commits/4 Repos; Commit ist Interventionsevidenz, aber kein automatischer Wirksamkeitsbeweis |
| `tests/letzter-lauf.json` | aktueller deterministischer Teststatus | je Testlauf | 480 gruen/12 rot am gebundenen Stand; Test-PASS != beobachtetes Zero-Verhalten |
| `tests/verlauf.jsonl` | Teststatus ueber Zeit | wachsend, eine Zeile je Lauf | aktuell erst 1 Punkt; spaeter Change-Point-/Regression-Zeitreihe |
| `ZIELE.md` | Soll/Ist-Faehigkeitsinventar mit Messpruefern | Snapshot | Status ist capability-spezifisch, kein globaler Health-Score; Zaehler selbst auf Messfehler pruefen |
| `MANIFEST.json` | Export-Metrologie | Snapshot | zentrale Quelle fuer Zaehler, Hashes, Truncation |

## Automatische Aufnahme neuer Instrumente

Wenn eine neue Datei oder Datenfamilie in `agentZero/MANIFEST.json` erscheint, wird im naechsten `go` mindestens erfasst:

- Name/Pfad;
- vermutetes Messobjekt;
- tatsaechlich beobachtete Felder;
- Einheit/Skala;
- Sampling- bzw. Eventtrigger;
- Clock/Generation;
- Persistenz und Retention;
- Missing-/Null-Semantik;
- bekannte Filter/Redaktion/Truncation;
- moegliche Rueckwirkung des Instruments auf Zero;
- erster sinnvoller Falsifikator;
- Beziehung zu bereits vorhandenen Instrumenten.

## Prioritaet fuer weitere Messfaehigkeit

Nicht als Produktbau-Auftrag, sondern als Forschungsbedarf:

1. **Zeitbasis/Latenzen** — monotone Timestamps fuer Turnphasen, Retrieval, Workspace, EffectGate, Stop/Re-entry;
2. **Ressourcen** — CPU/RAM/IO/Queue/Context-Groesse pro Episode;
3. **Retrieval-Qualitaet** — Kandidaten, gewaehlte Seeds, Relevanz, Misses, spaetere Utility;
4. **Autonomie** — Zielquelle, Initiativegrund, next_runnable, Planrevision, Abbruchgrund;
5. **Workspace-Entropie** — angebotene Alternativen, Auswahl, Konfliktgrad, unresolved facets;
6. **Graph-Dynamik** — echte Delta-Knoten/-Kanten statt nur Projektion-Snapshot;
7. **Recovery** — Restart-ID, Pre/Post-Generation, offene Turns/Effects, UNKNOWN-Erhalt;
8. **Cross-user** — Collision-/Privacy-Indikatoren ohne Inhaltsleakage;
9. **Calibration** — Vorhersage/Confidence gegen spaeter verifiziertes Outcome;
10. **Method transfer** — wiederverwendete Analyse-/Loesungsstruktur gegen held-out Aufgaben.

Jede neue Instrumentierung muss ihren Informationsgewinn gegen Overhead, Reaktivitaet und Datenschutz abwaegen.
