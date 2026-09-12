# Free Swarm — Messdashboard der Clay Research Entity

<!-- EVIDENCE_FORGE_AUTO:BEGIN -->
## AUTO — Evidence Forge / dritter autonomer Swarm
Aktualisiert: `2026-08-25T14:46:02.839652+00:00`

Zweck: **Aktivität → ausführbarer Patch/Test → reproduzierbare Architektur-Evidenz**. Der Forge nutzt primär andere Kapazitäten als die LLM-Swarms: OpenAlex, Crossref, Semantic Scholar, Hugging Face Hub, GitHub, lokale Disposable-Clones und — innerhalb eines harten Free-Credit-Budgets — parallele E2B-Sandboxes.

| Kennzahl | Wert |
|---|---:|
| Discovery-Queries | 861 |
| Discovery-Hits | 4377 |
| Forge-Evaluierungen | 148 |
| evident akzeptierte Forge-Deltas | 1 |
| akzeptierte Deltas pro 1 Mio. Free-Swarm-Tokens | 0.025 |
| E2B-Reproduktionsjobs | 0 |
| E2B-PASS | 0 |
| E2B kumulierte Sandbox-Sekunden | 0.0 |
| gemessener Forge-Peak parallel | 0 |
| Forge SQLite | 5,918,720 Byte |

### Candidate-Zustände
| Zustand | Anzahl |
|---|---:|
| `NEW` | 403 |
| `PATCH_REJECTED` | 81 |
| `NEEDS_IMPLEMENTATION` | 65 |
| `ACCEPTED` | 1 |
| `VALIDATED_NOT_BETTER` | 1 |

### Zusätzliche Tool-Quellen
| Tool/Quelle | Hits |
|---|---:|
| `crossref` | 4280 |
| `openalex` | 65 |
| `github` | 21 |
| `semantic_scholar` | 11 |

### Zentral beobachtete Provider-/Tool-Limits
| Provider/Tool | Max inflight | aktiv | Requests | 200 | 429 | Fehler |
|---|---:|---:|---:|---:|---:|---:|
| `arxiv` | 1 | 0 | 4 | 2 | 0 | 0 |
| `crossref` | 1 | 0 | 863 | 858 | 5 | 0 |
| `exa` | 2 | 0 | 2 | 2 | 0 | 0 |
| `github` | 1 | 0 | 867 | 780 | 0 | 87 |
| `groq` | 128 | 0 | 167 | 109 | 58 | 26 |
| `huggingface_hub` | 4 | 0 | 863 | 863 | 0 | 0 |
| `nvidia` | 256 | 0 | 6743 | 5125 | 659 | 924 |
| `openalex` | 2 | 0 | 863 | 32 | 0 | 831 |
| `openrouter` | 16 | 0 | 1414 | 134 | 1279 | 0 |
| `semantic_scholar` | 1 | 0 | 674 | 36 | 638 | 187 |
| `tavily` | 2 | 0 | 6 | 6 | 0 | 0 |

### Produktivitätsdiagnose
- Free-Swarm-Tokenzähler sind **kumuliert über die vorhandenen Worker-Artefakte**, nicht 'aktuell aktive Credentials'. Dadurch ist die frühere Null-Baseline kein Widerspruch mehr, sondern eine historische Startmessung.
- Distillery Entity-Dataset-Yield: **0.000%**.
- Forge Architecture-Conversion: **0.025 akzeptierte Deltas / 1 Mio. Free-Swarm-Tokens**.
- Ein Forge-Delta zählt erst als `accepted`, wenn Patch/Test in einem Disposable-Clone mindestens zweimal reproduziert, negative/static checks bestanden und ein positiver Baseline-Unterschied oder Benchmarkvorteil gemessen wurde.
<!-- EVIDENCE_FORGE_AUTO:END -->

<!-- RESEARCH_DISTILLERY_AUTO:BEGIN -->
## AUTO — Research Distillery / kumuliertes Wissens-Dataset
Aktualisiert: `2026-09-12T13:44:57.093783+00:00`

**1. wichtigste Quote — Entity-Dataset-Yield:** `0 / 88,774 = 0.000%`  
Kompressionsfaktor Quelltokens : akzeptierte Dataset-Tokens: **UNKNOWN**.

