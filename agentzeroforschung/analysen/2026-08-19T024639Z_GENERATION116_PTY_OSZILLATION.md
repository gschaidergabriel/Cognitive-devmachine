# Generation 116 — PTY-Lease-Oszillation als Reproduzierbarkeitsbefund

## Bindung

- neuester ausgewerteter Export-Commit: `68d8c7b1224496ff76acbd8121e9da0d7b74cf7a`
- Export-Tree: `8277af1ffcccb8195b1a61f549359d196064ac59`
- Generation: `116`
- Exportzeit: `2026-08-19T02:41:07Z`
- Testreceipt-Zeit: `2026-08-19T02:42:24Z`
- verkürzter Receipt-Source-Identifier: `1a09c7593`

## Beobachtet

Der unmittelbar vorherige Export `a5c68d5e14f70193362c3b0dbbf9fca77a10f1bd` meldet auf demselben verkürzten Source-Identifier `1a09c7593`:

- `583 GREEN / 1 RED`
- einzig rot: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Der neueste Export `68d8c7b1...` meldet 31 Minuten später:

- `582 GREEN / 2 RED`
- weiterhin rot: Claude-Code-Runtime-Adapter-Isolation
- erneut rot: `tests/test_terminal_ws_auth_lease_protocol.py::test_same_clerk_session_can_refresh_and_continue_pty_input`

Der PTY-Lease-Invariant hat damit in der beobachteten Gen-116-Zeitreihe bereits mehrfach zwischen rot und grün gewechselt, ohne dass die exportierte Receipt-Source-Identität wechselt.

## Ableitung

Der PTY-Lease-Test darf nicht als dauerhaft repariert oder dauerhaft defekt klassifiziert werden. Die wiederholte Zustandsoszillation ist selbst die belastbare Evidenz. Der Befund wird von `Fix-Credit` auf `REPRODUCIBILITY_FRONTIER` getrennt.

Die persistente Claude-Code-Adapter-Isolation bleibt davon separiert: sie ist ueber dieselben Snapshots stabil rot und ist damit der staerkere Kandidat fuer einen deterministischen Produkt-/Adapter-Invariant.

## Haupt-Hypothese H1

Der PTY-Lease-Test exponiert eine echte Timing-/Race-Bedingung an der Session-/Lease-Grenze. Erwartung unter H1: Bei identischem Source-Tree steigt die Fehlerrate systematisch mit bestimmten Scheduler-, Last-, Timing- oder Event-Ordering-Bedingungen; instrumentierte Fail-Runs zeigen eine abweichende Reihenfolge von Lease-Refresh, PTY-Input und Session-State-Commit.

## Gegenhypothese H0

Die Rot/Grün-Wechsel entstehen durch nicht gebundene Executor-/Environment-/Test-Harness-Zustaende und nicht durch die Produktsemantik. Erwartung unter H0: Nach vollstaendiger Environment-Bindung verschwindet die Varianz oder korreliert mit einer Harness-/Executor-Dimension statt mit dem internen Lease-Protokoll.

## Billigster diskriminierender Falsifikator

Auf demselben vollstaendigen Commit+Tree und demselben isolierten Ubuntu-Executor den einzelnen PTY-Test mehrfach ausfuehren und pro Versuch atomar erfassen:

1. `test_run_id`, Full Source SHA + Tree SHA;
2. Kernel/OS/Python/pytest-Version und Executor-Image-Digest;
3. monotone Timestamps fuer Session-Create, Lease-Issue, Lease-Refresh, PTY-Input-Admission, PTY-Write und Session-State-Commit;
4. Session-ID, Lease-ID/Generation und Refresh-Resultat;
5. Prozess-/Thread-/Eventloop-Identitaet und relevante Timeoutwerte;
6. CPU-/Load-Klasse bzw. kontrollierte Laststufe;
7. Testresultat und Failure-Signatur.

Minimaler Versuchsplan: mindestens 30 Wiederholungen bei Baseline und 30 unter kontrollierter CPU/Eventloop-Last. Keine Produktmutation vor der Messung. Wenn Failures an ein reproduzierbares Ordering-Fenster gebunden sind, H1 wird `MECHANISM_SUPPORTED`; wenn sie nur mit Executor/Harness-Drift verschwinden/auftreten, H0 gewinnt.

## Messinstrument-Vorschlag

`PTY_LEASE_TRACE/v1` als Teil von `TEST_RECEIPT_LEDGER/v1`:

- Variable: Lease-/Session-State-Transitions und monotone Zeitdifferenzen;
- Einheit: ns oder us auf monotonic clock;
- Trigger: nur PTY-Lease-Protocol-Tests und spaeter optional sampled live sessions;
- Clock: monotonic lokal zum Executor, zusaetzlich UTC Run-Anker;
- Provenienz: Full Source SHA, Tree, Executor-Digest, Test-Run-ID;
- Missing-Semantik: fehlendes Event = explizit `MISSING_EVENT`, niemals 0;
- Bias: Instrumentierung kann Timing veraendern; deshalb leichte und schwere Trace-Variante vergleichen;
- Informationsgewinn: trennt Race/Ordering von Ambient-State-/Harness-Flake.

## Status

- PTY lease invariant: `REPLICATED_NONDETERMINISM`
- PTY fix credit: `0`
- Claude adapter red: `REPLICATED_PERSISTENT`
- Exact-source promotion credit: `0`, solange `1a09c7593` nicht auf Full Commit+Tree gebunden ist
- Whole-system acceptance: `NOT_CLAIMED`

## Naechster Schritt

1. Full Commit+Tree hinter `1a09c7593` binden.
2. `TEST_RECEIPT_LEDGER/v1` um Environment-Digest und `PTY_LEASE_TRACE/v1` erweitern.
3. PTY-Test wiederholt und kontrolliert ausfuehren, bevor irgendein Fix-Credit vergeben wird.
4. Den persistenten Claude-Adapter-Test separat als deterministischen Frontier weiter untersuchen.
