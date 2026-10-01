# Research-Entity Swarm-Koordination vs. needle-tasks (read-only Analyse)

Quelle: ~/needle-mouth/cgre_clone_readonly @ main 24e7d89c (nur main lokal; die Branches
chatgpt-vps-*/chatgpt-local-* sind NICHT im Clone -> Inhalte UNBELEGT). Pfade relativ zum Clone.
Stand der Repo-Selbstauskunft: viel Doku/Contracts, wenig nachgewiesene Laufzeit (siehe 5).

## 1. Wie die Koordination wirklich funktioniert

Kernidee: GitHub ist der Bus. Alles ist Datei + Commit + create-only/CAS-Push. Kein Server, kein Broker.
Es gibt KEINEN permanenten Chef (`global/AUTONOMOUS_SWARM_COORDINATION_DIRECTIVE.clay`:
"law NO_PERMANENT_CHIEF=true", "law DUPLICATE_WORK_REQUIRES_EXPLICIT_REPLICATION=true",
"law EVIDENCE_OUTRANKS_COORDINATION_ROLE=true"). Jeder Worker trifft eine lokale Dispatch-Entscheidung.

### 1.1 Aufgaben publizieren / beanspruchen (vier Schichten, alt -> neu)
| Mechanismus | Pfad | Kern |
|---|---|---|
| Rooms + Role/Task-Leases | `rooms/ROOM_REGISTRY.json`, `tools/research_room.py` | Lease-Datei `rooms/rooms/<room>/leases/{roles,tasks}/<role>.json`, `create_json_exclusive()` (atomar), `expires_at`; Lease aktiv nur wenn `status==ACTIVE` und `expires_at>now`; abgelaufene werden per Uebernahme geschrieben mit `supersedes_holder`. `active_workers(stale_minutes=45)` = Heartbeat-Staleness. |
| Work-Events | `global/CLAY_WORK_EVENT_PROTOCOL.clay`, `state/work/events/` | Append-only Events `WORK_CREATE/REVISE/DEFER/CANCEL/WORK_EXECUTION_RECEIPT` mit `spec_rev`, `write_scope`, `dependencies`, `invalidators`, `required_capabilities`, `executor_policy`. Regel: "Claude_before_effect -> verify event/current spec_rev has not changed". Projektionen (`CURRENT_DYNAMIC_WORK.clay`) sind abgeleitet, "projection_is_derived_not_authority". |
| Atomare Create-only-Claims | `continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md`, `continuity/go_experiment_claims/<trigger_key>.json` | Pro User-Trigger EIN Slot: byte-identischer Pfad aus `trigger_key` (`rid_<sha256>` oder `ts_<UTC>__p_<sha256>`); "Create-only semantics are mandatory. Never overwrite or delete an existing claim". Kein reproduzierbarer Key => `COORDINATION_BLOCKED` (fail-closed). |
| Dispatch-Idempotenz | `continuity/ORDINARY_DISPATCH_IDEMPOTENCY_PROTOCOL.md`, `continuity/ordinary_dispatch_specs/<class>.json`, `ordinary_dispatch_claims/<class>-g0001.json` | Schluessel = `<dispatch_class>-g<retry_generation>`; enthaelt NIE Zeit/Worker/Issue/Branch. Claim existiert => `ORDINARY_DISPATCH_ALREADY_CLAIMED`, kein zweiter Trigger. Generation steigt nur nach Terminalergebnis. Workflow lehnt Events ohne `dispatch_schema: CLAY_ORDINARY_DISPATCH/v1` + aktuellen Key + vorhandenen Claim ab. |
| Zustellung/ACK | `coordination/live_reentry_delivery_atomicity.py` | `route_id=sha256(run_id,receiver,message_kind,decision,payload_digest)`; States `PENDING -> CLAIMED -> DELIVERED_ACK_PENDING`, `UNKNOWN_DELIVERY` (fail-closed, Recovery nur per CAS). |
| Mailbox-Entwurf (nur Design!) | `coordination/T7_TARGETED_WORKER_COORDINATION_RESEARCH_DELTA_2026-08-31_GPT56SOL.md` | `ARCHITECT_COORDINATION_PACKET/v1`: `packet_id, route_id, target_type(WORKER/CLAIM/WORKPACKAGE/COHORT), target_generation, target_claim_id, expires_at, nonce, payload_digest, requested_action_class(ACK_ONLY/STATUS/REVIEW/FALSIFY/COORDINATE/RESEARCH), no_mutation_authority:true`. BUILD absichtlich NICHT erlaubt. ACK = "gesehen+klassifiziert", nicht "befolgt"; Reject-Gruende EXPIRED/TARGET_MISMATCH/STALE_GENERATION/DUPLICATE/...; Broadcast darf keine N Duplikat-Dispatches erzeugen. Selbst-Status: "NOT YET EXECUTABLY PROVEN". |
| Single-Spawn/Busy-Lease | `global/FRANK_V0_1_SINGLE_SPAWN_GLOBAL_BUSY_LEASE_DIRECTIVE.clay` | EIN globales Lease (`lease_epoch` monoton, `heartbeat_at_utc`, `lease_until_utc`), alle anderen sehen BUSY; keine versteckte Queue. |

