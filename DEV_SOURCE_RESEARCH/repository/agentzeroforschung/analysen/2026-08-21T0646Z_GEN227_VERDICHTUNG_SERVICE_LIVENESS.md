# Generation 227 — Pflichtdienst-Liveness vor weiterer Acceptance

## Gebundene Evidenz

- AgentZero-Export: `f11a9386f12122c7dbe1055efd3ce217df24ba64`
- Export-Tree laut Supervisor: `6da2b1913d8f05331c9cf3d9aa8497826df74f79`
- Generation: 227
- Executable Test-Receipt: `896 gruen / 1 rot`
- Persistenter Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Receipt-Source-Short: `483cfbbf0`
- ZIELE Runtime-Probe: nur `3/4` Pflichtdienste gesund; `verdichtung` ist `TOT/WIRKUNGSLOS`, obwohl sie getaktet ist; `6/6` gezuendete Bahnen scheiterten.

## Neue Kernaussage

Gen227 liefert einen starken operationalen Gegenbeweis gegen die Gleichsetzung von fast vollstaendig gruenen Tests mit einer gesunden laufenden EntityOS/AgentZero-Instanz. Die Testoberflaeche wuchs auf 897 gemessene Tests mit nur einem persistenten Red, waehrend gleichzeitig ein deklarierter Pflichtdienst seine Wirkung vollstaendig verlor.

Daraus folgt eine Architekturregel:

> Unit-/Integration-Suite und Mandatory-Service-Liveness sind orthogonale Acceptance-Achsen. Eine darf die andere niemals implizit vertreten.

## Hypothesenraum fuer 6/6 Verdichtungsfehler

H1 — Provider-/Capability-Drift:
Eine oder mehrere bisher funktionierende FREE_ONLY-Bahnen sind extern nicht mehr erreichbar, haben Modell-/Endpoint-Namen geaendert oder weisen neue Quoten-/Rate-Limits auf.

H2 — Credential-/Konfigurationsdrift:
Provider ist erreichbar, aber lokale Token-/Env-/Routing-Konfiguration ist stale, unvollstaendig oder wird im Dienstkontext nicht mehr transportiert.

H3 — Queue-/Scheduler-/Service-Regression:
Der Timer feuert, aber Worker/Queue/Claim/Retry oder der eigentliche Verdichtungsprozess erreicht keine terminale Erfolgsschreiboperation.

H4 — Input-/Schema-Regression:
Alle sechs Bahnen erhalten nun einen Payload, den sie mechanisch ablehnen oder der vor Providerkontakt an Validierung/Serialisierung scheitert.

H5 — Netzwerk-/DNS-/TLS-Lokalschaden:
Der Dienstcontainer/-prozess kann externe FREE_ONLY-Endpunkte nicht erreichen, obwohl andere Teile des Hosts Zugriff haben.

H6 — Messgeraetefehler:
Verdichtung wirkt, aber der Liveness-Pruefer misst einen falschen DB-Pfad, veraltete Resultatfelder oder verwechselt 'fired' mit 'effectively completed'. Diese Hypothese muss erhalten bleiben, weil im Projekt wiederholt Messpfad-/Snapshotfehler nachgewiesen wurden.

## Hoechster Informationsgewinn: MANDATORY_SERVICE_LIVENESS_RECEIPT/v1

Fuer jeden der sechs gezuendeten Versuche atomar binden:

- full source commit + tree + dirty state
- service/unit identity und service generation
- scheduler tick / trigger id
- lane id + provider + model/family
- FREE_ONLY admission decision
- request start/end monotonic timestamps
- endpoint class (ohne Secret)
- HTTP/transport status
- timeout/rate-limit/auth/DNS/TLS/network classification
- input digest + output digest
- fallback transition
- quota/budget state
- queue/claim state
- DB target + terminal write/result state
- recovery/retry attempt
- final typed state: `SUCCESS | PROVIDER_UNAVAILABLE | AUTH_ERROR | RATE_LIMIT | NETWORK_ERROR | INPUT_REJECTED | LOCAL_RUNTIME_ERROR | UNMEASURED`

`ERROR` darf nicht als `0`, leerer String oder 'keine Wirkung' aggregiert werden.

## Kontrollen

1. Aus demselben Service-/Container-Netzwerk eine bekannte FREE_ONLY-Kontrollanfrage an genau einen aktuell erwartbar erreichbaren Lane-Typ senden.
2. Derselbe Input einmal durch die reale Verdichtungspipeline und einmal bis unmittelbar vor Providertransport fuehren, um Input-/Serialisierungsfehler zu trennen.
3. DB-Schreibpfad separat mit einem synthetischen, nicht-produktiven Resultat pruefen, ohne eine Providerantwort als Erfolg zu simulieren.
4. Bei einem transienten Providerfehler denselben Lane nicht global als 'unavailable' markieren; mindestens ein unabhaengiger Wiederholungs-/Kontrollbeleg ist erforderlich.
5. Keine bezahlte Fallback-Kapazitaet und keine Together-API einfuehren.

## Promotionsregel

`MANDATORY_SERVICES_ACCEPTED = true` nur wenn alle vier Pflichtdienste auf dem akzeptierten Ubuntu-Exact-Source entweder (a) eine echte terminale Wirkung mit gebundener Provenienz produzieren oder (b) fuer eine explizit deklarierte, vom Eigner akzeptierte Degradationssemantik einen fail-closed Receipt liefern. 'Timer laeuft' reicht nicht fuer `verdichtung`.

## Weitere offene Grenzen nicht verdraengen

- Gen224 Wake-Event-Replay / fehlende durable Cursor-/Ack-Semantik: Wake-Governor bleibt ohne Aktivierungscredit; 30-s-Puls bleibt Fallback.
- Gen227 ZIELE-Wake-Probe ist stale, weil sie den Governor als fehlend bezeichnet, obwohl `wake_governor.py` bereits gebundene Source-Evidenz hat.
- `LIVEPATH_GWT_EQUIVALENCE_RECEIPT/v1` bleibt offen.
- `TEST_EXPORT_ATOMIC_RECEIPT/v1` und Full EntityOS Source Commit+Tree+Dirty-State+Ubuntu-Executor fehlen.
- Persistenter ClaudeCodeInference-Adapter-Red bleibt separat zu zerlegen.

## Neue Forschungsbegriffe

**Coverage–Liveness Decoupling** — eine wachsende gruene Testsuite kann gleichzeitig mit dem Ausfall eines Pflichtdienstes existieren.

**Scheduled-but-Dead Service** — ein Dienst kann korrekt getaktet und prozessual sichtbar sein, aber keinerlei terminale Wirkung mehr erzeugen.

**Lane Failure Correlation** — 6/6 gleichzeitige Fehler sind prima facie eher kompatibel mit gemeinsamem Konfigurations-/Netzwerk-/Input-/Messpfad als mit sechs unabhaengigen Modellfehlern; dies ist nur eine Priorisierung, kein Beweis.

## Naechster exakter Schritt

Keine breite Reparatur. Zuerst genau einen `MANDATORY_SERVICE_LIVENESS_RECEIPT/v1` fuer alle sechs bereits beobachteten/neu reproduzierten Bahnen erzeugen und anhand der typisierten Terminalzustaende entscheiden, ob Provider, Credential, Input, lokaler Runtimepfad oder Messinstrument der gemeinsame Nenner ist. Erst danach die kleinste gezielte Reparatur.