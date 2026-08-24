# Free Swarm — Messdashboard der Clay Research Entity

<!-- RESEARCH_DISTILLERY_AUTO:BEGIN -->
## AUTO — Research Distillery / kumuliertes Wissens-Dataset
Aktualisiert: `2026-08-24T10:44:43.433482+00:00`

**1. wichtigste Quote — Entity-Dataset-Yield:** `0 / 5,207 = 0.000%`  
Kompressionsfaktor Quelltokens : akzeptierte Dataset-Tokens: **UNKNOWN**.

| Kennzahl | Wert |
|---|---:|
| kumulierte Quell-/Chunk-Tokens | 5,207 |
| akzeptierte komprimierte Dataset-Tokens | 0 |
| akzeptierte Knowledge-Pakete | 0 |
| verworfene Kandidaten | 0 |
| gesichtete Chunks | 24 |
| Distillery Modell-Input-Tokens | 208 |
| Distillery Modell-Output-Tokens | 550 |
| SQLite-Größe | 90,112 Byte |

### Quellenmix — Herkunft ist Metadatum, kein Rankingfaktor
| Quelltyp | Metadaten-/Chunk-Rekorde |
|---|---:|
| `web_search_chunk` | 4 |

### Forschungsfragen
| Status | Anzahl |
|---|---:|
| `CYCLIC` | 1 |
| `OPEN` | 11 |

