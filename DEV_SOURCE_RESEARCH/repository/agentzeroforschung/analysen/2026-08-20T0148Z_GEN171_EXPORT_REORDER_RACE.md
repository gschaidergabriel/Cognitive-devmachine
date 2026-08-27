# Generation 171 — Out-of-order Export / Snapshot Race

## Beobachtung

Zwei unmittelbar aufeinanderfolgende Gen-171-Export-Commits bilden **nicht** die zeitliche Reihenfolge der exportierten Snapshots ab:

- Parent `0ac95fd51e9e4f5c1340bb85888f6e82626a31ab` wurde als Git-Commit um 01:41:58Z geschrieben, exportiert aber Snapshot `2026-08-20T01:41:12Z`.
- Child `3f9f66c3a0f597d18234021078085fb62a9f155d` wurde spaeter um 01:42:25Z geschrieben, exportiert aber den **aelteren** Snapshot `2026-08-20T01:40:40Z`.

Der Child ueberschreibt damit im kanonischen Git-Verlauf einen neueren Snapshot mit einem aelteren Snapshot.

## Test-Frontier-Swap bei gleichem Source-Identifier

Beide Receipts nennen `commit = f681ca215` und jeweils `583 gruen / 1 rot`, aber der rote Test wechselt:

- Snapshot 01:41:12Z: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Snapshot 01:40:40Z: `tests/test_terminal_ws_auth_lease_protocol.py::test_same_clerk_session_can_refresh_and_continue_pty_input`

Das ist **kein belastbarer Rot->Gruen- oder Gruen->Rot-Produktdelta**, weil der spaetere Git-Commit einen aelteren Laufstand repraesentiert.

## Weitere sichtbare Folge

Der spaetere Child-Commit setzt die Zielmatrix von `59 erfuellt / 5 offen / 1 zurueckgestellt` auf `62 / 2 / 1`, obwohl sein exportierter Snapshot zeitlich aelter ist. Dadurch kann ein Konsument, der nur Git-Head oder Commit-Reihenfolge betrachtet, faelschlich eine Verbesserung ableiten.

## Klassifikation

`EXPORT_COMMIT_ORDER != SNAPSHOT_TIME_ORDER`

Staerkste Hypothese: mehrere Exportprozesse laufen ueberlappend und committen nach Abschlussdauer statt nach Snapshot-Erfassungszeit. Langsamerer aelterer Lauf kann einen bereits persistierten neueren Snapshot ueberschreiben.

## Sicherheits-/Evidenzfolge

Bis zur Reparatur gilt:

1. Git-Commit-Reihenfolge allein ist **keine** kanonische Zeitordnung fuer AgentZero-Exports.
2. Ein Export darf nur Promotion-/Regression-Credit erhalten, wenn `snapshot_captured_at`, `test_run_id`, Full Source Commit+Tree und Export-Run-ID gebunden sind.
3. Ein Commit mit `snapshot_captured_at <= latest_committed_snapshot_captured_at` muss fail-closed verworfen oder unter einer unveraenderlichen Run-ID archiviert werden, darf aber den kanonischen `latest`-Zustand nicht zuruecksetzen.
4. Test-Frontier-Wechsel zwischen solchen out-of-order Runs bekommen `0` Produkt-Fix-/Regression-Credit.

## Vorgeschlagenes Instrument: EXPORT_SERIALIZATION_RECEIPT/v1

Pflichtfelder:

- `export_run_id`
- `snapshot_captured_at_monotonic`
- `snapshot_captured_at_utc`
- `source_commit_full`
- `source_tree`
- `test_run_id`
- `test_result_digest`
- `db_snapshot_id` / WAL position
- `export_started_at`
- `export_finished_at`
- `git_parent`
- `latest_snapshot_before_commit`
- `commit_admission = ACCEPT | ARCHIVE_STALE | REJECT`

Harte Invariante: Ein aelterer Snapshot darf niemals den kanonischen neuesten Snapshot ersetzen.

## Naechster hoechst-informativer Test

Zwei kontrolliert ueberlappende Exporte starten: Lauf A nimmt zuerst Snapshot, wird absichtlich verlangsamt; Lauf B nimmt spaeter Snapshot und beendet zuerst. Erwartung nach Fix: B wird kanonisch, A wird als `ARCHIVE_STALE` persistiert oder verworfen und kann `latest` nicht rueckwaerts bewegen.

## Credit

- Produkt-Fix-Credit fuer Adapter/PTy-Swap: `0`
- Messgeraete-/Architektur-Credit: `YES` — konkreter Out-of-order-Commit-Pfad belegt
- Whole-machine acceptance: `NO`
