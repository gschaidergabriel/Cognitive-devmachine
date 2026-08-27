# Generation 116 — PTY-Oszillation fortgesetzt

Gebundener Export: `5a2cbb3916235dab9811d0053fde94064cb53dcb`
Tree: `d9239e72d9bc452993c48207998042069b9fe08e`
Zeit: 2026-08-19T03:11:43Z

## Befund

Der aktuelle Test-Receipt meldet wieder **583 gruen / 1 rot**. Der zuvor erneut rote Clerk-PTY-Lease-Test ist wieder gruen; einzig dauerhaft rot bleibt:

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Der Receipt bindet weiterhin nur den verkürzten Source-Identifier `1a09c7593`.

## PTY-Klassifikation

Die beobachtete Folge lautet nun mindestens:

`RED -> GREEN -> RED -> GREEN -> RED -> GREEN`

Zwischen dem unmittelbar vorherigen Research-Stand `b643704e7245d1e9cb3302c5ef1db2bd5e5d6b52` und dem Export `5a2cbb3916235dab9811d0053fde94064cb53dcb` liegt kein ausgewiesener Produkt-Fix; der neue Commit ist ein periodischer AgentZero-Export. Deshalb bleibt **Fix-Credit = 0**.

Die PTY-Spur wird damit staerker als `REPLICATED_NONDETERMINISM` klassifiziert. Hauptklassen: Timing/Race, nicht gebundener Executor-/Environment-State oder Test-/Instrumentierungsflake.

## Persistenter Frontier

Der Claude-Code-Runtime-Adapter bleibt der einzige wiederholt rote Invariant und ist damit der prioritaere deterministische Reparaturpfad.

## Naechstes Messinstrument

`PTY_LEASE_TRACE/v1` sollte weiterhin Bestandteil von `TEST_RECEIPT_LEDGER/v1` sein und pro Wiederholung mindestens binden:

- Full Source Commit + Tree
- Executor-/Environment-Digest
- monotone Timestamps fuer Session create, lease issue, lease refresh, input admission, PTY write und state commit
- Session-/Lease-ID
- kontrollierte Lastklasse
- Ergebnis + Failure-Klasse

Empfohlener diskriminierender Versuch: 30 identische Baseline-Wiederholungen plus 30 unter kontrollierter Eventloop/CPU-Last, ohne Produktpatch vor der Messung.

## Promotion

- PTY Fix-Credit: 0
- Exact-Source Promotion-Credit: 0
- Whole Clay Machine: nicht behauptet
