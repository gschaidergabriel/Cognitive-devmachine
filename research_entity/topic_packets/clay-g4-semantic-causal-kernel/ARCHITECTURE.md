# Architecture — G4 Semantic Causal Kernel Candidate

```text
Host OS / hardware
  ↓ platform adapter
Portable systems runtime
  scheduler · IPC · resource governor · sandbox · capability gateway · recovery
  ↓
Canonical event/provenance plane
  append/version/hash; truth and activation remain separate
  ↓ delta stream
Incremental semantic projection plane
  set-valued contextual state · role-aware n-ary relations · facets/indexes
  ↓ selection
Activation / dynamic assemblies
  ↓
Causal GWT episodes
  candidate → compete → ignite → broadcast → reconstruct → effect → outcome → reenter
  ↓
ClayCode/XENO typed proposal IR
  ↓
state/environment semantic validator
  ↓
external capability/effect gateway
  ↓
OS/tools/network/robots/services
  ↑ effect receipts/outcomes

Qwen-class 4B is a routed semantic transform operator, not canonical state and not execution authority.
Verification observes every boundary and supports replay, lesion, shuffle, delay, rescue and fault injection.
```

## Non-negotiable boundaries in this candidate

- storage implementation is not ontology;
- activation is not truth;
- model output is not authority;
- grammar validity is not semantic validity;
- GWT mechanism is not phenomenal-consciousness proof;
- hot projections are rebuildable derivatives, not unique history;
- coupling is adaptive and bounded by outcome/noise/propagation cost;
- platform-specific acceleration sits below stable semantic contracts.

## Competing implementations to retain

Canonical history: append log, temporal relational DB, embedded log-structured store.  
N-ary state: relation-node/property graph, hypergraph, temporal relational encoding.  
Active projections: in-process indexes, differential dataflow/materialized views, specialized caches.  
Runtime boundaries: modular single process, shared-memory services, conventional IPC, distributed replicas.  
Model runtime: llama.cpp, MLC, ExecuTorch or other platform adapters.

Selection must be by controlled complete-system effects, not architectural aesthetics.
