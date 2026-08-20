# Generation 169 — Testdrift und DB-Lock als gemeinsamer Messfrontier

## Gebundener Stand

- AgentZero-Export: `42df314bf1729229bea55096228b0f8891846b30`
- Generation: 169
- Exportzeit: 2026-08-20T00:41:12Z
- Exportdauer: 162.05 s
- Test-Receipt Source-Kurz-ID: `df75f5114`

## Harte Befunde

1. `agentZero/tests/letzter-lauf.json` meldet fuer denselben Export **583 gruen / 1 rot**. Der einzige rote Test ist weiterhin:
   `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`.
2. Das automatisch erzeugte Zielbild (`ZIELE.md` / Zielaggregat) meldet dagegen **582 gruen / 2 rot**.
3. Damit liegt erneut ein Cross-Consumer-Widerspruch vor: Test-Receipt und Zielaggregator konsumieren offenbar nicht atomar denselben Run bzw. dieselbe Quelle.
4. Im Puls-Tail treten im selben Zeitfenster mehrere `database is locked`-Fehler mit etwa 202 ms Wartezeit auf, gefolgt von mehreren `notlauf`-Ereignissen (`keine Datenbankverbindung — Puls schlaegt, Phasen 1-5 aus`).
5. Die Exportdauer steigt gleichzeitig wieder stark auf **162.05 s**. Der vorherige einzelne 168.79-s-Spike war nachfolgend auf ca. 48 s und 43 s zurueckgefallen; Gen169 zeigt nun einen zweiten grossen Spike.

## Interpretation

### H1 — gemeinsame SQLite-/Snapshot-Kontention

Die Kombination aus expliziten `database is locked`-Ereignissen, Notlauf und erneut hoher Exportdauer macht SQLite-/Snapshot-Kontention jetzt deutlich plausibler als reine lineare Datenmengenskalierung. Das ist jedoch noch keine bewiesene Kausalitaet: Puls-Locks und Export-Latenz koennen denselben Host-Load teilen, ohne direkt voneinander verursacht zu sein.

### H2 — nicht-atomare Testkonsumenten

Der Widerspruch `letzter-lauf=583/1` vs. `ZIELE=582/2` ist unabhaengig von der Produktfunktion ein Messintegritaetsfehler. Ein Acceptance-Zustand darf nicht aus zwei unterschiedlich getakteten oder unterschiedlich gebundenen Quellen zusammengesetzt werden.

## Neue priorisierte Messung

`TEST_EXPORT_ATOMIC_RECEIPT/v1` sollte fuer einen Export in EINEM Receipt binden:

- full source commit + tree
- test_run_id
- Test-Suite-Digest
- gruen/rot/skip + geordnete Fail-Liste
- Start/Ende und Exitstatus des Tests
- DB-Snapshot-ID / WAL-Checkpoint-Position
- Zeitpunkt, an dem `ZIELE.md` seine Testzahlen liest
- Export-Start/Ende + Phasenzeiten
- SQLite busy/locked count und kumulative busy-Zeit je Phase
- COMPLETE / INCOMPLETE / ERROR als typisierter Zustand

Harte Invariante: `letzter-lauf.json`, Verlauf und `ZIELE.md` duerfen nur aus demselben terminalen Receipt rendern. Kein Fallback auf aeltere Zahlen und keine numerischen Sentinels fuer Fehlerzustand.

## Hoechster Informationsgewinn im naechsten Lauf

Mindestens sechs aufeinanderfolgende Exporte mit diesem gemeinsamen Receipt sammeln. Dann pruefen:

1. korreliert Exportlatenz mit `busy/locked`-Zeit?
2. tritt Testzaehler-Drift nur bei Lock/Notlauf auf oder auch ohne?
3. bleibt der Claude-Code-Adapter-Red in einem atomaren Exact-Source-Receipt deterministisch?

## Evidenzgrenze

- Kein Produktregressions-Credit aus dem Testzaehler-Widerspruch.
- Kein Fix-Credit fuer den Adapter.
- Kein Whole-System-PASS.
- Neue ungewoehnliche Experimente: 0.
