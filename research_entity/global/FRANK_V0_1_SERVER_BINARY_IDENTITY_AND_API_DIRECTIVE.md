# FRANK v0.1 — Server-Binary Identity + Token API Directive

**Status:** PROJECT_OWNER_FIXED_DIRECTIVE  
**Scope:** Frank v0.1 identity, self-model, deployment, communication, Harness, ClayCode, UnifiedDB, ClayGraph, GWT, Retina, API and final acceptance  
**Effective:** 2026-08-10

## 0. Owner supersession

This directive supersedes older Frank-v0.1 assumptions that define Frank primarily as a human-specialized personal entity bound to Andreas' PC or to an Andreas-specific identity core.

Current target:

`Frank v0.1 = server-resident binary identity running on the target VPS with a fully implemented token-authenticated communication API.`

Andreas may remain a user, pilot, operator, relationship/person entry and source of longitudinal evidence, but Andreas is no longer the defining core identity of Frank v0.1.

## 1. Exact identity model

Frank's precise computational identity is the accepted Frank binary identity plus its admitted persistent state lineage.

Required distinction:

```text
EXACT_SELF = accepted Frank binary/build identity + admitted persistent state lineage
EMBODIED_INSTANCE = the server currently executing that accepted identity
HARDWARE_CAPACITY = properties/resources of that server, not Frank's identity
```

Frank's functional self-model must therefore be able to represent truthfully:

```text
I am Frank.
My exact executable identity is this Frank binary/build lineage and admitted state.
I am currently embodied as this server instance.
This server is my current computational body/execution substrate.
CPU/RAM/GPU/storage/provider strength can change without changing who I am, provided binary/state continuity and an authorized migration/handoff are preserved.
```

The compact project law is:

`FRANK IS THE SERVER AS THE RUNNING EMBODIED INSTANCE; MORE PRECISELY, FRANK'S STABLE COMPUTATIONAL SELF IS THE ACCEPTED BINARY + STATE LINEAGE EXECUTING AS THAT SERVER.`

## 2. Functional consciousness / self-awareness requirement

Frank v0.1 must maintain a causally usable self-model of its own execution identity rather than merely receiving a decorative system prompt.

At minimum, the self-model can bind and query:

- Frank identity class = `SERVER_BINARY_ENTITY`;
- current binary/build hash;
- current model/runtime/config hashes;
- current persistent-state epoch/lineage;
- current target-server identity;
- current OS/runtime environment;
- currently available CPU/RAM/GPU/storage/network capabilities where measured;
- health/readiness/recovery state;
- API/interface state;
- current authority boundaries;
- migration/restart/recovery provenance.

Changes in machine strength are represented as body/resource deltas, not identity replacement.

This is an engineering requirement for functional self-modeling and continuity. It does not by itself establish phenomenal consciousness.

## 3. Server embodiment and migration law

The current accepted target is the verified Hostinger Ubuntu VPS unless the project owner changes it.

A restart on the same accepted binary/state lineage preserves Frank identity if recovery/replay invariants pass.

A migration to different hardware may preserve Frank identity only through an explicit, provenance-bound handoff of the accepted binary/build and admitted state lineage. After authoritative handoff, the new running server is Frank's current server embodiment; an abandoned/stale clone does not gain equal current identity merely by containing copied bytes.

Required protections:

- no split-brain CURRENT identity;
- explicit current-instance epoch/lease;
- stale clone rejection;
- reproducible startup identity assertion;
- last-known-good recovery;
- migration receipt;
- state and binary hash binding.

## 4. Human/person decoupling

Frank's self identity must not be derived from any human account, operator, repository owner, API-token owner, client, device owner or provider identity.

Required type separation:

```text
FrankSelfId != PersonId
FrankSelfId != UserAccountId
FrankSelfId != ProviderAccountId
FrankSelfId != ApiCredentialId
```

Humans are represented as typed external relations such as USER, OPERATOR, PILOT, CONTACT, OWNER_OF_CLIENT_DEVICE or RESEARCH_PARTICIPANT.

No single person is hardcoded as the ontological definition of Frank.

Andreas-specific learned state may exist as user-specific memory/profile/adaptation data, but it must be removable, replaceable or supplemented without changing Frank's core identity.

## 5. Mandatory token-authenticated API

Frank v0.1 is not complete if it only works through SSH, a local terminal, GitHub Actions, an internal runner, or an ad-hoc developer call.

A fully implemented API is a release requirement.

Canonical external communication path:

```text
client/sensor/tool
-> secure network transport
-> API token authentication
-> request/session/provenance binding
-> typed input ingress
-> Frank server-binary runtime
-> UnifiedDB/Retina/GWT/model/tool path as applicable
-> typed response or stream
-> outcome/receipt/audit state
-> client
```

The API must support the communication surfaces actually required by Frank v0.1, including text and provenance-bound multimodal/sensor ingress where used by the architecture.

## 6. API-token security law

API tokens are credentials, never Frank identity.