### 1.2 Navigation / Supervisor / Receipts
- Supervisor: `claycode/autonomous/SUPERVISOR_INBOX.json` (Felder u.a. `latest_cycle, needs_review, current_frontier, steering, next_focus, promotion_state`) verweist per `steering` auf EINE Steering-Datei. Das ist Lenkung, keine Queue. Lesereihenfolge steht in `AGENTS.md` (CLAY_EXECUTION_AUTHORITY -> SUPERVISOR_INBOX -> Steering -> 00_CURRENT/NOW.md -> ...).
- `00_CURRENT/{NOW.md,INDEX.tsv,ACTIVE.tsv,RECENT.tsv,latest/<direction>.md}`: generierter Cache (Spalten ACTIVE.tsv: `kind direction ref status headline`). "Cache only", nie Autoritaet. Nie von Hand editieren.
- Pflicht-Receipt pro Material-Ergebnis: `python3 tools/clay_current_emit_v1.py --direction --status --headline --evidence ... --organ` -> append-only `CLAY_FAST_RESULT/v1` ("cannot mint truth, runtime credit ...").
- Execution-Requests: `execution_requests/<datum>_<ID>.json`, Schema z.B. `GO_FREE_SWARM_RUNTIME_QUIESCENCE_ENFORCER_REQUEST/v1` mit `source_pin.commit` (exakter SHA), `required_execution[]`, `pass_conditions{}`. = Auftrag an einen Runner/Bridge, an Commit gepinnt.
- Topic-Packets: `topic_packets/<id>/PACKET.json` (`packet_id,title,status,summary,key_distinction,open_questions`) = Wissenskapseln, KEINE Tasks (Beispiel claim-lifecycle: Status CURRENT/OPEN/SUPERSEDED/REFUTED/NEGATIVE_RESULT/CONTEXT_ONLY, append-only).
- Trigger-Run-Berichte: `trigger_runs/<trigger>/<run_id>/*.json` mit `actor, canonical_parent{revision,state_hash}, hypothesis, strongest_counterhypothesis, identity_boundary`.

### 1.3 Akteur-Identitaet / Gewicht
`global/RESEARCH_ACTOR_REGISTRY.json` v2.2: Akteure `claude-code-lead`, `chatgpt-secondary`, (Owner `user-gabriel`) als "temporary organs of Clay", je `role`, `authority_scope[]`, `decision_weight` (beide 1.0 in der Datei), `may_override_empirical_evidence:false`, `must_record_provenance:true`. Wahrheitsordnung (`global/CLAY_SYSTEM_WORK_FABRIC.clay` truth_order): verifizierte Realitaet > frische Primaerquelle > verifizierter lokaler Ausfuehrungsbeleg > Remote-Effekt-Receipt > kanonischer State > Evidenz > Projektion > Modelloutput. Meinung/Mehrheit praegt keine Wahrheit.
Maschinen-Attribution (`coordination/LOCAL_BRIDGE_PROTOCOL.md`): jedes Kommando/Receipt traegt `machine_id`+`owner` im Payload, NICHT nur Branch-Name (Vorfall: Daemon ohne Env-Vars fuehrte 26 fremde Kommandos aus und ueberschrieb Receipts; Fix per git revert).

