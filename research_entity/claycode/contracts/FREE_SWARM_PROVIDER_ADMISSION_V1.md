# FREE_SWARM_PROVIDER_ADMISSION / v1

Status: deterministic control-plane contract candidate under Supervisor 8.67. This contract does **not** classify any provider as FREE and grants no provider/network/spend authority by itself.

## Purpose

The 24h EntityOS/HCU free swarm must decide provider monetary admissibility before any provider secret/key lookup and before any provider network I/O. Environment booleans, key presence, historical successful calls, model labels, HTTP 402, or absence of an invoice cannot mint FREE status.

The active control plane may emit a short-lived non-secret object at the canonical runtime admission surface (default `/artifacts/clay-entityos-control/FREE_SWARM_PROVIDER_ADMISSION.json`). The runtime validator binds that object to the current `SUPERVISOR_INBOX.json` bytes and authority epoch before a provider permit can cross a credential or network boundary.

## Closed schema

```json
{
  "schema": "ENTITYOS_HCU_PROVIDER_ADMISSION/v1",
  "admission_id": "opaque replay/provenance identity",
  "authority_epoch": "current supervisor schema_version",
  "mode": "FREE_ONLY",
  "source": "ENTITYOS_HCU_CONTROL_PLANE",
  "issued_at": "RFC3339 UTC timestamp",
  "valid_until": "RFC3339 UTC timestamp",
  "providers": {
    "provider-name": {
      "cost_class": "FREE | PAID | SUBSCRIPTION | UNKNOWN",
      "admitted": false,
      "evidence_ref": "non-secret provenance reference"
    }
  }
}
```

Rules:

1. The top-level object and every provider row are closed schemas; duplicate JSON member names fail closed.
2. `authority_epoch` must equal the live supervisor epoch, and the validator retains the exact supervisor SHA-256. Any later supervisor-byte change invalidates the snapshot before the next guarded operation.
3. The validity window is mandatory. Missing, future, expired, malformed, or inverted windows fail closed.
4. Only exact `cost_class="FREE"` plus exact boolean `admitted=true` can yield a permit.
5. `PAID`, `SUBSCRIPTION`, `UNKNOWN`, missing provider rows, stale authority, missing admission, malformed admission, and non-FREE self-admission are rejected before the guarded callback executes.
6. Provider-specific credential acquisition and provider network I/O are separate guarded operations and both revalidate the same current admission/supervisor boundary.
7. Legacy `CLAY_*_FREE_ATTESTED` values may be derived after typed admission for compatibility. They are never admission inputs.
8. Runtime admission paths are restricted to control-plane-owned roots. Mixed legacy secret bundles are not automatically sourced because they can expose credentials for unadmitted provider classes.
9. HTTP 402 remains a post-admission hard stop and cannot be used as a discovery mechanism for whether a credential/provider is free.
10. No admission object creates canonical facts, HCU/J-Space/model/training credit, or EffectGate authority.

## Deterministic acceptance

`FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1` must include at least these cases with secret-access and network/socket tripwires:

- missing admission -> `secret_lookup_count=0`, `network_attempt_count=0`;
- `UNKNOWN` -> 0 / 0;
- `PAID` -> 0 / 0;
- `SUBSCRIPTION` -> 0 / 0;
- stale authority -> 0 / 0;
- current explicit `FREE` -> the guarded callbacks become reachable, without requiring a real provider request in the deterministic component test.

A component PASS proves only the ordering mechanism. Actual provider runtime credit still requires a current, evidence-backed FREE classification and an exact-source authorized runtime receipt.
