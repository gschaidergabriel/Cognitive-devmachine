# Generation 224 — Wake-Governor-Frontier

## Gebundene Evidenz

- AgentZero Export: `d3b05b307a09f795c39ef2159758e7475072f0d4`
- Export Tree: `89c0d32a822d1571c7c98f1244939ff08d59a24c`
- Generation: 224
- Test-Receipt: 878 gruen / 1 rot
- Persistenter Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Receipt-Source-Short: `53082f39c`
- Zielmatrix: 71 erfuellt / 7 offen / 2 zurueckgestellt

## Neuer Architektur-Delta

Zwischen Gen223 und Gen224 ist der dritte Baustein des ereignisgetriebenen Wartens sichtbar geworden:

- `the artefact/clayverse/wake_governor.py`
- `the artefact/tests/test_wake_governor.py`
- `forschung/wake/governor_vs_puls.py`

Damit existieren jetzt mechanisch getrennte Schichten fuer:

1. typisierte Wake-Bedingungen,
2. persistente/coalesced Wake-Signale,
3. einen Governor, der die Signale gegen Polling verarbeiten soll.

Der Export-Bauverlauf bindet diese Dateien an lokale EntityOS-Chronik-Commits `b8af77281914`, `2278c47244d3` und `a9dcd89328c7`.

## Evidenzgrenze

Das Vorhandensein von Governor-Code und Tests ist noch kein Aktivierungs-Credit. Das Zielbild beschreibt den Wake-Vertrag weiterhin als nur teilweise promotionsreif; `wait` darf nicht allein aufgrund von Source-/Unit-Evidenz den 30-s-Puls ersetzen.

Vor Aktivierung muss ein `WAKE_GOVERNOR_RECEIPT/v1` mindestens folgende Race-/Recovery-Faelle binden:

- Event zwischen Condition-Check und Schlaf-Commit
- Restart zwischen Signal-Persistierung und Consume
- Duplicate/Replay
- stale Goal/Step Generation
- Deadline-vs-Event Ordering
- Wall-clock jump / monotonic-time binding
- Retention expiry
- Cross-session / cross-user isolation
- terminal effect/goal transitions
- `UNBEKANNT` / storage error fail-closed
- coalescing under load without event loss

## Neue Hypothese

Der entscheidende Fehlerkanal ist jetzt **WAKE LOST-BETWEEN-CHECK-AND-SLEEP**: Wenn der Governor zuerst den Zustand prueft, danach ein passendes Signal eintrifft und erst anschliessend der Schlafzustand durable wird, kann ein edge-triggered Consumer das Signal verlieren. Ein sicherer Entwurf braucht entweder einen atomaren DB-Handshake (condition generation + signal cursor + sleep registration) oder level-triggered Reconciliation beim Aufwachen/Restart.

## Hoechster Informationsgewinn

Ein gezielter Falsifikator sollte zwei Prozesse/barrieren verwenden:

1. Governor liest `OFFEN` und pausiert exakt vor durable sleep registration.
2. Producer persistiert das passende wake signal.
3. Governor setzt sleep registration fort.
4. Erwartung: der Schritt muss trotzdem genau einmal runnable werden; kein Lost Wake, kein Doppelrun.
5. Danach Prozess-Crash vor Consume-Commit und Restart; dieselbe Bedingung muss erneut reconciled, aber nicht doppelt ausgefuehrt werden.

Nur wenn dieser Test und die Recovery-Matrix auf einem exact source/tree + DB snapshot receipt gruen sind, ist ein schrittweiser Shadow->Partial->Default Switch vom 30-s-Puls verantwortbar.

## Sonstige Beobachtung

Die Testoberflaeche ist auf 879 Tests gewachsen, bei weiterhin exakt einem persistenten Red. Das staerkt die Lokalisierung des Claude-Code-Runtime-Adapters als separaten Boundary-Fehler, veraendert aber die Wake-Promotion nicht.

## Status

- Wake contract: mechanism present
- Wake signal: mechanism present
- Wake governor: mechanism present
- Governor activation credit: 0
- 30-s pulse fallback: keep
- Whole Clay Machine: not claimed