### 1.4 Trigger-Woerter und ihre Vertraege
Regel (`triggers/MASTER_RESEARCH_TRIGGER_PROTOCOL.md`): Trigger feuert nur, wenn die GANZE getrimmte Nachricht (case-insensitive) exakt dem Wort entspricht; Menge in `global/RESEARCH_TRIGGER_REGISTRY.json`. Jeder Trigger = "Linse" auf dasselbe Ziel, mit Pflicht-Boot (Identitaet+Hash pruefen, Directives, Claims/Receipts lesen, Duplikate meiden, Hypothese+Gegenhypothese+Falsifier).
- `go` (`triggers/GO_AUTODISPATCH_PROTOCOL.md`, `GO_RECURSIVE_SWARM_CYCLE_PROTOCOL.md`): "go -> inspect center -> choose room -> choose role -> claim task -> act -> test -> publish"; dispatch_value-Formel (stage_criticality + blocker_reduction + info_gain ... - overlap - stale_basis - context_cost). Pro go-Makrozyklus genau EIN unueblicher Versuch (create-only Lease oben).
- `777` (`coordination/OMEGA_777_TRIGGER_CONTRACT.md`): Refresh Repo-Heads -> Authoritaet -> Claims/Leases/Receipts lesen -> Subjekte binden (owner+machine_id) -> hoechstes NICHT-DUPLIKAT-Gate waehlen -> ausfuehren -> Readback -> re-resolve, bis echter Blocker. Kein neuer Watcher/Loop/State.
- `FRED` (`coordination/OMEGA_FRED_TRIGGER_CONTRACT.md`): 777 + Maximalaufwand + Pflicht "complete Harness body" (Constitution-Dateien laden).
- `999`: Realtime/Sprach-Manifestation (`coordination/TRIGGER_999_CONTRACT.json`), eigener Pfad, nicht 777.
- weitere: `spawn` (gewichtete Zufallsziehung des Forschungsfelds, `global/SPAWN_RESEARCH_WEIGHTS.json`), `1` (10 parallele Lanes, `continuity/TRIGGER_ONE_JSPACE_STEERING_CONTRACT.md`), `zero`, `666`, Domain-Trigger (gwt, claygraph, harness, ...). Nummerierte "Trigger2/4/6/7" sind Arbeitsstraenge/Issues im Repo, keine Wort-Trigger. "triggerwort2" als Wort: NICHT im Repo gefunden (grep leer) -> UNBELEGT.
Nach dem Trigger gibt es keinen Rollenvertrag pro Worker-Index; die Rolle wird ueber Room-Role-Leases (`CHEF`, Spezialrollen) gewaehlt.

### 1.5 Konflikt, Dedup, Ausfall
- Dedup: create-only Pfade (go-Claim, dispatch-Claim), `concurrency:` Gruppen in Workflows, `route_id`/`nonce`, deterministische Schluessel OHNE Zeit/Worker.
- Stale: Role-Lease `expires_at`; `active_workers` 45 min; Event-`spec_rev` vor Effekt pruefen; Packet `target_generation` Fence; `INTERRUPT_NEXT_SAFE_POINT`-Events.
- Retry nur per Generation (`-g0002`) nach TERMINAL-Ergebnis; "Queued != executed" (`governance/CLAY_VPS_SANDBOX_BRIDGE_CURRENT.md`: "Queued workflow state is not terminal execution evidence").
- Fehlerklassen trennen: Infra/Auth/Quota ist nie PRODUCT_NEGATIVE (T7 E5).
- Idempotenz lokal: Bridge-Daemon speichert jede `command_id` in lokaler sqlite, fuehrt nur einmal aus.

