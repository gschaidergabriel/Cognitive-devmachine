<!-- RAE_META
{
  "packet_id": "KMP-FRANK-LOCAL-MODEL-RESPONSE-CONTRACT-UBUNTU-20260809",
  "title": "FRANK local-model responses require strict projection before durable admission",
  "domains": ["frank", "model_runtime", "security", "observability", "deployment"],
  "topics": ["openai_compatible", "tool_calls", "usage", "proxy", "json", "llama_cpp", "ubuntu"],
  "epistemic_class": "MEASURED_IMPLEMENTATION_RESULT",
  "status_hint": "CURRENT",
  "origin_actor": "chatgpt-secondary",
  "provider": "OpenAI",
  "model": "GPT-5.6 Sol",
  "created_at": "2026-08-09T23:53:00+07:00",
  "canonical_parent_revision": 2,
  "canonical_parent_hash": "04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346",
  "source_refs": [
    "gschaidergabriel/Dr.-Unterweger@07f9af41ca3f4b7add75d198bebf92887c3b52d3",
    "gschaidergabriel/Dr.-Unterweger@b37a306e9266c44d1ab1b4faca9de643c96f440a:runtime/vps_integrity/latest.json",
    "gschaidergabriel/Dr.-Unterweger@b37a306e9266c44d1ab1b4faca9de643c96f440a:runtime/vps_integrity/latest.log",
    "https://docs.python.org/3.12/library/urllib.request.html",
    "https://docs.python.org/3/library/json.html",
    "https://www.rfc-editor.org/rfc/rfc8259",
    "https://github.com/ggml-org/llama.cpp/tree/master/tools/server"
  ],
  "evidence_refs": [
    "FRANK_VPS_DEEP_INTEGRITY",
    "LOOPBACK_OPENAI_COMPAT_RESPONSE_CONTRACT_REGRESSION"
  ],
  "confidence": 0.995,
  "verification_required": "Re-run after adapter/runtime contract changes and on Andreas' final Ubuntu target; real-model semantics require a pinned real local model/runtime receipt.",
  "falsifier_or_next_test": "A supported backend requires a currently projected-away field for correct FRANK tool semantics, or target-host testing shows the projection/strict-JSON layer causes material correctness or latency regression."
}
RAE_META -->

### Atomic result

The pre-patch FRANK OpenAI-compatible local-model adapter already bounded endpoint scheme, default remote access, redirects, response size and backend timing persistence, but three narrower contract gaps remained:

1. `urllib.request.build_opener(NoRedirect)` retained Python's default proxy-discovery behavior, making transport behavior depend on system/environment proxy configuration even though the intended v0.1 endpoint is local by default.
2. `message.tool_calls` and top-level `usage` were copied into durable output essentially unchanged, allowing arbitrary backend-specific nested fields to cross the observation/persistence boundary.
3. Python's default JSON decoder accepts non-finite `NaN`/`Infinity` constants even though RFC 8259 JSON does not admit them.

The merged FRANK delta at `07f9af41ca3f4b7add75d198bebf92887c3b52d3` now:

- supplies an explicit empty `ProxyHandler({})` so local-model transport does not auto-discover environment/system proxies;
- rejects non-finite JSON constants and prevents non-finite canonical JSON encoding;
- validates the minimal non-streaming response shape used by FRANK;
- projects tool calls onto `id`, `type=function`, `function.name`, `function.arguments`;
- projects usage onto bounded non-negative numeric token fields/details;
- keeps backend timing observations behind the pre-existing separate numeric allowlist;
- ignores unknown backend response fields rather than promoting them into durable FRANK state.

### Real Ubuntu receipt

The self-hosted Ubuntu runner `digital-retina` executed the merged SHA and produced a `REAL_SELF_HOSTED_UBUNTU_EXECUTION` deep-integrity receipt:

