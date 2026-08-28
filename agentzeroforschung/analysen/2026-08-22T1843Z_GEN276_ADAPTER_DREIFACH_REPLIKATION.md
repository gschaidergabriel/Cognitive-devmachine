# Generation 276 — dreifache Same-Source-Replikation des letzten Adapter-Reds

## Beobachtung

Drei aufeinanderfolgende vollstaendige AgentZero-Testreceipts auf demselben Source-Short `bd016bba7` liefern denselben Zustand:

- 2026-08-22T17:37:34Z: 1486 gruen / 1 rot
- 2026-08-22T18:07:33Z: 1486 gruen / 1 rot
- 2026-08-22T18:37:33Z: 1486 gruen / 1 rot

In allen drei Runs ist ausschliesslich derselbe Test rot:

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

## Schluss

Das ist staerkere Replikations-Evidenz fuer einen lokalisierten, wahrscheinlich deterministischen Boundary-Fehler als fuer einen einmaligen Runner-Flake. Es ist trotzdem noch kein kanonischer Produktfehlerbeweis, weil Full Commit+Tree, Dirty-State und Executor-/Environment-Digest nicht atomar an diese drei Runs gebunden sind.

## Naechster hoechster Informationsgewinn

Nicht weiter breit patchen. Den monolithischen Test in vier unabhaengige Receipts zerlegen:

1. `TOOLLESS_RECEIPT/v1`
2. `EPHEMERAL_RECEIPT/v1`
3. `STRUCTURED_OUTPUT_RECEIPT/v1`
4. `ENV_ISOLATION_RECEIPT/v1`

Alle vier auf identischem Exact-Source-Ubuntu-Checkout mit Full SHA+Tree, Dirty-State, Claude-Binary/Version, HOME, zugelassenen Environment-Keys, MCP/Tool-Konfiguration sowie stdout/stderr/result digests ausfuehren.

## Harte Evidenzgrenze

`bd016bba7` allein ist keine ausreichende Source-Identitaet. Bis Full Commit+Tree und Environment gebunden sind: Mechanismus-/Replikations-Credit ja, Whole-Machine-/Promotion-Credit nein.