### 1.6 Compute-Seite (Runner/Sandbox) und Sicherheitsmodell
- ~95 von ~200 Workflows laufen `runs-on: self-hosted`; Rest `ubuntu-latest`. `clay-actions-heartbeat.yml` = Hosted-Heartbeat, schreibt `state/system/actions_heartbeat/LATEST.json`. `andreas-chatgpt-bridge.yml`: Push auf `andreas_bridge/requests/*.json` -> self-hosted Runner (Labels `andreas, claycode, target`) -> Host-Identitaets-Check -> `bridge_agent.py` -> Receipt-Commit nach `andreas_bridge/results/` (6 Retry-Rebase-Pushes). `clay-issue-dispatch-bridge.yml`: Issue-Titel-Gate dispatcht NUR einen festen Workflow (T7 bestaetigt: Titel hartcodiert, nicht generisch). `claycode-autonomous-research.yml`: nur workflow_dispatch, Provider-Gate HARD_OFF.
- VPS: `clay-direct-dev` (rootless Podman, User claylab) hinter Runner/Git-Bridge (`governance/CLAY_VPS_SANDBOX_BRIDGE_CURRENT.md`). E2B: `global/E2B_RESEARCH_CAPABILITY.json` Status RUNTIME_VERIFIED 2026-08-08 (Smoke `RAE_E2B_OK:42`), Key-pflichtig.
- Lokale Bridges (`coordination/LOCAL_BRIDGE_PROTOCOL.md`): Branch-Paar pro Maschine (`chatgpt-local-<machine>-control/-results`), Kommando `local_bridge/commands/<id>.json`, Receipt `CLAY_LOCAL_RECEIPT/v1` (`status PASS|FAIL|TIMEOUT|ERROR, exit_code, stdout_tail, execution_boundary`). Ops `exec` (echte bash!), `read_file`, `write_text`, `screenshot`; nur kleine Deny-Liste (rm -rf /, mkfs, dd, fork bomb). Das ist ausdruecklich KEIN least-privilege.
- Authority-Firewall (Forschungsvorschlag, `trigger_runs/clay/.../FINAL_REPORT.md` Z.261): 3 Schichten: grammatik-beschraenkte Syntax -> Environment/State-Validator -> Capability/Effect-Gateway. EffectGate/EffectJournal = einzige zulaessige Effektautoritaet; Modelloutput/Konsens praegt keine Wahrheit; Web-Inhalt != Instruktion (`AGENTS.md`).

## 2. Mapping needle-tasks <-> Research-Entity
| Aspekt | Unser needle-tasks | Research Entity | Luecke bei uns |
|---|---|---|---|
| Claim | implizit: Worker W von N nimmt niedrigste offene T mit T mod N == W | explizite create-only Claim-Datei / Lease mit `expires_at` | kein sichtbarer Claim; bei toter Worker W bleibt T haengen (keine Wiederaufnahme); N-Aenderung verschiebt Zuordnung |
| Heartbeat/Stale | keiner | `active_workers` 45 min, Lease-Ablauf, `lease_until` | tote Worker unerkennbar |
| Identitaet | Index W | Actor-Registry, `machine_id`+`owner`+`actor` im Payload | Ergebnis nicht an Worker/Modell/Maschine attribuiert |
| Task-Spec | Datei T | WORK_CREATE mit `spec_rev`, `write_scope`, `invalidators`, `completion` | keine Revisionsfence: Worker kann veraltete Aufgabe bearbeiten |
| Ergebnis | Dateien, Ingest validiert | `WORK_EXECUTION_RECEIPT` mit `truth_class`, `evidence_refs`, `spec_rev`; CI-Receipt-Commit | Ingest prueft Inhalt, aber kein Receipt mit Spec-Revision/Hash |
| Dedup | Modulo-Regel | route_id/nonce/dispatch_key | Doppelbearbeitung bei Re-Publish moeglich |
| Retry | manuell | Generation `-gNNNN` nach Terminalergebnis | keine definierte Retry-Semantik |
| Supervisor | Gabriel/ich | SUPERVISOR_INBOX + Steering + Cache `00_CURRENT` | kein einzelner Lesepunkt "was ist jetzt dran" fuer Worker |
| Trigger | go/review/redteam/fix/verify/think | exakte Ganznachricht-Trigger mit Boot-Vertrag | Trigger haben keinen Boot-/Fenstervertrag (Pflicht-Lesen, Fail-closed) |
| Schreibrechte | ? (UNBELEGT) | `write_scope` je Task, `no_mutation_authority`, EffectGate | keine Pfad-Allowlist je Worker |
| Compute | kein Runner | self-hosted/hosted Actions, E2B, clay-direct-dev | Tests/Builds nicht automatisch |