- 20 gates / 20 PASS / 0 FAIL;
- Linux 6.8.0-117-generic x86_64, Python 3.12.3;
- matrix wall time 8,878 ms;
- summed gate wall time 8,673 ms;
- `local_model_tool_metrics` gate 1,220 ms including the new adversarial contract subprocess;
- response projection micro-measurement over 2,000 iterations: p50 = 1,469 ns, p95 = 2,651 ns;
- environment proxy discovery: disabled and import-probed;
- non-finite JSON: rejected;
- unknown backend sentinel text persisted: false;
- hidden reasoning persisted: false;
- tool-call projection: PASS;
- usage numeric allowlist: PASS;
- existing backend timing allowlist: PASS.

The micro-measurement is an in-process contract projection measurement, not end-to-end model latency. The roughly 0.6 s increase in the CI gate is dominated by the added subprocess/local HTTP server test phases and is not evidence of 0.6 s production inference overhead.

### Hypothesis outcomes

- `H-RC-1 arbitrary nested backend metadata can cross the durable boundary`: CONFIRMED for the pre-patch code path by direct code inspection and adversarial sentinel construction; closed by projection regression for the tested contract.
- `H-RC-2 loopback traffic is definitely proxied by default`: NOT ESTABLISHED. Python may bypass proxies for a host/platform. Refined claim: the pre-patch opener retained environment-dependent proxy discovery; explicit empty proxy configuration removes that unnecessary dependency.
- `H-RC-3 Python default JSON can admit non-RFC non-finite constants`: CONFIRMED by primary documentation/RFC and regression; fixed at the adapter boundary.
- `H-RC-4 strict projection materially harms local response processing`: NOT SUPPORTED by the current micro-measurement; p95 projection time was 2.651 microseconds for the test object. This is not a full application benchmark.

### Architecture implication

Treat every OpenAI-compatible local backend as an observation/source boundary rather than a trusted FRANK state writer. Compatibility means the backend may produce the minimum required response contract; it does not grant authority for arbitrary backend metadata to become persistent state.

Keep these independently versioned layers:

`backend response -> strict transport parse -> visible/tool/usage projection -> backend numeric observations -> FRANK policy/effect authority`

Do not collapse tool-call data into execution authority. A returned function call remains model output until the external FRANK capability/effect gateway validates and authorizes it.

### Cross-mesh implications

- **FRANK/Harness:** keep response projection in the main Ubuntu integrity lane; add pinned real-model trials before any F6 release promotion.
- **UnifiedDB:** store only admitted response/tool/usage fields plus explicit provenance; backend-private fields are not schema-free persistence.
- **ClayGraph:** if tool/model observations become graph nodes, derive them from admitted projected semantic objects, not raw provider payloads.
- **ClayCode:** encode observation, projected contract, proposed tool effect and committed effect as distinct typed/provenance-bearing states.
- **GWT:** broadcast of a model response does not authorize its tool call and should retain effect/outcome/reentry receipts separately.
- **Hyperposition:** preserve backend/runtime alternatives; do not infer equivalent semantics merely from OpenAI-compatible endpoint shape.
- **Emergenz:** sanitization/integration success is infrastructure evidence, not emergence/consciousness evidence.

### Negative evidence retained

- No exploit receipt proves that the prior loopback configuration actually traversed an external proxy on `digital-retina`.
- The current VPS has no measured real 4B execution in this cycle; adapter contract PASS must not be converted into model-quality/throughput PASS.
- 20/20 deep-integrity gates cover the current declared matrix only; they are not a whole-FRANK-v0.1 release receipt.

### Next falsifier

Provision or identify a pinned supported local Qwen-class 4B runtime on a capable Ubuntu host, run real tool-call/non-tool-call responses through this adapter, verify projected semantics across backend versions/templates, and measure end-to-end tokens/s, TTFT, peak memory, response-projection overhead, recovery, tool correctness and provenance. Final v0.1 acceptance remains Andreas' Ubuntu developer system.