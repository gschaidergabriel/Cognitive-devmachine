# Generation 116 — Adapter-Evidenzkorrektur

## BIND

- Research-Snapshot: `95234c15716795cc5787bc231b6edbe00a51e5c1`
- Tree: `078894e342579577593bd606e73cb10e073f3b8f`
- Generation: 116
- Exportzeit: `2026-08-18T21:41:07Z`
- Testreceipt-Source: verkürzt `1a09c7593`

## Beobachtung

Der durable Export meldet `583 gruen / 1 rot` mit genau einem verbleibenden Test:

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Dieser Zustand ist nicht nur im neuesten Export vorhanden. Derselbe `583/1`-Receipt mit demselben Test und demselben verkürzten Source-Identifier liegt auch auf den früheren Snapshots `c43a3fef...` und `ff50d5c2...` vor.

Damit widerspricht der Commit-Narrativtext von `c43a3fef...` ("584 gruen, 0 rot") dem exportierten Messartefakt auf genau diesem Forschungsstand.

## Klassifikation

Status: `REPLICATED` fuer den dauerhaft exportierten `583/1`-Zustand.

Nicht promotionsfähig ist dagegen die Behauptung `584/0`, weil dafür im gebundenen Exportpfad kein dauerhaftes Testreceipt vorliegt.

## Haupt-Hypothese

Der Claude-Code-Runtime-Adapter-Invariant ist weiterhin tatsächlich ungelöst; ein kurzfristiger oder manuell beobachteter `584/0`-Lauf wurde in Committext übernommen, aber nicht durch den kanonischen Export-Receipt konserviert.

Erwartung: wiederholte automatisierte Exporte zeigen weiterhin denselben einen roten Adapter-Test, solange kein produktiver Adapter-Fix erfolgt.

## Gegenhypothese

Es existierte ein echter `584/0`-Lauf, aber der 30-Minuten-Exporter nahm später einen flackernden oder ambient-state-abhängigen `583/1`-Lauf auf. In diesem Fall wäre der Adapter-Test nicht deterministisch rot, sondern umgebungs-/zustandsabhängig.

Erwartung: kontrollierte Wiederholungen auf demselben Exact-Checkout wechseln zwischen gruen/rot oder korrelieren mit Environment-/Session-Unterschieden.

## Billigster diskriminierender Falsifikator

Ein atomarer `TEST_RECEIPT_LEDGER/v1` muss je Testlauf mindestens binden:

- vollständiger Source-Commit + Tree;
- `test_run_id`;
- Suite-Digest;
- Executor-Identität;
- normierter Environment-Digest;
- Green/Red/Skip-Zähler;
- geordnete Fail-Liste;
- Result-Digest;
- Start-/Endzeit.

Danach den Adapter-Test mehrfach auf demselben isolierten Exact-Checkout ausführen. Stabil rot -> Produkt-/Testinvariant untersuchen. Wechselnd -> Flake/Ambient-State kausal eingrenzen.

## Weitere aktuelle Messwerte

Generation 116 exportiert 114 Turns, 57 Causal-, 57 Workspace- und 57 Retrieval-Episoden, 175 Checkpoints, 67 `durable_memory`-Zeilen und 3 Effects. `retrieval_entrypoint_policy=0` sowie `retrieval_feedback=0` bleiben Null; damit gibt es weiterhin keinen Messbeleg für aktives Retrieval-Entry-Point-Lernen.

Die Zielmatrix liegt bei 50 erfüllt, 8 offen, 1 zurückgestellt. `ZIELE.md` stimmt beim Teststand mit dem durable Receipt überein: 583/1.

## Forschungsdelta

1. Frühere Forschungs-/Chatbehauptung `584/0` wird auf `UNVERIFIED_TRANSIENT` herabgestuft.
2. Kanonischer durable Teststand ist `583/1`.
3. Der einzige verbleibende rote Invariant ist der Claude-Code-Runtime-Adapter-Test.
4. Der höchste Informationsgewinn kommt jetzt nicht von breiter neuer Feature-Arbeit, sondern von deterministischer Exact-Source-/Environment-Bindung dieses einen Tests.
5. Retrieval-Lernen bleibt trotz wachsender Runtime-/Memory-Zähler unbelegt, weil Entry-Point-Policy und Feedback weiterhin 0 sind.

## Status

- Adapter-Rot: `REPLICATED`
- 584/0: `UNVERIFIED_TRANSIENT`
- Whole-system test green: `NOT VERIFIED`
- Retrieval-learning pass: `NOT VERIFIED`
- Whole Clay Machine: `NOT CLAIMED`