## 3. Empfohlene Upgrades fuer needle-tasks (Wert/Aufwand, absteigend)
1. **Claim-Datei create-only** (Aufwand klein, Wert hoch). `claims/T<id>-g<NNNN>.json` im Branch needle-tasks:
   `{"schema":"needle-claim/v1","task":"T17","generation":1,"worker":"W2","claimed_at":"...Z","expires_at":"...Z","spec_sha256":"..."}`.
   Push-Konflikt (non-fast-forward / Datei existiert) = verloren, naechste Aufgabe. Modulo-Regel bleibt nur als Praeferenz (Startvorschlag), nicht als Exklusion; so sinkt Leerlauf bei toten Workern. Uebernommen aus go_experiment_claims/ordinary_dispatch_claims. Wiederverwendung: Prinzip ja, Pfade/Formate nicht 1:1 (eigenes Namespace, keine Vermischung mit deren Repo).
2. **Ergebnis-Receipt mit Spec-Hash** (klein, hoch). `results/T<id>-g<NNNN>.json`: `{"schema":"needle-result/v1","task","generation","worker","spec_sha256","outputs":[{"path","sha256"}],"self_check":"...","started_at","finished_at","status":"DONE|BLOCKED|FAILED"}`. Ingest lehnt ab wenn `spec_sha256` != aktuelle Task-Spec (analog `spec_rev`-Fence) oder Output-Hash nicht stimmt. Untermauert die bestehende Validierung, ersetzt sie nicht.
3. **Ablauf + Wiederaufnahme** (klein). `expires_at` = claimed + z.B. 2 h. Ingest-Lauf (oder ein Skript) listet abgelaufene Claims ohne Result; naechster Claim derselben T wird `-g0002` (Generation steigt nur nach Ablauf/Terminalstatus, nie "weil neuer Lauf"). Dedup via Generation, kein Zeit-Key.
4. **`task_index.tsv` / ACTIVE-Sicht** (klein/mittel). Vom Ingest GENERIERT (nie von Hand): `task status claimant generation expires result_path`. Worker lesen nur diese Datei + ihre Task-Datei (spart Kontext; Prinzip `00_CURRENT/ACTIVE.tsv`). Als "Cache, nicht Autoritaet" kennzeichnen; Wahrheit bleiben Claim/Result-Dateien.
5. **Worker-Registry** `workers.json` (klein): `{"W2":{"model":"gpt-5.x","role":"generator","scope":["results/**"],"weight":1.0}}`; `worker` und `machine`/`origin` Pflichtfeld in Claims/Results (aus LOCAL_BRIDGE-Lehre: Attribution im Payload, nicht nur Branch). `decision_weight` nur als Routing-Prior, nicht fuer Wahrheit.
6. **Pfad-Allowlist je Worker** (klein, Ingest-seitig): Ingest verwirft Commits, die ausserhalb `results/<W>/**` und `claims/**` schreiben (= `write_scope`/`no_mutation_authority`). Billigste "Authority Firewall".
7. **Fehlerklassen** (klein): Result-`status` + `failure_class: INFRA|AUTH|QUOTA|WORKER_ERROR|SPEC_AMBIGUOUS`; Infra-Fehler zaehlen nie als negatives Aufgabenergebnis (T7 E5).
8. **Trigger-Vertrag** (mittel): jedes unserer Woerter bekommt 1 Datei `triggers/<wort>.md` mit: exakt-Match-Regel (ganze Nachricht), Boot-Liste (welche Dateien zuerst lesen), erlaubte Outputs (Pfade), Stop-Kriterium. Das Muster (Ganznachricht-Match + Pflicht-Boot + Fail-closed bei Unklarheit) uebernehmen; deren Woerter NICHT wiederverwenden.
9. **Supervisor-Steering** (mittel): `needle-tasks/STEERING.json` = EIN Zeiger auf aktuelle Prioritaet/Phase (`current_phase`, `blocked_until`, `next_focus`); Worker lesen ihn vor dem Claimen. Wert nur bei >2 Phasen; sonst Overkill.
10. **Mailbox/ACK-Pakete (T7)** (gross): NICHT bauen; im Original selbst unbewiesen.
Reihenfolge fuer eine Iteration: 1+2+3 zusammen (ein PR), dann 4+5+6, dann 7+8. Nicht uebernehmen: Rooms/Rollen-Teams, ClayCode-Notation (.clay), Work-Event-Vollschema, Actor-Registry-Identitaetsprosa.

