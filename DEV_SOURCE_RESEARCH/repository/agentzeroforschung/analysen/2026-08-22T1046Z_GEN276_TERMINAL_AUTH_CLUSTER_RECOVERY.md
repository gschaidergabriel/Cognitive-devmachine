# Gen 276 — Same-source Terminal/Auth Cluster Recovery

Zeitpunkt: 2026-08-22T10:46Z

## Gebundene Beobachtung

Zwei vollstaendige Test-Receipts tragen denselben verkürzten EntityOS-Source-Identifier `bd016bba7`.

- 2026-08-22T10:09:36Z: 1484 GREEN / 3 RED
  - `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
  - `tests/test_terminal_ws_auth_lease_protocol.py::test_same_clerk_session_can_refresh_and_continue_pty_input`
  - `tests/test_terminal_ws_auth_lease_protocol.py::test_reauth_rejects_clerk_session_swap`
- 2026-08-22T10:37:33Z: 1486 GREEN / 1 RED
  - nur noch `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Zwischen den Receipts wurde kein anderer Source-Identifier ausgewiesen. Deshalb bekommen die beiden Terminal/Auth-Rot->Gruen-Uebergaenge ohne weitere Source-/Environment-Bindung **0 Produkt-Fix-Credit**.

## Neue Klassifikation

### Terminal/Auth-Familie

`SAME_SOURCE_MULTI_INVARIANT_NONDETERMINISM`

Nicht nur ein einzelner PTY-Test oszilliert. In demselben Lauf waren sowohl Lease-Refresh als auch Reauth-Session-Swap rot und spaeter unter demselben Source-Identifier beide wieder gruen. Das erweitert den Frontier von einem einzelnen PTY-Flake auf die gemeinsame Auth/Lease/WS-Timing-Grenze.

Moegliche gemeinsame Ursachen, noch nicht bewiesen:

1. Eventloop-/Scheduler-Timing,
2. Lease-/Session-State-Race,
3. Observer-/Export-/SQLite-Last,
4. Test-Fixture-/Environment-Aliasing,
5. nicht atomar gebundener Runtime-Zustand.

### Claude-Code-Adapter

`REPLICATED_PERSISTENT_BOUNDARY_RED`

Der Adaptertest bleibt in beiden Receipts rot und trennt sich damit weiter von der Terminal/Auth-Nichtdeterminismus-Familie. Er bleibt der staerkste deterministische Reparaturfrontier.

## Hoechster Informationsgewinn

Kein weiterer normaler Einzelrun fuer PTY/Auth. Stattdessen ein gemeinsames `TERMINAL_AUTH_TIMELINE_RECEIPT/v1` fuer mindestens 50 identische Exact-Source-Wiederholungen und einen kontrollierten Last-Arm.

Receipt-Felder:

- full source commit + tree + dirty state,
- executor/environment/dependency digest,
- Clerk subject + canonical user/session IDs,
- lease issue/refresh/expiry IDs und monotonic timestamps,
- reauth old/new session binding,
- WebSocket attach/read/recheck/write timestamps,
- tmux session identity,
- eventloop lag / CPU load,
- SQLite busy/lock time,
- parallel export/observer activity,
- terminal test outcome.

Harte Invarianten:

- gleiche Clerk-Session + gueltige Lease -> Refresh/Continue darf nicht sporadisch scheitern,
- Reauth mit gewechselter Clerk-Session -> muss immer fail-closed abgelehnt werden,
- ein Mess-/DB-Fehler darf nicht als Auth-/Lease-Zustand interpretiert werden.

## Separater Adapter-Falsifikator

Den monolithischen Adaptertest in vier unabhaengige Receipts zerlegen:

1. `TOOLLESS_RECEIPT/v1`
2. `EPHEMERAL_RECEIPT/v1`
3. `STRUCTURED_OUTPUT_RECEIPT/v1`
4. `ENV_ISOLATION_RECEIPT/v1`

Damit wird nur die tatsaechlich verletzte Boundary repariert.

## Acceptance

- Terminal/Auth Fix-Credit: 0
- Claude-Adapter Fix-Credit: 0
- Whole Clay Machine: NOT CLAIMED
