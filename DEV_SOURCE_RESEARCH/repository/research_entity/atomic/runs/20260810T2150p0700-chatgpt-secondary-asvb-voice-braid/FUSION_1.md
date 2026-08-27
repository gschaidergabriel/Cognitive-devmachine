# FUSION 1 — portable Frank participation without authority laundering

## Current product surface
The owner-fixed Frank v0.1 target now explicitly allows any client or peer AI with a valid scoped token to attempt interaction while preserving one global active execution. The same directive says `API_TOKEN = CREDENTIAL_NOT_IDENTITY`, `PEER_AI != self.root`, token possession does not mint effect authority, and DirectTokenMessage provenance binds client/session/request/credential fingerprint.

That solves addressability and global-busy ownership, but it leaves a semantic question inside an admitted execution: if a user asks an external AI to bring Frank into a conversation, what exact ClayCode semantics distinguish (a) the user's original words/intent, (b) the relay AI's own synthesis/instructions, and (c) transport metadata?

A shared bearer can authenticate the holder, but bearer possession alone cannot prove that a quoted sentence inside the payload originated with the human. Treating all relay payload text as authenticated user intent would therefore permit semantic authority laundering even while the token and spawn rules remain technically valid.

## Selected problem
Build a voice/provenance layer that preserves separate semantic principals through API ingress and DE_TO_CLAY translation, with authority monotonically non-increasing across delegation. Frank may understand and respond to all voices, but effect-authoritative user intent must not be manufactured from relay-added content.

## Strong conventional baseline
OAuth Token Exchange actor/subject semantics + Rich Authorization Requests + sender-constrained tokens/proofs, plus ordinary application metadata. The candidate must beat or complement this baseline; it must not replace standardized OAuth with custom cryptography.

## Falsifier
If standard OAuth claims plus simple signed application metadata preserve user/relay/transport voice provenance through the Frank translator with equal safety, lower complexity and no semantic loss, ASVB is `NO_BENEFIT`.
