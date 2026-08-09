# 666 PF tree seg01 modified shard m064-m096

Status: COMPLETE_WITH_OVERLAP_DEDUP

Attempted scope: `modified_paths[64..96]`, 33 immutable-ref blob identities. All 33 were materialized, zero missing.

During integration a prior peer lease for `m064..m095` was discovered. Its claim commit (`6a187756...`) predates this worker's claim. Therefore:

- `m064..m095`: 32 identities retained as corroborative provenance only, parent decrement = 0
- `m096`: 1 new unique identity, parent decrement = 1
- full attempted ledger SHA256: `f7b607add7e026a4cebfaa83ae7fc8a15a5c1ae8ed65e219a115b7c41b5bd642`
- counting singleton ledger SHA256: `b1d82459b68f8c3ec7b0f3cf6beff8c4456dbeb6b1009b89b157113b35477a33`
- parent seg01 after integration: 168/232 materialized, 64 remaining (`m000..m063`, peer-owned)

Coordination negative result: exact-string shard searches are insufficient for interval leases. Future selection must test numeric interval intersection or use structured lease metadata.

No semantic credit and no earned-work hours added.
