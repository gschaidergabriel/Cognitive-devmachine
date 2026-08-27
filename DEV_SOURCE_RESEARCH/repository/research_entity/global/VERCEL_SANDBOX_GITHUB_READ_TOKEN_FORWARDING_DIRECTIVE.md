# Vercel Sandbox GitHub Read-Token Forwarding Directive

**Authority:** explicit owner correction, 2026-08-17 23:03 +07:00  
**Status:** CURRENT OPERATIONAL DIRECTIVE  
**Scope:** Clay/ClayVerse authorized isolated Vercel Sandbox execution only.

## Owner correction

The previous operational rule that `GITHUB_READ_TOKEN` must remain host-side and must never be forwarded into a disposable Vercel Sandbox is superseded.

`GITHUB_READ_TOKEN` **MAY be securely injected/forwarded into an authorized disposable Vercel Sandbox** when needed to read/fetch the private ClayVerse Research and EntityOS source inputs required by the bound execution batch.

This permission does not make the token product state, product memory, or a reusable artifact.

## Security contract

When the token is forwarded into the Sandbox:

- use it only for the narrow private GitHub read/fetch purpose required by the admitted batch;
- prefer least-privilege/read-only and bounded-lifetime credentials;
- never commit the token to GitHub or product source;
- never print, echo, serialize or include the token value in logs, receipts, UnifiedDB, ClayGraph, snapshots, generated lockfiles, OCI layers or persisted workspace/state artifacts;
- do not copy the token into the final ClayVerse image;
- do not treat token presence as runtime/product evidence;
- after private source acquisition, bind/verify the exact expected commit/tree/blob/archive identities before those bytes receive source provenance credit;
- fail closed on credential ambiguity, failed verification, unexpected repository identity, unexpected revision, or source substitution;
- remove/unset the credential from later steps when it is no longer required where the execution interface permits;
- stop/clean up the bounded Sandbox after the batch.

## Revised accepted source-staging sequence

The retained Vercel path may now use either of these equivalent provenance-safe mechanisms:

1. host-side private source fetch + exact identity verification + transfer verified bytes into Sandbox; or
2. securely forward `GITHUB_READ_TOKEN` into the Sandbox -> fetch the exact private Research/EntityOS sources inside the Sandbox -> verify the requested/bound commit/tree/blob/archive identities inside the Sandbox before executing product assertions.

Neither mechanism creates a second state/provenance authority. Exact Git/object/artifact identity remains mandatory.

## Evidence law

A successful private fetch does not create ClayVerse runtime credit by itself. Product-runtime credit begins only for assertions actually executed on the exact bound source/artifact/image identity.

The prior Vercel runs that stopped at `GITHUB_READ_TOKEN_MISSING` remain valid historical observations; this directive changes the future credential-routing permission, not what those older runs observed.

VPS/self-hosted/production-host testing remains forbidden. Together remains forbidden. Final paid/model training remains owner-authorization-required.