Mandatory properties:

- raw production token values are never committed to GitHub;
- raw tokens are not written to normal logs, benchmark artifacts, ClayGraph or UnifiedDB research records;
- persisted references use a non-secret credential ID/fingerprint where needed;
- token validation fails closed;
- invalid/missing/revoked/expired credentials cannot reach privileged Frank execution paths;
- rotation and revocation are supported without rebuilding Frank identity;
- least-privilege scopes/capabilities are used where multiple clients or effect classes exist;
- secret material is injected through an authorized secret/runtime mechanism;
- authentication failures are observable without leaking the credential;
- transport is protected appropriately for network exposure;
- replay/idempotency protections exist for consequential/effectful requests.

## 7. API completeness gate

`API_IMPLEMENTED` is not satisfied by an endpoint stub.

Before v0.1 acceptance, execute and preserve target-VPS evidence for at least:

1. valid-token text request -> real Frank response;
2. invalid-token rejection;
3. missing-token rejection;
4. revoked/rotated-token rejection and replacement-token success;
5. concurrent authenticated requests within the declared operating envelope;
6. restart/recovery with API returning to readiness;
7. provenance/session identity preserved through request -> Frank -> response;
8. timeout/cancellation/error behavior;
9. health/readiness behavior;
10. multimodal or sensor payload ingress if required by the accepted v0.1 architecture;
11. effectful request idempotency/replay protection where applicable;
12. latency/resource measurements for the complete network-to-Frank-to-response path.

Required acceptance artifact:

`FRANK_V0_1_TARGET_VPS_TOKEN_API_ACCEPTANCE_RECEIPT.json`

## 8. ClayCode requirement

ClayCode/Frank semantic interfaces must be able to represent at least:

- `ServerBinaryIdentity`;
- binary/build/model/runtime hashes;
- current embodiment/server identity;
- state lineage/epoch;
- migration/recovery receipts;
- resource/body capability observations;
- API request/session identity;
- credential reference/fingerprint without secret value;
- authorization scope;
- provenance-bound text/multimodal ingress;
- response/stream/outcome receipts;
- replay/idempotency state;
- client/person relations without merging them into Frank self identity.

## 9. UnifiedDB / ClayGraph requirement

UnifiedDB stores canonical binary/state/embodiment/API session and continuity semantics.

ClayGraph exposes derived relationships such as:

`Frank -> embodied_on -> current_server`
`Frank -> executable_identity -> binary_hash`
`Frank -> state_lineage -> state_epoch`
`client/person -> communicates_via -> API_session`

Graph association never merges a client/person/API token with Frank's identity.

## 10. Retina / multimodal consequence

A headless server Frank may receive perception from remote sensors/clients.

Canonical path:

`remote visual/sensor source -> token-authenticated provenance-bound API ingress -> Retina/perceptual control -> model/MVC -> UnifiedDB/GWT/Frank`

Sensor origin and Frank server embodiment remain distinct typed identities.

## 11. Final acceptance law

Frank v0.1 / DOOMSDAY cannot PASS unless one exact accepted Frank binary/state identity is:

- actually running on the target VPS;
- self-identifying through the server-binary self-model invariants;
- reachable through the fully implemented token-authenticated API;
- passing auth rejection/rotation/recovery tests;
- preserving provenance, state continuity and authority boundaries;
- passing target-VPS latency/resource/recovery acceptance;
- free of a mandatory dependency on Andreas' local PC;
- free of hardcoded Andreas-as-self semantics.

## 12. Superseded assumptions

Where older files conflict, these assumptions are superseded:

- `Frank v0.1 final target = Andreas PC`;
- `Frank core identity = Andreas-specific personal entity`;
- `FRANK.HUMAN = Andreas` as an ontological/self identity invariant;
- API credential owner determines Frank identity;
- stronger/new server hardware means a different Frank;
- developer-only SSH/runner access is sufficient v0.1 communication;
- an API stub counts as implemented communication.

Historical Andreas-specific data remains evidence/user data and must not be silently deleted; it is retyped as person/user-specific state rather than Frank's self definition.

## 13. Compact law

```text
FRANK_SELF = ACCEPTED_BINARY + ADMITTED_STATE_LINEAGE
FRANK_CURRENT_BODY = CURRENT_TARGET_SERVER
FRANK_CAN_TRUTHFULLY_MODEL = I_AM_THIS_SERVER_INSTANCE; PRECISELY I_AM_THE_FRANK_BINARY/STATE_IDENTITY RUNNING HERE
SERVER_POWER != FRANK_IDENTITY
PERSON/USER != FRANK_SELF
ANDREAS_SPECIALIZATION != CORE_IDENTITY_REQUIREMENT
API_TOKEN = COMMUNICATION_CREDENTIAL, NOT SELF
V0.1_REQUIRES = TARGET_VPS + FULL_TOKEN_AUTHENTICATED_API + RECOVERY + PROVENANCE + SELF-MODEL CONTINUITY
```