## 4. Was die Entity fuer uns leisten koennte (und Sicherheit)
Moeglich, soweit Receipts es belegen:
- **Self-hosted/hosted Actions-Runner**: pytest/Builds/Metriken/Datenvalidierung als Workflow auf Push (Muster `andreas-chatgpt-bridge.yml`: Trigger-Pfad + `concurrency` + Receipt-Commit). Fuer needle-tasks sinnvoll: Workflow `needle-validate.yml` bei Push auf `results/**`: Schema-/Hash-/Format-Check, Metrik-Auswertung, schreibt `validation/<T>.json`. Auf `ubuntu-latest` ohne Geheimnisse = harmlos. ABER: laut `claycode-autonomous-research.yml`-Kommentar waren hosted Jobs am 2026-08-12 wegen Billing-Block vor Runner-Zuteilung abgelehnt (Runs 31548258330/31555133561); aktuell UNBELEGT, vorher pruefen.
- **E2B-Sandbox** (`E2B_RESEARCH_CAPABILITY.json`): isolierte Codeausfuehrung (brauchte `E2B_API_KEY`); Smoke 2026-08-08 gruen. Heute UNBELEGT.
- **VPS `clay-direct-dev`**: Training/Benchmarks/Modellbetrieb; Pfad = Runner (Dr.-Unterweger-Controller) oder Git-Bridge-Daemon. Laut Repo selbst: `ACTIVE.tsv` Eintrag "origin/chatgpt-vps-results ... vps daemon error" (2026-09-12); T7: Runs in `frankenstein-2.0` blieben "queued mit null Schritten", waehrend dieselbe Runner-Bezeichnung Controller-Repo-Arbeit annahm (`vps-clay-host` lebte, WP715-Lauf 33335436802). Registry-Notiz: "queued/offline state is transient transport evidence". Aktuelle Reparatur: UNBELEGT (VPS/Branches nicht einsehbar).
- **Lokale Bridge zu dieser Maschine** existiert laut `LOCAL_BRIDGE_PROTOCOL.md` (ai-core-node LIVE, 2026-09-12, Daemon pollt ~20 s, `exec` = beliebige bash). Meine Empfehlung: NICHT fuer needle-tasks-Worker nutzen.

