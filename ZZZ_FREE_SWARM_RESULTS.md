# ZZZ — FREE SWARM RESULTS / LIVE INDEX

**Diese Datei liegt absichtlich als `ZZZ_...` im Repository-Root, damit sie in der normalen GitHub-Dateiliste von `main` ganz unten bei den Textdokumenten leicht auffindbar ist.**

## Wo sind die Ergebnisse?

| Gesucht | Datei auf `main` | Zweck |
|---|---|---|
| **komplettes Live-Dashboard** | [`000_FREE_SWARM_LIVE_DASHBOARD.md`](./000_FREE_SWARM_LIVE_DASHBOARD.md) | automatisch publizierter Vollbericht: Swarm, Distillery, Forge, GO, Sonnet-Vergleich, Kosten |
| **kanonischer Free-Swarm-Bericht** | [`free swarm/README.md`](./free%20swarm/README.md) | detaillierte Auswertung und historische/live Trennung |
| **Live Token-/Modellmetriken** | [`free swarm/LIVE_METRICS.json`](./free%20swarm/LIVE_METRICS.json) | Worker, Modelle, Tokens, echte gemessene Parallelität |
| **GO-/Systemanalyse** | [`free swarm/SYSTEM_ANALYSIS_LIVE.json`](./free%20swarm/SYSTEM_ANALYSIS_LIVE.json) | GO-Funnel, Runtime, Source→GO, Sonnet-Kostenvergleich |
| **Distillery** | [`free swarm/DISTILLERY_LIVE.json`](./free%20swarm/DISTILLERY_LIVE.json) | Quellen, Forschungsfragen, Dataset-Yield, Knowledge-Pakete |
| **Evidence Forge** | [`free swarm/FORGE_LIVE.json`](./free%20swarm/FORGE_LIVE.json) | Discovery → Reproduktion → Test/Benchmark → akzeptierte Deltas |
| **Delta-Ledger** | [`free swarm/architecture_delta_evaluations.jsonl`](./free%20swarm/architecture_delta_evaluations.jsonl) | gemeinsame Evidenzlatte für Free/GPT/Sonnet |

## Letzter beim Anlegen dieser Indexdatei belegter Snapshot

Zeitpunkt des zugrunde liegenden Dashboards: **2026-08-24 12:43 UTC**.

- Worker-Records: **722**
- usage-exakte erfolgreiche GO-Outputs: **422**
- kumulierte Free-Swarm-Tokens: **3,240,266**
- historische gemessene Parallelität: **Ø 3.580**, Peak **14**
- maschinenlesbare Architektur-Deltas: **1**
- forge-ready Deltas: **0**
- Distillery: **11,621 Quelltokens → 0 akzeptierte Dataset-Tokens**
- Evidence Forge: **142 Queries / 705 Discovery-Hits / 0 Evaluations / 0 akzeptierte Deltas**
- nominales Claude-Sonnet-5-Äquivalent des gemessenen LLM-Tokenmixes: **ca. $11.23**; verifiziert gespart bleibt getrennt davon `UNKNOWN`.

## Neue Parallelitätsarchitektur

`tools/run_6000_free_swarm.py` ist jetzt die **Global-Work-Stealing-v2-Fabric**:

1. **6000 logische Forschungsorgane** liegen in einer gemeinsamen Queue statt dauerhaft an einen Provider gebunden zu sein.
2. Jeder aktuell freie, FREE-admitted Provider kann den nächsten Shard übernehmen. Ein Groq-Cooldown blockiert daher nicht mehr Arbeit, die NVIDIA/Mistral/OpenRouter übernehmen kann.
3. NVIDIA startet bei historisch gesunder Lane mit einem höheren Probe-Target; 429 halbiert weiterhin automatisch die Concurrency.
4. Gesunde Lanes rampen wesentlich schneller hoch als im alten `+1 nach 2×target Erfolgen`-AIMD.
5. Der OpenRouter-GO-Pfad ist auf **`openrouter/free`** beschränkt; kein Paid-Fallback.
6. Der zentrale HTTP-Threadpool ist für die Fabric auf **512** angehoben; die tatsächliche externe Concurrency bleibt durch Provider-Wahrheit, Shared Quota, 429/402 und Ressourcen begrenzt.
7. Jeder Output bleibt problem-/rollen-/mechanismus-geshardet und muss auf ausführbare Deltas/Falsifier statt redundante Essays optimieren.

### Arbeitsverteilung

Die GO-Arbeit rotiert weiterhin über zwölf Funktionen: `ARCHITECT`, `FALSIFIER`, `CLAYCODE_FORGE`, `HCU_CAUSAL`, `COGNITION`, `MEMORY_JSPACE`, `RUNTIME`, `EXTERNAL_HARVEST`, `EXPERIMENT_DESIGN`, `SECURITY`, `REVIEWER`, `SYNTHESIZER`. Zusätzlich wird jeder Call auf eine offene Distillery-Frage bzw. einen grundlegenden Forschungs-Shard gelegt; Wiederholungen bekommen eine neue Mechanismusvariante.

## Wichtig

Diese `ZZZ_...`-Datei ist der **stabile Finder/Index**. Für aktuelle Zahlen immer zuerst [`000_FREE_SWARM_LIVE_DASHBOARD.md`](./000_FREE_SWARM_LIVE_DASHBOARD.md) öffnen; genau diese Datei wird vom bestehenden autonomen Metrics-Publisher laufend aktualisiert.
