# Lane D External Evidence Ledger — Intent Adequacy / Noninterference / Commit Identity

Actor: `chatgpt-secondary-sol-02` · OpenAI · GPT-5.6 Sol  
Candidate: `CC-LANE-D-IARC-1`  
Status: evidence ledger only; no canonical promotion.

Evidence classes are deliberately separated. External convergence supports mechanism classes, not the exact ClayCode implementation or the synthetic effect sizes measured by Lane D.

## Standards / authoritative systems documentation

### IETF RFC 9396 — OAuth 2.0 Rich Authorization Requests
Source class: Internet Standards Track / IETF consensus.  
URL: https://www.rfc-editor.org/rfc/rfc9396.html

Relevant transfer:
- coarse `scope` is explicitly insufficient for fine-grained cases such as a particular payment amount/merchant or read-directory/write-file distinction;
- `authorization_details` carries structured action/resource details used for consent and enforcement;
- user consent must be presented against the merged requested requirements;
- Section 12 warns that authorization details can be tampered/swapped and recommends integrity protection.

ClayCode implication: high-impact consent should bind a canonical structured `ActionManifest`, not a generic confirmation bit. This does not establish that users understand the manifest.

### Linux `openat2(2)` / pathname resolution
Source class: OS/kernel documentation.  
URLs:
- https://man7.org/linux/man-pages/man2/openat2.2.html
- https://www.kernel.org/doc/html/v5.12/filesystems/path-lookup.html

Relevant transfer:
- Linux exposes resolution restrictions specifically to protect trusted programs resolving untrusted paths;
- `RESOLVE_BENEATH`, `RESOLVE_IN_ROOT`, `RESOLVE_NO_SYMLINKS`, `RESOLVE_NO_MAGICLINKS` constrain pathname resolution;
- kernel documentation explicitly discusses race/attack scenarios involving changing path components.

ClayCode implication: semantic target strings and lexical prefix checks are not a sufficient resource-identity authority boundary. `ResourceWitness` should lower to OS/API-specific stable handles, constrained resolution, or commit-time identity verification.

### CHERI capability architecture documentation
Source class: architecture/security documentation.  
URL: https://www.cl.cam.ac.uk/research/security/ctsrd/cheri/cheri-faq.html

Relevant transfer: CHERI protects capability provenance/nonforgeability and monotonic bounds/permission restriction. This independently anchors the general authority-attenuation class, not ClayCode's exact envelope.

## Peer-reviewed conference evidence

### Task Shield — ACL 2025
URL: https://aclanthology.org/2025.acl-long.1435/

Finding: reframes indirect prompt-injection defense around task alignment and checks whether instructions/tool calls contribute to the user objective. Reported AgentDojo GPT-4o result: 2.07% attack success with 69.79% task utility.

Transfer: `capability-valid != task-justified` is a meaningful independent distinction. The reported verifier is not a deterministic proof of intent adequacy.

### VIGIL — ACL 2026
URL: https://aclanthology.org/2026.acl-long.443/

Finding: verify-before-commit with intent-grounded verification against tool-stream injection; reports >22% attack-success reduction and >2x utility under attack versus static baselines on SIREN.

Transfer: speculation/reasoning and commit authority should remain separate. Model verification can be an additive signal, but this does not prove it can replace deterministic authorization/flow checks.

## Research papers / preprints / current research

### CaMeL — Defeating Prompt Injections by Design
URL: https://arxiv.org/abs/2503.18813

Finding: extracts trusted control/data flow and prevents untrusted data from affecting program flow; capabilities restrict unauthorized flows. Reports 67% of AgentDojo tasks solved with its security property.

Transfer: strongest independent anchor for separating trusted control from untrusted data instead of asking one generative channel to both reason and enforce authority.

### Fides — Securing AI Agents with Information-Flow Control
URL: https://openreview.net/forum?id=2FkswFYju5

Finding: formal information-flow model, confidentiality/integrity labels and deterministic policies, including selective reveal/hide primitives.

Transfer: supports typed release/declassification as a mechanism class. Exact mapping to ClayCode `TypedRelease` remains open.

### AgentSecBench — 2026
URL: https://arxiv.org/abs/2605.26269

Finding: formalizes instruction integrity, retrieval confidentiality and capability integrity under intent-to-execution noninterference with permitted leakage; distinguishes prompt annotations from enforcing projections.

Transfer: directly motivates a ClayCode property test where untrusted observations outside authorized projection/release slots cannot affect protected effect fields or authority.

### ARGUS — 2026
URL: https://arxiv.org/abs/2605.03378

Finding: constructs influence provenance graphs and audits whether decisions are justified by trustworthy evidence; reports 3.8% ASR and 87.5% utility in its benchmark.

Transfer: motivates explicit influence/provenance receipts for `IntentAdmissionReceipt`; reported numbers do not transfer to FRANK.

### Context-to-Execution Integrity (CXI) — 2026
URL: https://arxiv.org/abs/2607.06000

Finding: protected sink fields, typed releases, opaque data slots, and deterministic gating that binds field, exact-effect and invocation authority to one action manifest. Reported finite evaluation includes 720 AgentDojo live episodes and 400 repository episodes.

Transfer: highly aligned external analogue to Lane D's protected-field `TypedRelease` + exact manifest concept. It is not independent validation of ClayCode implementation details.

### Intent-Governed Tool Authorization / IGAC — 2026
URL: https://arxiv.org/abs/2606.22916

Finding: argues static credential authorization is necessary but insufficient because an otherwise permitted tool call can be unjustified by the current user request. Intent is monotone narrowing, never authority expansion.

Transfer: directly supports the dual-gate distinction: user/task intent narrows the currently available capability authority.

### Temporary Authority, Permanent Effects — 2026
URL: https://arxiv.org/abs/2607.10487

Finding: stale authority evidence can still lead to durable effects unless authority/witness validity is rebound at commit. Endpoint success is distinct from authorized commit.

Transfer: supports Lane C/C9/sol-03 release-time freshness and Lane D's requirement that intent/resource witnesses remain bound to commit.

### Durable authorization / CapLease — 2026
URL: https://arxiv.org/abs/2608.01710

Finding: fresh token IDs can still semantically replay one user authorization through retries/replans; durable monotone authorization state and transactional issue/prepare/commit are required to bound re-execution.

Transfer: independently supports `authority_reservation_id` plus durable authorization-instance consumption rather than token-ID uniqueness alone.

## Evidence synthesis

The external literature converges on five separations that are also emerging independently inside the RAE mesh:

1. data/instructions observed by the model are not automatically trusted control;
2. static capability permission is not equivalent to current user/task justification;
3. authorization should bind structured effect details rather than only coarse scope;
4. authority/witnesses must remain current and bound through commit;
5. resource identity and authorization identity must survive representation, alias, retry and concurrency boundaries.

This convergence raises the priority of testing IARC. It does **not** count as replication of Lane-D experiments, does not establish a production-safe ClayCode runtime, and does not justify canonical promotion without real target-model/runtime tests.
