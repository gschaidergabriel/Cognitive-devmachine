# FRANK Clay-Native Architecture Contract

**Status:** PROJECT-OWNER ARCHITECTURE DIRECTIVE — NOT A RESEARCH HYPOTHESIS  
**Applies to:** FRANK architecture research, Clay, ClayCode, ClayGraph, GWT, Hyperposition, Emergence research that feeds FRANK  
**Owner directive recorded:** 2026-08-08

## Fixed design premise

The target FRANK system is Clay-native end to end.

The abliterated Qwen-class 4B is to be full-model adapted so that Clay is its native generated and deliberative symbolic language. Research must not repeatedly reopen the question of whether FRANK should speak/think Clay. That decision is fixed. Research must instead optimize, falsify implementation subclaims, measure consequences, expose failure modes, and refine how the fixed architecture should be realized.

The target semantic stack is:

- model-facing thought/deliberative symbols: Clay;
- generated internal and external machine-facing language: Clay, with human-language projections only at explicit I/O boundaries;
- architecture source: Clay/ClayCode semantic IR;
- persistent semantic memory: ClayGraph/Clay;
- episodic, self, goal, world, policy, uncertainty and provenance representations: Clay-native typed objects;
- scalar/vector/tensor-facing semantic labels, coordinates and typed value schemas: Clay-native semantics;
- GWT candidates, Assemblies, WorkspaceEpisodes and re-entry contracts: Clay-native;
- Hyperposition relation instances/topologies: Clay-native;
- inter-module semantic communication: Clay-native;
- capability/effect proposals and receipts: Clay-native typed contracts;
- migration/observability/replay descriptions: Clay-native canonical semantics.

Neural hidden activations, KV tensors, numeric arrays, machine instructions and storage encodings remain physical representations. They do not become literal text. They MUST, where they cross a semantic boundary, be bound to Clay-native typed meaning/provenance rather than treated as an alternative semantic language.

## Sole intentional semantic foreign body: Needle

Needle is the one intentionally retained non-Clay subsystem.

Needle remains a fast pre-model classifier/router and should be used fully rather than reimplemented merely for Clay purity. Its output is bridged into Clay as a typed, provenance-bound observation/proposal.

Needle does NOT mint execution authority. Authorization/effect validity remains a deterministic runtime invariant. The authority semantics themselves belong to the Clay architecture; compiled/trusted runtime enforcement is allowed and required.

## No hidden second architecture

There must not be a second independent semantic architecture in Python/Rust/JSON/SQL beside Clay. Conventional code, databases and kernels may implement or cache compiled projections of Clay contracts, but Clay/ClayCode is the semantic source of truth for the target architecture. Derived representations must remain reconstructible/auditable against Clay semantics.

## Research rule

The following are valid research questions:

- how full-model Clay internalization changes reasoning, tokenization, forgetting, transfer and controllability;
- what Clay vocabulary/tokenizer/training curriculum minimizes loss and preserves useful pretrained capabilities;
- how ClayGraph memory interacts with a Clay-native model;
- whether same-language memory/model/architecture reduces reconstruction cost or increases correlation/error cascades;
- how to type and protect values/vectors/tensors in Clay;
- which Clay representations best preserve n-ary relations, temporal validity, uncertainty, causal basis and authority;
- how to compile deterministic semantics before model inference;
- how to prevent homoiconic code/data, memory/prompt, authority/proposal and truth/activation confusion;
- how to measure GWT/emergence causally when all semantic stages share one language;
- how to migrate existing stores reversibly into Clay-native semantics;
- how to retain cross-platform/low-latency execution while Clay remains the semantic source.

The following is NOT a research hypothesis to reopen:

> whether the target FRANK should be Clay-native across thought, language, memory, values/vectors, architecture and internal semantic communication.

That is the fixed target architecture.
