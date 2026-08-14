# Cactus Runtime Delta — Needle-specific differential findings

Run: `harness-20260809T1854p0700-chatgpt-secondary-needle-fusion`
Actor: `chatgpt-secondary` / Research Entity temporary worker
Date: 2026-08-09
Scope: current `cactus-compute/cactus` Needle execution path; no claim that Frank currently ships this exact runtime.

## Why this matters

Needle's README describes Cactus as its production runtime. The H1 reference boundary therefore cannot infer production behavior from the Python/JAX path alone. This delta cross-reads and falsifies assumptions across the current Cactus C++ implementation.

## 1. Cactus fixes one Python/JAX schema problem — but only partially

Current `complete.cpp` intentionally converts ordinary JSON Schema into the flat parameter map Needle was trained on:

`ToolFunction(JSON Schema) -> extract properties/required -> serialize_needle_tools(flat Needle map)`

Therefore the Python/JAX `parameters.properties` mismatch is **not automatically a Cactus bug**.

However, the Cactus helper extraction is string-pattern-based rather than a full JSON-AST transformation:

- object field lookup searches exact `"properties":`;
- parameter type extraction searches exact `"type":"`;
- parameter description extraction searches exact `"description":"`.

Sandbox reproduction of these exact helper rules:

- compact schema `"type":"integer"` -> integer preserved;
- ordinary JSON whitespace `"type": "integer"` -> property remains but type falls back to string;
- ordinary `"description": "How many"` -> description lost;
- whitespace before colon `"properties" : {...}` -> properties extraction fails.

Historical Frank registry relevance: the frozen 2026-08-04 active fixture uses string arguments and no parameter descriptions, so this is not promoted as a proven current Frank failure. It is a general Cactus/H1 conformance counterexample for future typed tools and noncanonical serializers.

## 2. Current Cactus `parse_tools_json` has escaping/brace fragility

Current `utils.h::parse_tools_json()` is a manual string scanner.

Executable source-mirror probes found:

- an escaped quote in a tool description can terminate the parsed description early;
- schema object extraction counts raw `{`/`}` bytes without string-state tracking, so unmatched braces inside schema string values can distort the extracted schema boundary.

The current historical Frank registry contains no quote/brace tool descriptions, so this remains a forward-compatibility/fuzz requirement rather than a present Frank failure.

H1 response: canonicalize and hash the exact outbound toolset before runtime, keep a runtime-version profile, and independently validate returned calls.

## 3. Needle constraint whitespace weakness exists in Cactus too

Current `cactus-engine/src/constraints.cpp` has a distinct C++ `ToolCallConstrainer`, but its Needle branch recognizes the same compact markers:

- `"name":"`
- `"arguments":{`
- argument keys beginning only after compact `{"` or `,"`.

Therefore the earlier legal-JSON-whitespace counterexample is not merely a Python implementation artifact. The Cactus Needle constrainer can remain in FREE mode for legal outputs using spaces/tabs/newlines at those marker boundaries.

This is not evidence that the trained Needle usually emits whitespace; training examples use compact JSON. It is evidence that the constrainer is a partial format-specific guard, not a complete JSON security grammar.

## 4. Needle required-argument enforcement is not intrinsic to the Cactus Needle constrainer

`ToolCallConstrainer` contains machinery for:

- emitted keys;
- remaining-key trie;
- required-satisfied state.

But the current Cactus source uses that machinery in the Gemma branch. In the Needle branch, closing an argument key does not populate the emitted-key set or drive `required_satisfied()` as a generation constraint.

`complete.cpp` contains a later `function_calls_missing_required()` check, but the inspected handoff decision wires `invalid_local_tool_call` to the cloud-eligible + deferred-probe path. H1 must therefore not rely on Cactus' Needle constrainer or cloud handoff to enforce required arguments for local acceptance.

The Research Entity's strict post-validator independently enforces missing/unknown/type-invalid arguments for every accepted Needle decision.

## 5. Cactus syntax sanitizer is weaker than the H1 admissibility boundary

`utils.h::is_valid_json()` validates JSON syntax, and `sanitize_function_calls()` removes syntactically invalid calls. Its object parser does not maintain a duplicate-key set.

Therefore syntactically valid JSON with duplicate keys is not rejected merely by this sanitizer. H1 deliberately rejects duplicate keys before semantic validation to avoid parser-differential/last-wins ambiguity.

