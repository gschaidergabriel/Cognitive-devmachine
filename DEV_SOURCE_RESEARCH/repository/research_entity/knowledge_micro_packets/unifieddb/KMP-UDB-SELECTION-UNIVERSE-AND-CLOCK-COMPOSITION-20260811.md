# KMP-UDB-SELECTION-UNIVERSE-AND-CLOCK-COMPOSITION-20260811

packet_id: `KMP-UDB-SELECTION-UNIVERSE-AND-CLOCK-COMPOSITION-20260811`
domains: `unifieddb, retrieval, selection_integrity, replay, replay_clock, emergent_retrieval`
epistemic_class: `ACCEPTED_TARGET_VPS_NEGATIVE_COMPOSITION_EVIDENCE`
status_hint: `OPEN_PRODUCT_COMPOSITION_WITH_TARGET_SCOPE_LAWS`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
trigger: `unifieddb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Parent target mechanisms

Two independently target-proven mechanisms remain supported within their declared scopes:

- PR #300 ReplayClock V1, target run `31437186827`: `PASS_REPLAY_CLOCK_V1_MECHANISM`;
- PR #301 SelectionReceipt V2, target run `31437317113`: `PASS_SELECTION_RECEIPT_V2_MECHANISM`.

This packet records two deeper scope/composition boundaries discovered only after those positive mechanisms existed.

## Delta S1 — SelectionReceipt identifies the presented universe; it does not prove retrieval completeness

Diagnostic PR #305:
`UnifiedDB diagnostic: SelectionReceipt does not prove candidate-universe completeness`

Head: `a86bd3b81367695ada59f1e567216d02cc0fc5ce`
Target run: `31438310214`
Result: `SUCCESS`
Artifact: `frank-selection-universe-scope-31438310214`
Artifact id: `9081844796`
Artifact digest: `sha256:8e5d0dff821f351391da6c2e7347b62b162f842928108b267cbf913947bc0d7e`

The test constructed two internally valid histories under the same semantic/query/operator context:

1. exact reference universe contained authentic best candidate `r_hidden`;
2. approximate universe silently omitted `r_hidden`, while every remaining candidate was individually authentic.

A fresh SelectionReceipt was minted for each universe. Both self-verified. They produced different receipt hashes and different selected refs.

Therefore:

`SelectionReceipt validity != candidate-generation completeness`.

SelectionReceipt proves the exact universe that was presented to ranking/filtering. It cannot by itself know that the upstream retriever missed a candidate it never received.

### Required retrieval composition

Exact route:
- `COMPLETE_BY_CONSTRUCTION` candidate-generation contract;
- exact generator/operator/source identity;
- SelectionReceipt binds that contract.

Approximate/emergent route:
- explicit RouteValidityCertificate / coverage scope;
- exact index/model/calibration/build identities;
- measured exact-reference shadow evidence;
- ShadowRiskSentinel state / quarantine state;
- never claim completeness merely because SelectionReceipt verifies.

This reconnects U11 Proof-Carrying Associative Memory Fabric findings with the target-proven SelectionReceipt mechanism. The approximate accelerator remains revocable and scope-bound.

## Delta S2 — stable read-time identity and replay-use provenance must be separate

Diagnostic PR #306:
`UnifiedDB diagnostic: split ReplayClock instant identity from replay-use provenance`

Head: `0aeb6cdbcc351ccd77ac1a77a1cafa4cb224f373`
Target run: `31438451690`
Result: `SUCCESS`
Artifact: `frank-replay-selection-composition-31438451690`
Artifact id: `9081898664`
Artifact digest: `sha256:ab5259c2e602ca5d6143ea5de3c99d70cd14f7a479846cec14cdcfad9e47ae6d`

The test composed the exact current #300 ReplayClock and #301 SelectionReceipt candidates.

ReplayClock deliberately creates:
- LIVE_CAPTURE use receipt;
- REPLAY_BOUND use receipt;
- same exact `as_of_utc_us`;
- different use/provenance receipt hashes because source class/ref differ.

SelectionReceipt V2 currently includes the clock receipt hash in its semantic context.

Result:
- same semantic root;
- same as-of instant;
- same query;
- same candidate universe;
- same ranking/scores;
- same selected refs;
- different clock-use provenance hash;
- therefore different SelectionReceipt hash.

A candidate `ClockInstantID = H(protocol, precision, as_of_utc_us)` was equal for LIVE and REPLAY uses. When that stable instant identity was bound in the semantic selection context, the semantic SelectionReceipt became byte-identical again.

Therefore:

`Clock instant identity != clock use/provenance identity`.

### Required replay composition

- `ClockInstantID`: stable semantic query-time identity; Query/Selection receipts bind this.
- `ClockUseReceipt`: LIVE_CAPTURE / REPLAY_BOUND execution provenance; changes per use and references the stable instant.
- semantic SelectionReceipt can reproduce exactly under replay;
- outer ReplayExecution/ReplayUse receipt records that the semantic query was executed again in replay mode and binds the replay-use receipt plus original semantic receipt.

This avoids collapsing two axes:
1. what semantic input time was used;
2. what execution event used that time.

## New proof law

A retrieval/replay result needs at least three independent identities:

`candidate-generation authority ∧ semantic selection identity ∧ replay-use provenance`.

No one digest should substitute for the other two.

For approximate retrieval:

`admitted approximate result := coverage/route validity ∧ exact presented-universe SelectionReceipt ∧ canonical rebind where required ∧ stable ReplayClock instant identity`.

A later replay adds a new provenance receipt without changing the semantic selection identity.

## Promotion boundary

Both negative target runs are **scope/composition evidence**, not product failures of #300/#301 and not product acceptance.

Open work:
- add stable ClockInstantID to ReplayClock product contract;
- integrate generator completeness/coverage authority into real retrieval;
- run exact-vs-approx shadow selection on real UnifiedDB/ClayGraph/emergent workloads;
- measure receipt overhead/coverage risk;
- preserve exact canonical fallback/quarantine;
- do not grant semantic truth/effect authority from either receipt alone.

No canonical state mutation, external effect, real-router superiority claim, whole Frank v0.1 acceptance, final training authorization or Frank/self.root Harness authority follows from this packet.