| Kennzahl | Wert |
|---|---:|
| kumulierte Quell-/Chunk-Tokens | 88,774 |
| akzeptierte komprimierte Dataset-Tokens | 0 |
| akzeptierte Knowledge-Pakete | 0 |
| verworfene Kandidaten | 0 |
| Near-Miss-Kandidaten | 0 |
| Reviewer-underfilled | 0 |
| klare Review-Rejects | 0 |
| gesichtete Chunks | 275 |
| Distillery Modell-Input-Tokens | 6,116 |
| Distillery Modell-Output-Tokens | 23,481 |
| SQLite-Größe | 1,069,056 Byte |

### Candidate-/Gate-Diagnose
| Zustand | Anzahl |
|---|---:|
| — | 0 |

**Aktueller Hauptengpass:** Es wurden Quellen gesammelt, aber noch keine Candidate-Review-Stufe erreicht. Das ist ein Pipeline-/Runtime-Signal, kein Qualitätsurteil über die Quellen.

### Quellenmix — Herkunft ist Metadatum, kein Rankingfaktor
| Quelltyp | Metadaten-/Chunk-Rekorde |
|---|---:|
| `web_search_chunk` | 8 |

### Forschungsfragen
| Status | Anzahl |
|---|---:|
| `CYCLIC` | 851 |
| `OPEN` | 73 |