## 6. Cactus Tool RAG is a concrete candidate, not yet an accepted Frank component

Current `rag.cpp::select_relevant_tools()`:

- embeds `tool.name + " " + tool.description`;
- embeds the query;
- computes cosine similarity;
- computes BM25 lexical ranking;
- fuses embedding/BM25 ranks by RRF;
- weights embedding 0.8 and BM25 0.2;
- returns requested top-k.

On embedding/tokenizer failure it returns all tools.

This makes Cactus Tool RAG a strong executable candidate for Franks 51-tool context-pressure problem, but the fail-open-to-all behavior is incompatible with treating retrieval failure as permission to overflow a frozen Needle encoder budget. Frank's outer preflight must re-check the complete selected toolset and escalate/fallback when it does not fit.

## 7. Cactus Tool RAG lexical path is lossy for German UTF-8

The current BM25 helper iterates raw `char` bytes and applies `std::isalnum(static_cast<unsigned char>(c))`. Non-ASCII UTF-8 bytes break lexical tokens.

Exact source-equivalent sandbox examples:

- `Möglichkeiten prüfen` -> `glichkeiten`, `fen`
- `Überprüfe diesen Computer` -> `berpr`, `diesen`, `computer`
- `wöchentliche Bewusstseins-Session` -> `chentliche`, `bewusstseins`, `session`
- `größer Größe Größe` -> no retained words.

Actual active Frank registry analysis:

- 945 content words inspected;
- 65 contain non-ASCII and are altered by the lexical tokenizer (~6.9%);
- 44 distinct affected terms;
- terms such as `für` and `größe` disappear entirely in the lexical arm.

This proves lexical representation loss, not ranking degradation. The embedding arm has higher RRF weight and fragmented terms can sometimes match symmetrically. Required experiment: German vs English vs bilingual tool descriptions and Unicode-aware lexical baseline, report recall@k/MRR and downstream route accuracy.

## 8. Cactus confidence is not a proven Needle correctness probability

Current `complete.cpp` uses a generic confidence surface when no special handoff probe is loaded:

`confidence = 1 - token_uncertainty/entropy-like output`

It has generic fallback thresholds (model default or 0.7). Where a dedicated handoff probe exists, a separate `p_wrong` path can replace this with `1 - p_wrong`.

No current evidence recovered in this run establishes a Needle-specific calibrated wrongness probe. Therefore Cactus' generic threshold must not be imported into Frank as a semantic confidence threshold without held-out Needle/Frank calibration.

## 9. Cactus Needle prompt construction does not solve Franks budget question by itself

Current tokenizer path formats Needle as:

`format_needle_query_text(messages) + "<tools>" + serialize_needle_tools(tools) + "</s>"`

The model runtime is initialized with an explicit context size. The inspected preparation path serializes the selected tool block before tokenization; no semantic guarantee was found here that an over-budget tool list is shortened only at whole-tool boundaries while preserving a fixed headroom target.

Therefore H1 retains the stronger rule: exact tokenizer preflight of the complete selected catalogue and query, with fail-closed fallback rather than blind truncation/overflow behavior.

## 10. Runtime-profile conclusion

The two current execution families have different failure surfaces:

### Python/JAX Needle
- direct `parameters` mismatch for ordinary OpenAI schema;
- exact-marker constraint activation;
- explicit fail-open constraint states;
- raw pickle loader;
- invalid-JSON alias string replacement.

### Cactus Needle
- intentionally flattens JSON Schema;
- nevertheless string-pattern/escaping-sensitive schema parser;
- exact-marker Needle constraint activation remains;
- required/duplicate semantic checks are not sufficient as an authority boundary;
- has practical hybrid Tool RAG but its lexical BM25 path is byte/ASCII oriented for German;
- exposes generic confidence/handoff machinery that is not automatically Needle-calibrated.

## H1 invariant after differential fusion

Runtime differences must be treated as implementation profiles beneath one stricter Frank boundary:

`canonical tool contract -> exact budget preflight -> optional audited retrieval -> pinned Needle runtime -> strict independent validator -> NeedleDecisionReceipt(authority=NONE) -> Clay ingress -> separate effect authority`

The outer contract must be at least as strict as every runtime profile; it must not depend on a runtime-specific parser, constrainer, confidence threshold or recovery path for authority.
