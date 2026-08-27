# H6 CARTS -> ClayCode

**Source:** Hyperposition H6 `HYP-RC6 CARTS`  
**Effect:** SUPPORT + REVISE

CC13/MCAAT is strengthened. Add topology-specific types:
- `TopologyCandidate` — versioned/non-live;
- `TopologyIntent` — non-authoritative live-switch proposal;
- `TopologyPermit` — opaque host-minted capability;
- `LiveTopologyRef` — current active topology identity;
- `CreditScope<ITEM|PATH|ASSEMBLY|ROUTE|UNKNOWN>`.

Constructive repoint remains consequential. Destruction-free syntax and recoverability do not authorize a new live topology. Compiler/runtime checks should prevent credit/salience/workspace values from implicitly casting into live topology or authority.
