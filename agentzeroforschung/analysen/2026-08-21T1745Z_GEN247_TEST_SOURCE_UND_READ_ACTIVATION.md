# Gen247: Test-Source-Bindung und Read-Side-Aktivierung

Status: SOURCE-PROVENANCE PARTIALLY RESOLVED + READ-SIDE MUTATION SOURCE-CONFIRMED. Research-only; no AgentZero product bytes changed by this receipt.

## Neuer kanonischer Stand

Der aktuelle Generation-247-Export `8d7d549ab9588adf8a952e0ea617f8898c5c53da` meldet 1244 grüne und 1 roten Test. Der verbleibende rote Test ist weiterhin:

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Das Test-Receipt nennt Source-Short `2b01ead42`.

## Source-Provenienz enger aufgelöst

Der exportierte Bauverlauf enthält zur passenden Epoche einen lokalen EntityOS-Chronik-Commit `2b01ead42d0f` mit Änderungen an:

- `the artefact/architekt/budget.py`
- `the artefact/architekt/immunsystem.py`
- `the artefact/architekt/zustand.py`
- `the artefact/tests/test_architekt_budget.py`
- `the artefact/tests/test_architekt_immunsystem.py`
- `the artefact/tests/test_architekt_zustand.py`

Damit ist der zuvor anonyme Test-Source-Short erstmals an eine konkrete lokale EntityOS-Chronik gebunden. Full 40-SHA, Tree, Dirty-State und Executor-/Dependency-Digest fehlen weiterhin; finaler Exact-Source-Promotion-Credit bleibt deshalb 0.

## Read-Side-Aktivierung bleibt ein eigener harter Frontier

Gen247 hat zusätzlich eine runtime-materialisierte Schema-Fähigkeit gezeigt: Read-Methoden im Bug-/Bewertungsbereich rufen `sicherstellen()` auf, das `CREATE TABLE/INDEX IF NOT EXISTS` ausführen kann. Damit kann ein semantisch lesender Pfad beim ersten Zugriff durable DDL auslösen.

Der bereits angelegte `READ_SIDE_EFFECT_RECEIPT/v1` plus gepaarter Discriminator ist der richtige Falsifikator:

1. Negative control: read-only `/readyz` gegen eingefrorene Disposable-DB; keine Schema-/Data-Deltas erwartet.
2. Positive discriminator: erster `GET /api/bug` gegen DB ohne `eos_bug_hypothesen`; DDL/Schema-Delta erwartet, falls die Hypothese korrekt ist.
3. Zweiter identischer `GET /api/bug` nach Materialisierung; sollte bei reinem Lazy-Init-Mechanismus wieder observational read-only sein.

## Neue Fusion

Die beiden Frontiers gehören zusammen, dürfen aber nicht vermischt werden:

- `2b01ead42 -> 2b01ead42d0f` verbessert die Provenienz des Test-Snapshots.
- Read-Side-Schemaaktivierung erklärt eine versteckte Mutationsautorität und mögliche Lock-/Observer-Effekte.

Neue Regel:

`TEST_SOURCE_IDENTITY != RUNTIME_SIDE_EFFECT_IDENTITY`

Beides muss separat gebunden werden, bevor ein Testresultat als Whole-System-Evidenz gilt.

## Nächster höchster Informationsgewinn

1. Full SHA + Tree hinter `2b01ead42d0f` exportieren.
2. `TEST_EXPORT_ATOMIC_RECEIPT/v1` mit Source, Tree, Dirty-State, Executor und Environment abschließen.
3. `READ_SIDE_EFFECT_RECEIPT/v1` gepaart ausführen und statement-/schema-/lock-seitig binden.
4. Den persistenten Claude-Code-Adapter-Red weiter separat in `toolless`, `ephemeral`, `structured-output`, `environment/HOME-isolation` zerlegen.

Whole Clay Machine: NOT CLAIMED.