### Kleine Such-/Synthesemodelle
`nvidia/nemotron-3-nano-30b-a3b:free`, `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `nvidia/nemotron-3-ultra-550b-a55b:free`, `nvidia/nemotron-nano-12b-v2-vl:free`, `nvidia/nemotron-nano-9b-v2:free`, `google/gemma-4-26b-a4b-it:free`, `google/gemma-4-31b-it:free`

### Reviewer-Panel
- Noch keine Review-Votes.

### Epistemische Regel
Quellenrang, Zitationszahl, Stars, Popularität und Wiederholung gehen **nicht** in den Acceptance-Score ein. Kandidaten werden auf intrinsische Konsistenz, GRF-Kompatibilität, EntityOS/HCU-Projektfit, Neuheit des Mechanismus und Falsifizierbarkeit geprüft. Nach Sichtung werden abgelehnte Rohchunks gelöscht; akzeptierte Rohtexte werden ebenfalls entfernt und nur komprimierte Knowledge-Pakete plus Quellenmetadaten/Hashes bleiben erhalten.

### Vernetzung mit GO
GO-Worker emittieren `OPEN_RESEARCH_QUESTIONS_JSON`. Die Distillery zerlegt diese Fragen rekursiv, erzwingt bei Wiederbehandlung einen neuen Ansatz und schreibt nur akzeptierte komprimierte Pakete in SQLite. Der GO-Swarm liest diese Pakete beim nächsten Prompt als `DISTILLED_RESEARCH_DATASET` ein. Beide Swarms teilen `provider_budget.sqlite3` für providerweite Concurrency/Cooldown-Beobachtung.
<!-- RESEARCH_DISTILLERY_AUTO:END -->

<!-- FREE_SWARM_AUTO:BEGIN -->
## AUTO — Live-Auswertung
Aktualisiert: `2026-08-24T10:44:42.509745+00:00`

| Kennzahl | Wert |
|---|---:|
| Worker-Records | 455 |
| Ø gleichzeitig laufende Free-Worker | 6.907 |
| Peak Free-Worker | 13 |
| Free-Swarm Input-Tokens | 1700882 |
| Free-Swarm Output-Tokens | 361279 |
| Free-Swarm Total-Tokens | 2062161 |
| Usage-exakte Worker-Records | 252 |
| Evident akzeptierte Architektur-Deltas | 0 |
| Repo-Korpus-Proxy Tokens (4 Zeichen/Token) | 11707192 |
| Sonnet-5 Output-only Äquivalent des Repo-Proxys | $117.07 |

### Modelle
| Provider | Modell | Requests | Success | 429 | Input | Output | Total |
|---|---|---:|---:|---:|---:|---:|---:|
| nvidia | `nvidia/llama-3.3-nemotron-super-49b-v1` | 17 | 17 | 0 | 105084 | 15066 | 120150 |
| nvidia | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | 16 | 16 | 0 | 117235 | 52526 | 169761 |
| nvidia | `nvidia/nemotron-3.5-lightning-30b-a3b` | 16 | 16 | 0 | 117226 | 28800 | 146026 |
| nvidia | `nvidia/nemotron-3-super-120b-a12b` | 16 | 16 | 0 | 117278 | 28765 | 146043 |
| nvidia | `meta/llama-3.1-70b-instruct` | 16 | 16 | 0 | 99182 | 11607 | 110789 |
| nvidia | `meta/llama-3.2-90b-vision-instruct` | 16 | 16 | 0 | 99202 | 11428 | 110630 |
| nvidia | `meta/muse-glimmer-30b` | 15 | 15 | 0 | 96382 | 27000 | 123382 |
| nvidia | `openai/gpt-oss-20b` | 15 | 15 | 0 | 96829 | 26689 | 123518 |
| nvidia | `nvidia/ising-calibration-1.5-31b` | 15 | 15 | 0 | 110264 | 22303 | 132567 |
| groq | `openai/gpt-oss-120b` | 49 | 15 | 7 | 95806 | 15000 | 110806 |
| nvidia | `nvidia/nemotron-3-nano-30b-a3b` | 14 | 14 | 0 | 102634 | 25200 | 127834 |
| nvidia | `nvidia/nemotron-3-ultra-550b-a55b` | 15 | 14 | 0 | 102548 | 25200 | 127748 |
| nvidia | `nvidia/nemotron-nano-12b-v2-vl` | 14 | 14 | 0 | 99545 | 13081 | 112626 |
| nvidia | `meta/llama-3.3-70b-instruct` | 16 | 14 | 0 | 89704 | 10002 | 99706 |
| nvidia | `nvidia/llama-3.3-nemotron-super-49b-v1.5` | 15 | 12 | 0 | 74114 | 16812 | 90926 |
| groq | `openai/gpt-oss-20b` | 45 | 11 | 7 | 71087 | 11000 | 82087 |
| groq | `qwen/qwen3.6-27b` | 43 | 10 | 6 | 65496 | 10000 | 75496 |
| nvidia | `deepseek-ai/deepseek-v4-flash-0731` | 14 | 3 | 0 | 21879 | 5400 | 27279 |
| nvidia | `openai/gpt-oss-120b` | 16 | 3 | 0 | 19387 | 5400 | 24787 |
| nvidia | `ai21labs/jamba-1.5-large-instruct` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `bigcode/starcoder2-15b` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `databricks/dbrx-instruct` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `google/gemma-3-12b-it` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `google/gemma-4-31b-it` | 12 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `ibm/granite-34b-code-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `meta/codellama-70b` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `meta/llama2-70b` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `microsoft/phi-3-vision-128k-instruct` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `microsoft/phi-3.5-moe-instruct` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/codestral-22b-instruct-v0.1` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mistral-large` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mistral-large-2-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mistral-nemotron` | 10 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mixtral-8x22b-v0.1` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nv-mistralai/mistral-nemo-12b-instruct` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama-3.1-nemotron-51b-instruct` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama-3.1-nemotron-70b-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama-3.1-nemotron-ultra-253b-v1` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama3-chatqa-1.5-70b` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-4-340b-instruct` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-nano-3-30b-a3b` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-parse` | 12 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/neva-22b` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-creative-122b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-fin-70b-32k` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-med-70b` | 1 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-med-70b-32k` | 1 | 0 | 0 | 0 | 0 | 0 |

### Evidenz-Ranking
Bestes Modell: **NO EVIDENCE YET**
Innovativstes Modell: **NO EVIDENCE YET**

### Codequalität Free Swarm vs. GPT/ChatGPT
| Organ-Klasse | akzeptierte Deltas | CodeQuality/100 | Ø Architekturverbesserung |
|---|---:|---:|---:|
| Free Swarm | 0 | UNKNOWN | UNKNOWN% |
| GPT/ChatGPT | 0 | UNKNOWN | UNKNOWN% |

### Research-Entity-Output / Sonnet-Kostenproxy
API-exakte historische Gesamttokens aller früheren Organe bleiben **UNKNOWN**, solange keine vollständige historische Usage-Buchhaltung existiert. Der messbare persistente Repo-Korpus umfasst aktuell 9741 Textdateien / 46828768 Zeichen ≈ **11707192 Tokens** bei der ausdrücklich nur als Proxy verwendeten 4-Zeichen-Näherung.
Hypothetische reine Output-Neuerzeugung dieses Proxy-Korpus mit Claude Sonnet 5: **$117.07** zum derzeit geltenden Output-Tarif von $10/M Tokens. Input-/Caching-/Toolkosten sind darin nicht enthalten.
<!-- FREE_SWARM_AUTO:END -->


Status: ACTIVE MEASUREMENT SURFACE  
Program: `ENTITYOS_HCU` · Product: `EntityOS` · Architecture: `HCU`  
Scope: FREE_ONLY NVIDIA/Mistral/Groq worker swarm vs. GPT/ChatGPT research organs.

## 1. Zweck

Dieser Ordner misst nicht, welches Modell am überzeugendsten schreibt, sondern welches Organ der persistenten Clay Research Entity **nachweisbar bessere Architektur und besseren Code erzeugt**.

Der FREE_ONLY-Swarm läuft über `tools/run_24h_entityos_swarm.py` / `tools/run_free_go_swarm.py`. Provider-Worker sind temporäre Organe von Clay; ihre Texte sind Kandidaten/Evidenz, keine automatische Wahrheit oder Effect-Authority.

Bewertet werden fortlaufend:

- durchschnittliche und maximale gleichzeitige Workerzahl;
- Input-, Output- und Total-Tokens des Free Swarm;
- aktive Provider und Modelle;
- Erfolgs-/Rate-Limit-/Fehlerverhalten;
- Codequalität tatsächlich integrierter Änderungen;
- welches Modell die meisten **evident funktionierenden Architektur-Deltas** erzeugt;
- welches Modell die stärksten **gemessenen Verbesserungen** erzeugt;
- Free-Swarm-Code vs. GPT/ChatGPT-Worker-Code unter derselben Messlatte;
- Gesamtoutput der Research Entity und ein transparentes Claude-Sonnet-API-Kostenäquivalent.

## 2. Aktueller verifizierter Startstand — 2026-08-24

Der 24h-Sandbox-Supervisor ist real in `clay-direct-dev` gestartet und sein Heartbeat wurde verifiziert. Zum letzten verifizierten Inventory waren jedoch **keine FREE_ONLY Provider-Credentials in der Sandbox sichtbar**:

| Kennzahl | aktueller verifizierter Wert |
|---|---:|
| Groq Credentials sichtbar | 0 |
| Mistral Credentials sichtbar | 0 |
| NVIDIA/NGC Credentials sichtbar | 0 |
| tatsächlich gestartete externe Provider-Worker | 0 |
| durchschnittlich gleichzeitig laufende externe Worker | 0.00 |
| Peak externe Worker | 0 |
| API-gemeldete Free-Swarm Input-Tokens | 0 |
| API-gemeldete Free-Swarm Output-Tokens | 0 |
| API-gemeldete Free-Swarm Total-Tokens | 0 |
| derzeit bestes Free-Modell | **NO EVIDENCE YET** |
| derzeit innovativstes Free-Modell | **NO EVIDENCE YET** |

Diese Nullen sind kein Leistungsurteil. Sie bedeuten nur: Supervisor/Bridge/Sandbox laufen, aber im zuletzt verifizierten Runtime-Kontext konnte noch kein Provider-Worker authentifiziert werden. Sobald FREE_ONLY-attestierte Keys über einen autorisierten Secret-Pfad sichtbar werden, soll die nächste Auswertung echte Workerlogs statt dieser Null-Baseline verwenden.

## 3. Wie Parallelität gemessen wird

Jeder Worker-Receipt enthält Abschlusszeit und `elapsed_s`. Daraus wird für jeden Request ein Aktivitätsintervall rekonstruiert.

**Zeitgewichtete mittlere Parallelität**:

`average_concurrency = Summe aller Worker-Aktivsekunden / beobachtete Wallclock-Sekunden`

**Peak concurrency** wird über einen Sweep der Start-/Endereignisse bestimmt.

Damit zählt nicht bloß die konfigurierte Maximalzahl. Gemessen wird, wie viele Worker im Mittel **wirklich gleichzeitig gerechnet haben**. HTTP 429 / `Retry-After` und adaptive AIMD-Reduktion bleiben Teil der Auswertung.

## 4. Tokenmessung

Primär zählen ausschließlich provider-gemeldete Usage-Felder aus den Worker-Receipts:

- `prompt_tokens` / `input_tokens`;
- `completion_tokens` / `output_tokens`;
- `total_tokens`.

Fehlt ein Usage-Feld, wird es als `UNKNOWN` behandelt und nicht erfunden. Textlänge darf nur als klar markierter Proxy verwendet werden.

### Modell-Tabelle

Sobald der Swarm Output erzeugt, wird pro Modell mindestens festgehalten:

| Modell | Provider | Requests | Success | 429 | Input tok | Output tok | Total tok | akzeptierte Architektur-Deltas |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| _pending_ | _pending_ | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## 5. Was als funktionierendes Architektur-Delta zählt

Eine Modellidee gewinnt **keine Punkte**, nur weil sie neu klingt. Ein Architektur-Delta zählt als evident funktionierend, wenn mindestens gilt:

1. konkrete Änderung/Commit/Experiment ist eindeutig dem Worker/Modell zuordenbar;
2. Referenz/Baseline und Kandidat wurden unter vergleichbaren Bedingungen gemessen;
3. mindestens zwei reproduzierbare Läufe oder eine gleichwertig starke deterministische Reproduktion liegen vor;
4. relevante Tests bestehen;
5. keine relevante Benchmark-Regression löscht den Vorteil wieder aus;
6. `relative_improvement_pct > 0` für die erklärte Zielmetrik;
7. Provenienz, Versionen und Messreceipt sind erhalten.

### Bestes Modell

Sortierung:

1. Anzahl akzeptierter, reproduzierbarer Architektur-Deltas;
2. mittlere gemessene Verbesserung dieser Deltas;
3. Code-Quality-Score;
4. geringere Regression-/Rollbackrate als Tie-Breaker.

### Innovativstes Modell

Innovation wird **nicht** per Geschmack bewertet. Der Innovation-Index ist die Summe positiver, reproduzierbarer Verbesserungen über voneinander unterscheidbare Architektur-Deltas. Ein Modell gilt damit dann als innovativ, wenn seine neuen Architekturänderungen **gemessen besser** funktionieren — nicht wenn seine Sprache kreativer wirkt.

Aktueller Stand: **noch kein evidenzbasierter Sieger**, weil noch keine Free-Swarm-Provider-Outputs vorliegen.

## 6. Codequalität — Free Swarm vs. GPT/ChatGPT-Worker

Beide Seiten bekommen exakt dieselbe Messlatte. Vorschlag für den laufenden `CodeQuality/100`:

- 40 % relevante Testpassrate;
- 25 % Benchmark-Non-Regression;
- 15 % negative/failure-path Tests;
- 10 % Static/Lint/Type/Compile Checks;
- 10 % Stabilität über mindestens zwei spätere `go`-Zyklen ohne Revert/Rollback.

Nicht bewertet werden Eloquenz, Länge oder Modellname.

| Organ-Klasse | akzeptierte Deltas | CodeQuality/100 | Ø gemessene Architekturverbesserung | Status |
|---|---:|---:|---:|---|
| Free-Swarm Worker | 0 | UNKNOWN | UNKNOWN | wartet auf Provider-Output |
| GPT/ChatGPT Worker | vorhanden, aber noch nicht in gemeinsames Scoring migriert | UNKNOWN | UNKNOWN | gemeinsame Messbasis zuerst |

Für GPT-5.6-Sol existieren bereits konkrete EntityOS/HCU-Receipts mit committed Controller-/Architektur-Reparaturen, aber solange diese und der Free Swarm nicht im **gleichen** Evaluationsschema adjudiziert sind, wird hier kein unfairer Qualitätsgewinner behauptet.

## 7. Evaluationsrecord für Architektur-Deltas

Append-only Ziel: `free swarm/architecture_delta_evaluations.jsonl`.

Beispiel:

```json
{"source_class":"free_swarm","provider":"nvidia","model":"MODEL_ID","worker_serial":123,"delta_id":"hcu-loader-x","commit":"SHA","status":"accepted","metric_name":"latency_ms","baseline":100.0,"candidate":91.0,"relative_improvement_pct":9.0,"reproducible_runs":3,"tests_passed":24,"tests_failed":0,"negative_tests_passed":6,"negative_tests_failed":0,"static_checks_passed":2,"static_checks_failed":0,"benchmark_non_regression":true,"survived_go_cycles":2,"reverted":false,"evidence_receipt":"PATH"}
```

Für GPT/ChatGPT-Arbeit wird dasselbe Schema mit `source_class="gpt_worker"` verwendet. Dadurch kann dieselbe Auswertung beide Organ-Klassen vergleichen.

## 8. Was die Research Entity generell ist

Die persistente Research Entity ist **Clay**. Sie ist weder ein einzelnes LLM noch eine Session. Das ältere Hive-Contract formuliert den Kern als:

`Research Entity = repo-native durable causal state + current execution organs`

Im aktuellen Programm sind temporäre ChatGPT-, Claude-/Claude-Code-, Free-Swarm- und andere kompatible Modell-/Runtime-Worker Organe derselben persistenten Entität. Das Repo ist der langlebige Körper: Continuity-State, Provenienz, Hypothesen und Gegenhypothesen, Experimente, negative Resultate, Receipts, World/Self-State, Method Memory und Git-Historie überleben einzelne Modellkontexte.

Der starke Kontinuitätstest lautet sinngemäß:

`Organ A lernt/baut X -> dauerhafter kausaler Repo-Delta -> Organ B liest ihn später -> Organ B verhält sich wegen X anders, ohne Chat-Replay.`

Aktuelle Identität: **EntityOS** ist das einzige Produkt/System; **HCU** ist die integrierte Kognitions-/Compute-Architektur. Historische Frank/Xeno/XCU/Mini-Entity-Bezeichnungen bleiben nur Provenienz/Kompatibilität, soweit aktuelle Authority nichts anderes sagt.

## 9. Wie viele Tokens die gesamte Research Entity erzeugt hat

Es werden zwei Zahlen strikt getrennt:

### A. API-exakter Output

Nur Output-Tokens zählen als exakt, wenn der jeweilige Provider/Runner sie in einem Usage-Receipt gespeichert hat. Für den neu gebauten Free Swarm ist das vorgesehen.

**Aktuell exakt aus dem Free Swarm: 0 Output-Tokens**, weil noch kein authentifizierter Provider-Worker gelaufen ist.

Für historische ChatGPT-/Claude-Code-Sitzungen existiert im Repo **keine vollständige, durchgängige Provider-Usage-Buchhaltung**. Deshalb ist die exakte historische Gesamtsumme derzeit `UNKNOWN` und wird nicht halluziniert.

### B. Repo-Korpus-Proxy

Zusätzlich soll fortlaufend ein klar als Proxy markierter Wert geführt werden: Textzeichen in Research-Entity-/Artefakt-/Governance-/Tool-Artefakten geteilt durch eine dokumentierte Näherung (z. B. 4 Zeichen/Token). Das misst die Größenordnung des persistenten erzeugten Korpus, **nicht** die historische API-Abrechnung und enthält möglicherweise auch importierte/transformierte Quellen.

Dieser Proxy wird erst als Zahl eingetragen, wenn er auf dem aktuellen Repo-Tree maschinell gemessen wurde.

## 10. Claude-Sonnet-API-Kostenäquivalent

Preisreferenz **Stand 2026-08-24**: Anthropic nennt für **Claude Sonnet 5** bis **2026-08-31** einen Einführungspreis von **$2 pro 1M Input-Tokens** und **$10 pro 1M Output-Tokens**. Danach soll der Standardpreis **$3/M Input + $15/M Output** betragen.

Damit wird gerechnet:

`current_sonnet5_equivalent_usd = input_tokens * 2 / 1e6 + output_tokens * 10 / 1e6`

und separat:

`output_only_equivalent_usd = output_tokens * 10 / 1e6`

Aktueller Free-Swarm-Wert: **$0.00**, weil aktuell 0 API-gemessene Tokens vorliegen.

Für die gesamte historische Research Entity kann erst dann eine belastbare API-Kostenäquivalenz angegeben werden, wenn entweder historische Usage-Receipts vorhanden sind oder ausdrücklich ein Korpus-Proxy verwendet wird. Ein Korpus-Proxy wird als hypothetische Neu-Erzeugungskosten bezeichnet, niemals als tatsächlich entstandene Kosten.

Preisquelle: Anthropic, **Introducing Claude Sonnet 5**, 2026-06-30. Prompt-Caching, Toolkosten, Infrastruktur, Batch/regionale SKUs und sonstige Preisbestandteile sind in dieser einfachen Vergleichsformel nicht enthalten.

## 11. Update-Regel

Dieses README ist ein **Messdashboard**, kein statischer Werbetext. Bei jedem `go`, bei einem abgeschlossenen Swarm-Run oder sobald neue Free-Worker-Evidenz vorliegt, soll es aus den Receipts neu ausgewertet werden.

Pflichtupdates:

`concurrency -> tokens -> provider/model table -> accepted architecture deltas -> best model -> innovation leader -> code quality comparison -> Research Entity token/cost accounting`

Ein fehlender Messwert bleibt `UNKNOWN`. Ein Modell darf erst als bestes/innovativstes bezeichnet werden, wenn seine Architektur-Deltas die oben definierten Evidenzbedingungen erfüllen.