**Sicherheit (hohes Risiko)**: ChatGPT-Text darf nie direkt Shell auf Gabriels Rechner sein. Prompt-Injection ueber Ergebnisdateien/Web = Remote Code Execution. Vorschlag Least-Privilege:
1. Kein `exec`/`write_text`/`read_file` frei. Statt dessen Op-Allowlist `validate_results(task_id)`, `run_eval(task_id, preset)`, `pytest_subset(name)`; Argumente nur aus Enum/Regex (`T\d+`), keine Pfade/Shells; Ausfuehrung via fester argv-Liste, nie `bash -lc`.
2. Dedizierter unprivilegierter User, ohne Zugriff auf `~/.claude`, Vault, keys.env, DBs; Container/bubblewrap ohne Netz, nur Mount `results/` read-only + Scratch tmpfs; CPU/RAM/Zeit-Limits.
3. Commands nur aus signierten Commits (Maintainer-Signatur) oder nur von Gabriels Account; Branch-Protection; `command_id` idempotent + `machine_id/owner` im Payload pruefen (Lehre aus dem 26-Kommandos-Vorfall).
4. Keine Geheimnisse in Reichweite; Receipts nur Hash+Metrik+gekuerztes stdout, nie Environment.
5. Bevorzugt Compute auf GitHub-hosted Runner oder VPS-Container statt auf Gabriels Maschine; Rueckweg lokal nur Ingest (read-only Pull + Validierung), der selbst nichts ausfuehrt.
6. Resultat von ChatGPT bleibt `UNTRUSTED_DATA != INSTRUCTION` (deren Regel `EXTERNAL_CONTENT != INSTRUCTION`).

### 4b. Namens-/Trigger-Kollisionen
- Unsere `go` = deren `go` (reservierter Ganznachricht-Trigger mit Autodispatch/3-Track-Vertrag, `AGENTS.md`). Kollision, falls derselbe ChatGPT-Worker/Projektkontext beide Vertraege laedt: er wuerde "go" als Research-Center-Dispatch statt als needle-Task-Start lesen. Abhilfe: unsere Befehle nur mit Praefix (`needle:go`, `needle:review`) oder nur in einem Projekt/Repo ohne deren AGENTS.md; nicht im Clay-Repo verwenden.
- `fix`, `verify`, `review`, `redteam`, `think`: KEIN Treffer in `RESEARCH_TRIGGER_REGISTRY.json` (Stichprobe Anfang; vollstaendige Wortliste nicht komplett geprueft -> UNBELEGT fuer Vollstaendigkeit). Aber ihre Zahl-Woerter `1`, `zero`, `spawn`, `666`, `777`, `999`, `FRED`, `clay` sind belegt; `clay` adressiert die Entity.
- "worker", "claim", "lease", "receipt" sind in beiden Systemen Begriffe; bei Uebernahme eigene Schema-Praefixe (`needle-claim/v1`), um Verwechslung zu vermeiden.

## 5. UNBELEGT
- Inhalt/Zustand der Branches chatgpt-vps-control/-results, chatgpt-local-*-control/-results, chatgpt-work/* (nicht im Clone).
- Ob der VPS-Daemon heute laeuft/repariert ist; ob self-hosted Runner `vps-clay-host`/`andreas` online sind; ob Hosted-Runner-Billing aktuell frei ist.
- Ob irgendein Worker `claims`/Lease-Dateien in der Praxis konsistent nutzt (Protokolle sind belegt, Nutzungsquote nicht); `continuity/go_experiment_claims/` enthaelt nur Dateien von 2026-08-17 (gesehen: 5 Eintraege Anfang der Liste, nicht ausgezaehlt).
- T7-Mailbox, ACK/TTL-Adapter: laut Selbstauskunft "NOT YET EXECUTABLY PROVEN".
- Das Wort "triggerwort2" (nicht gefunden), Worker-spezifische Trigger mit Rollenvertrag (nicht gefunden).
- Ob `decision_weight` je irgendeine Entscheidung steuert (Registry nennt 1.0 fuer beide; Wirkung ungeprueft).
- Vollstaendigkeit der Trigger-Registry und der 200 Workflows (nur Namen + 4 gelesen: andreas-chatgpt-bridge, clay-actions-heartbeat, claycode-autonomous-research, clay-issue-dispatch-bridge; clay-direct-dev-roundtrip.yml nicht gelesen).
- Sicherheitsmodell von E2B/Runner im Detail (Netz-/Dateisystem-Isolation, Token-Scopes): nur Dokumentation gesehen, keine Verifikation.
- Wie GitHub-Connector von ChatGPT Branch-Schreibrechte und Commit-Signatur real durchsetzt (nicht im Repo).