### Kleine Such-/Synthesemodelle
`google/gemma-4-26b-a4b-it:free`, `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`, `liquid/lfm-2.5-2.6b:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `google/gemma-4-31b-it:free`, `nvidia/nemotron-3-ultra-550b-a55b:free`, `cohere/north-mini-code:free`, `dots-studio/dots-3-note-preview:free`

### Reviewer-Panel
- Noch keine Review-Votes.

### Epistemische Regel
Quellenrang, Zitationszahl, Stars, Popularität und Wiederholung gehen **nicht** in den Acceptance-Score ein. Kandidaten werden auf intrinsische Konsistenz, GRF-Kompatibilität, EntityOS/HCU-Projektfit, Neuheit des Mechanismus und Falsifizierbarkeit geprüft. `Near-Miss` senkt keine Schwelle; es macht nur sichtbar, *wo* das Gate greift.

### Vernetzung mit GO
GO-Worker emittieren `OPEN_RESEARCH_QUESTIONS_JSON`; die Distillery zerlegt Fragen rekursiv und speist akzeptierte komprimierte Pakete als `DISTILLED_RESEARCH_DATASET` zurück. Shared `provider_budget.sqlite3` koordiniert Limits mit Free Swarm und Evidence Forge.
<!-- RESEARCH_DISTILLERY_AUTO:END -->

<!-- SYSTEM_ANALYSIS_AUTO:BEGIN -->
## AUTO — Gesamtsystem, GO-Fluss, Script-Auswertung und Sonnet-Vergleich
Aktualisiert: `2026-09-12T13:44:57.807417+00:00`

### 1. Wichtigster Effizienzindikator — was geht im Durchschnitt wieder an `go`?
**Source → GO Pass-through: 0.000%.** Definition: `accepted dataset-token yield × average distinct accepted-packet coverage delivered to GO macrocycles`.
Distillery-Yield: **0.000%** (0/88,774 Tokens). Reinjection-Coverage: **UNKNOWN** über 0 gemessene GO-Zyklen.
Aus 5555 erfolgreichen historischen GO-Workeroutputs über **397 rekonstruierte 12-Rollen-Makrozyklen** enthalten 551 maschinenlesbare Deltas (9.919%) und 148 forge-ready Deltas (2.664%); Ø pro Makrozyklus: Deltaquote 8.115%, forge-ready 0.852%.
Bei 0 akzeptierten Dataset-Tokens ist Source→GO exakt 0%; fehlende Reinjection-Receipts bleiben zusätzlich UNKNOWN statt erfunden.

### 2. Was `go` auslöst
1. Sandbox/Bridge/Storage-Preflight; Defekte zuerst reparieren.
2. Aktuellen `main`-/Supervisor-/Authority-State lesen.
3. GO-Rollen erzeugen Falsifier, Patches, Tests, Benchmarks, Deltas und offene Fragen.
4. Distillery zerlegt Fragen, sammelt Quellenmechanismen, filtert und komprimiert.
5. Evidence Forge reproduziert Repos/Deltas in Disposable-Clones/Sandboxes und misst.
6. Akzeptiertes Wissen wird in spätere GO-Kontexte reinjiziert; verifizierte Deltas gehen ins gemeinsame Ledger.
7. Dashboard berechnet Funnel, Qualität, Modelle, Kosten, Pass-through und Fortschritt neu.

### 3. Script-by-Script — live
| Subsystem | Funktion | Runtime | Messbarer Stand |
|---|---|---|---|
| **24h Supervisor** `run_24h_entityos_swarm_supervisor.sh` | hält lokale/public Lanes am Leben, quarantänisiert externe LLMs ohne typed FREE admission | STOPPED/QUARANTINED | policy `FREE_ONLY; CREDENTIAL_BLIND_CONTROL_PARENT; SWARM_CHILD_ONLY_SECRET_SCOPE; CURRENT_CANONICAL_PROVIDER_ADMISSION; NO_PAID_FALLBACK; TOGETHER_FORBIDDEN` |
| **GO Free Swarm** `run_24h_entityos_swarm.py` + `run_free_go_swarm.py` | parallele Architektur-/Code-/Falsifikationsorgane | RUNNING | 13571 Records; Ø 3.65, Peak 136; 39,932,437 Tokens; 551 Delta-Records |
| **Research Distillery** `run_research_distillery_local.py` / `run_research_distillery_entry.py` | Quellen + offene Fragen → komprimierte Knowledge-Pakete | RUNNING | 88,774 Quelltokens → 0; Yield 0.000%; OPEN 73, CYCLIC 851 |
| **Evidence Forge** `run_free_evidence_forge.py` | Suche → Repo/Patch → Test/Benchmark → Evidenz | RUNNING | **861 Queries / 4377 Hits**; 148 Evaluations; 1 akzeptierte Deltas |
| **Local 4B lane** `local_research_model_server.sh` | providerunabhängige lokale Synthese/Vorfilterung | NOT_READY | Ready wird nur per Loopback-Health bestätigt; Build ≠ Runtime-PASS |
| **Shared quota gate** `free_swarm_quota.py` | gemeinsame Concurrency/Cooldown-/429-Koordination | EMBEDDED | 11 beobachtete Provider/Tool-Lanes |
| **Dashboard** `evaluate.py` + `update_distillery_readme.py` + `update_system_analysis.py` | autonome Messung + README-Publikation | RUNNING | dieses Dashboard wird aus Receipts/SQLite/Runtime neu erzeugt |

### 4. Woran die Research Entity gerade arbeitet
- EntityOS/HCU executable architecture and causal receipts
- typed entry → loader consumption → actual model execution → inference/J-Space/training provenance
- ClayCode compiler/VM/runtime and minimal native deltas
- Global J-Space/GWT, memory, replay, online learning and model switching
- synthetic cognition interventions with matched controls
- runtime bottlenecks, benchmarks, negative paths and recovery semantics
- external GitHub/arXiv/web mechanism harvesting and reproduction
- truth/effect/capability boundaries and falsification

**Top offene Forschungsfragen aus der laufenden Queue:**
- Does GWT latency affect convergence via coalition formation delay or via degraded workspace content fidelity?
- How does the concurrency limit of Nvidia affect the overall system performance?
- How to cryptographically distinguish sibling experiments without time/organ name inference?
- What is the exact NVIDIA API endpoint or header that authoritatively exposes per-credential free-tier quota status without consuming inference quota?
- What minimal trigger key set enables quarantine enforcement across all provider lanes?
- Does current local J-Space instrumentation satisfy causal trace reconstruction requirements?
- How can we reliably measure output similarity across models with differing tokenization schemes?
- What minimal model size is needed for synthetic cognition to outperform controls under current sandbox quotas?
- Can error signature clustering distinguish between transient provider degradation and systematic credential/route binding failures without ground truth labels?
- Which open-source inference gateway implements per-credential free-tier quota enforcement with pre-call economic receipts (not post-hoc logging)?

### 5. Fortschritts-Funnel
| Stufe | Wert |
|---|---:|
| erfolgreiche GO-Workeroutputs | 5555 |
| davon Research-Question-Emitter | 1005 (18.092%) |
| maschinenlesbare Architektur-Deltas | 551 (9.919%) |
| forge-ready Deltas | 148 (2.664%) |
| Distillery Quelltokens | 88,774 |
| akzeptierte Dataset-Tokens | 0 (0.000%) |
| Forge Discovery-Hits | 4,377 |
| Forge Evaluations | 148 |
| Forge akzeptierte Deltas | 1 |
| gemeinsames Ledger akzeptiert | 0 |

### 6. Free Swarm vs. GPT/ChatGPT vs. Claude Sonnet — gleiche Messlatte
| Organ | akzeptierte Deltas | CodeQuality/100 | Ø Architekturverbesserung |
|---|---:|---:|---:|
| Free Swarm | 0 | UNKNOWN | UNKNOWN% |
| GPT/ChatGPT | 0 | UNKNOWN | UNKNOWN% |
| Claude Sonnet | 0 | UNKNOWN | UNKNOWN% |

**Kein Qualitätsgewinner ohne matched Receipts.** Eloquenz oder Modellname zählen nicht; nur Patch/Test/Benchmark/Non-Regression im gemeinsamen Delta-Schema.

### 7. Claude-Sonnet-5 Kostenäquivalent / nominal vermiedene Kosten
Preisannahme: **Claude Sonnet 5 standard: $3/M input + $15/M output**.
| Vergleich | Tokenbasis | Sonnet-5 Äquivalent |
|---|---:|---:|
| Free-Swarm Usage | 31,313,649 input + 8,618,788 output | **$223.22** |
| Distillery Modellarbeit | 6,116 input + 23,481 output | **$0.3706** |
| zusammen, gemessener LLM-Tokenmix | — | **$223.59** |
| persistenter Repo-Korpus, Output-only Proxy | 30,843,863 Proxy-Tokens | **$462.66** |

**Nominal vermiedene Sonnet-Kosten, falls diese Calls tatsächlich $0 kosteten: $223.59. Verifiziert gespart: UNKNOWN.** Die aktuelle typed Authority verbietet die nachträgliche FREE-Klassifikation historischer Provider-Traffic; der Korpuswert ist ebenfalls nur ein Neu-Erzeugungsproxy.

### 8. Kapazität vs. 15 parallele Sonnet-Worker
Slotvergleich: Ø **3.65/15 = 24.3%**, Peak **136/15 = 906.7%**. Gemessener Free-Swarm Outputdurchsatz: **139.53 Output-Tokens/s**. Das ist kein Qualitäts- oder Sonnet-Durchsatzbenchmark.

### 9. Autonome Update-Regel
Dieser komplette Block ist Pflichtbestandteil des Publishers. Kompakte Tabellen dürfen ihn nicht mehr verdrängen. GO-Pass-through, alle Scripts, Forschungsfragen, Funnel, matched Qualitätsvergleich und Sonnet-Kosten werden fortlaufend neu berechnet.
<!-- SYSTEM_ANALYSIS_AUTO:END -->

<!-- FREE_SWARM_AUTO:BEGIN -->
## AUTO — Live-Auswertung
Aktualisiert: `2026-09-12T13:44:55.573250+00:00`

| Kennzahl | Wert |
|---|---:|
| Worker-Records | 13571 |
| Ø gleichzeitig laufende Free-Worker | 3.646 |
| Peak Free-Worker | 136 |
| Free-Swarm Input-Tokens | 31313649 |
| Free-Swarm Output-Tokens | 8618788 |
| Free-Swarm Total-Tokens | 39932437 |
| Usage-exakte Worker-Records | 5555 |
| Evident akzeptierte Architektur-Deltas | 0 |
| Nominal/historisch akzeptierte Architektur-Deltas | 1 |
| Legacy/unqualifizierte nominale Accepts | 1 |
| Repo-Korpus-Proxy Tokens (4 Zeichen/Token) | 30843863 |
| Sonnet-5 Output-only Äquivalent des Repo-Proxys | $462.66 |

### Modelle
| Provider | Modell | Requests | Success | 429 | Input | Output | Total |
|---|---|---:|---:|---:|---:|---:|---:|
| nvidia | `nvidia/nemotron-3-super-120b-a12b` | 4535 | 3437 | 642 | 19276633 | 5500155 | 24776788 |
| nvidia | `nvidia/nemotron-3-ultra-550b-a55b` | 1700 | 1072 | 5 | 6058286 | 1673107 | 7731393 |
| openrouter | `openrouter/free` | 288 | 115 | 113 | 640932 | 224021 | 864953 |
| nvidia | `nvidia/nemotron-3.5-lightning-30b-a3b` | 425 | 71 | 0 | 448462 | 118400 | 566862 |
| nvidia | `nvidia/ising-calibration-1.5-31b` | 423 | 69 | 0 | 438535 | 58573 | 497108 |
| nvidia | `openai/gpt-oss-20b` | 422 | 68 | 0 | 372013 | 112050 | 484063 |
| nvidia | `meta/muse-glimmer-30b` | 421 | 66 | 0 | 358268 | 110000 | 468268 |
| nvidia | `nvidia/nemotron-3-nano-30b-a3b` | 420 | 66 | 0 | 416286 | 108849 | 525135 |
| nvidia | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | 425 | 65 | 0 | 412270 | 225125 | 637395 |
| nvidia | `meta/llama-3.1-70b-instruct` | 425 | 65 | 1 | 347612 | 45806 | 393418 |
| nvidia | `meta/llama-3.3-70b-instruct` | 426 | 63 | 0 | 342225 | 47137 | 389362 |
| nvidia | `nvidia/llama-3.3-nemotron-super-49b-v1` | 428 | 59 | 0 | 318232 | 56593 | 374825 |
| nvidia | `meta/llama-3.2-90b-vision-instruct` | 425 | 59 | 0 | 317884 | 41664 | 359548 |
| nvidia | `nvidia/nemotron-nano-12b-v2-vl` | 420 | 55 | 0 | 341519 | 44763 | 386282 |
| nvidia | `nvidia/llama-3.3-nemotron-super-49b-v1.5` | 422 | 52 | 0 | 274588 | 73485 | 348073 |
| groq | `openai/gpt-oss-20b` | 207 | 49 | 38 | 260360 | 46536 | 306896 |
| groq | `openai/gpt-oss-120b` | 190 | 46 | 22 | 251469 | 44189 | 295658 |
| groq | `qwen/qwen3.6-27b` | 186 | 46 | 18 | 252813 | 43700 | 296513 |
| nvidia | `openai/gpt-oss-120b` | 414 | 15 | 0 | 82352 | 25193 | 107545 |
| nvidia | `deepseek-ai/deepseek-v4-flash-0731` | 392 | 11 | 0 | 67409 | 14571 | 81980 |
| nvidia | `mistralai/mistral-nemotron` | 56 | 6 | 0 | 35501 | 4871 | 40372 |
| nvidia | `ai21labs/jamba-1.5-large-instruct` | 4 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `bigcode/starcoder2-15b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `databricks/dbrx-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `google/gemma-3-12b-it` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `google/gemma-4-31b-it` | 20 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `ibm/granite-34b-code-instruct` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `meta/codellama-70b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `meta/llama2-70b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `microsoft/phi-3-vision-128k-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `microsoft/phi-3.5-moe-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/codestral-22b-instruct-v0.1` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mistral-large` | 5 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mistral-large-2-instruct` | 4 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mixtral-8x22b-v0.1` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nv-mistralai/mistral-nemo-12b-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama-3.1-nemotron-51b-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama-3.1-nemotron-70b-instruct` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama-3.1-nemotron-ultra-253b-v1` | 4 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama3-chatqa-1.5-70b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-4-340b-instruct` | 5 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-mini-4b-instruct` | 417 | 0 | 11 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-nano-3-30b-a3b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-parse` | 18 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/neva-22b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-creative-122b` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-fin-70b-32k` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-med-70b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-med-70b-32k` | 2 | 0 | 0 | 0 | 0 | 0 |

### Evidenz-Ranking
Bestes Modell: **NO EVIDENCE YET**
Innovativstes Modell: **NO EVIDENCE YET**

### Codequalität Free Swarm vs. GPT/ChatGPT
| Organ-Klasse | akzeptierte Deltas | CodeQuality/100 | Ø Architekturverbesserung |
|---|---:|---:|---:|
| Free Swarm | 0 | UNKNOWN | UNKNOWN% |
| GPT/ChatGPT | 0 | UNKNOWN | UNKNOWN% |

### Research-Entity-Output / Sonnet-Kostenproxy
API-exakte historische Gesamttokens aller früheren Organe bleiben **UNKNOWN**, solange keine vollständige historische Usage-Buchhaltung existiert. Der messbare persistente Repo-Korpus umfasst aktuell 11969 Textdateien / 123375453 Zeichen ≈ **30843863 Tokens** bei der ausdrücklich nur als Proxy verwendeten 4-Zeichen-Näherung.
Hypothetische reine Output-Neuerzeugung dieses Proxy-Korpus mit Claude Sonnet 5: **$462.66** zum derzeit geltenden Output-Tarif von $15/M Tokens. Input-/Caching-/Toolkosten sind darin nicht enthalten.
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

## 2. Historischer initialer Startstand — 2026-08-24 (nicht aktueller Runtime-Stand)

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
