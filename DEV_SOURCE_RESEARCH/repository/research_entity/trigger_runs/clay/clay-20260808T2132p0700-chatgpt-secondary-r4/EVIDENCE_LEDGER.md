# Clay G12 External Evidence Ledger

run_id: `clay-20260808T2132p0700-chatgpt-secondary-r4`

Evidence classes are preserved. Branch reuse/shared ancestry is not independent replication.

## Independent scholarly / primary evidence

### Synapse — Findings ACL 2026
Source: https://aclanthology.org/2026.findings-acl.1108/
Class: peer-reviewed conference findings paper.
Relevant mechanism: dynamic graph memory with spreading activation, lateral inhibition, temporal decay and hybrid retrieval.
Transfer: independently supports the plausibility of ClayGraph-style activation/inhibition/decay as a memory mechanism.
Boundary: does not validate FRANK, GWT ignition, authority, C3F/CACC or between-call Clay continuity.

### MAGMA — ACL 2026
Source: https://aclanthology.org/2026.acl-long.1709/
Class: peer-reviewed ACL long paper.
Relevant mechanism: orthogonal semantic, temporal, causal and entity graphs with policy-guided traversal.
Transfer: supports keeping relation/time/causal identity explicit instead of flattening all memory into one similarity space.
Boundary: benchmark success is not evidence for FRANK's exact topology or activation mechanism.

### Interlat — ACL 2026
Source: https://aclanthology.org/2026.acl-long.1248/
Class: peer-reviewed ACL long paper.
Relevant mechanism: direct hidden-state inter-agent communication and learned compression; reports task gains and up to 24x inference acceleration in its setting.
Transfer: establishes latent communication as technically feasible and motivates MRSC/P3 experiments.
Boundary: latent state is not canonical truth/authority and results do not imply that latent rails are universally superior.

### Latent Communication Between Language Model Agents — 2026 preprint
Source: https://arxiv.org/abs/2607.14103
Class: preprint.
Relevant negative evidence: latent/SAE channels retained more probe-visible features than text, but task-level latent communication never exceeded text in reported experiments; latent augmentation added no benefit.
Transfer: directly supports G12's separation `information retention != cognitive utility`.
Boundary: preprint; task/model family specific.

### Partial Effective Information Decomposition — 2026 preprint
Source: https://arxiv.org/abs/2605.03267
Class: preprint.
Relevant mechanism: intervention-grounded decomposition of multivariate causal influence into unique/synergistic components.
Transfer: useful candidate statistic for E-CERT2 only after exact intervention identity and functional effects exist.
Boundary: does not itself establish emergence in FRANK.

### Securing Agents With Tracked Capabilities — ACM CAIS 2026
Source: https://doi.org/10.1145/3786335.3813127
Class: peer-reviewed ACM conference paper; artifact/reproduction badges reported by ACM.
Relevant mechanism: tracked capabilities/type-based safety harness around agent effects and resources.
Transfer: independently supports an external deterministic capability/effect boundary rather than unrestricted model tool authority.
Boundary: Scala/capture checking is an implementation example, not a required FRANK technology.

### Apache Arrow C Data Interface
Source: https://arrow.apache.org/docs/format/CDataInterface.html
Class: authoritative technical specification/documentation.
Relevant mechanism: zero-copy sharing between runtimes/components in the same process.
Critical boundary: sharing between distinct processes and persistence are explicit non-goals; Arrow IPC or another process transport is required.
Transfer: CORF must keep same-process ABI and cross-process IPC as separate physical contracts.

### Qwen3-4B official configuration
Source: https://huggingface.co/Qwen/Qwen3-4B/blob/main/config.json
Class: authoritative model configuration.
Observed relevant fields: 36 hidden layers, 8 key/value heads, head_dim 128, max_position_embeddings 40960.
Transfer: used only for memory/context arithmetic and target identity. No hosted provider used in this run exposes an executable exact Qwen3-4B route.

## Current implementation evidence

### Feldera / DBSP
Source: https://github.com/feldera/feldera
Class: implementation/source evidence.
Relevant mechanism: incremental view maintenance/dataflow from deltas rather than recomputing complete history.
Transfer: supports feasibility of incremental derived-state maintenance; not a FRANK performance result.

## RAE internal evidence consumed

- Clay G11 / MOSAIC: `clay-20260808T2033p0700-chatgpt-secondary-r3`
- FRANK C7 / CORF: `20260808T2051p0700-chatgpt-secondary-r3`
- GWT R4 / CSOC: `gwt-20260808T1721p0700-chatgpt-secondary`
- Emergenz / E-CERT2: `emergenz-20260808T1756p0700-chatgpt-secondary`
- ClayCode CC12 / TCQS: `claycode-20260808T2104p0700-chatgpt-secondary-r3`
- Hyperposition H4 / HYP-RC4: `hyperposition-20260808T1806p0700-chatgpt-secondary-r2`
- ClayGraph G1d HOLD: `claygraph-20260808T1712p0700-chatgpt-secondary-r2`
- UnifiedDB U1 / UD-RC1: `unifieddb-20260808T2044p0700-chatgpt-secondary-r2`
- Fusion F5 / C3F: `fusion-20260808T2114p0700-chatgpt-secondary-r2`

These branches are one shared research lineage. Repetition among them is not replication.
