# DESIGN REFUTATION — self-signed relay grants were wrong

The first ASVB proxy allowed each relay actor to sign the scope of its own hop. That looked provenance-rich but was semantically unsound: a legitimate relay that had received a narrowed scope could issue itself a broader still-parent-compatible scope and produce a cryptographically valid chain. The signature proved who wrote the grant, not that the grantor was authorized to widen it.

The executable proxy exposed this before persistence.

## Correction
Every delegation edge is now sealed by its **parent/grantor**. A hop records `grantor -> actor`, narrowed scope, relay-content hash and previous-chain hash. The actor proves possession only when presenting the final request; it cannot rewrite its own incoming grant. Verification requires each hop scope to be a subset of the immediately preceding grant.

This is not proposed as a bespoke production cryptosystem. The synthetic HMAC model exists only to discriminate delegation semantics. Production realization should prefer established OAuth authorization-server/token-exchange and sender-constraining mechanisms, with ASVB limited to the ClayCode voice/provenance semantics above them.
