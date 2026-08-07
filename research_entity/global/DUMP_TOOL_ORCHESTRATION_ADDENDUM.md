# DUMP Tool Orchestration Addendum

`dump` inherits the project research tool orchestration policy.

After D4 hypothesis generation and before D5 external research:
1. classify hypothesis clusters into scholarly, bibliographic, current_web, implementation, executable and model_experiment as applicable;
2. create the provider plan with `tools/research_provider_router.py plan`;
3. execute applicable required providers while available;
4. record provider outcomes and any quota/runtime fallback in `TOOL_EXECUTION_MANIFEST.json`;
5. continue with legacy research methods whenever a provider cannot be used;
6. validate the tool manifest before strong claim promotion and before declaring the dump research cycle complete.

Dump-derived propositions remain OPEN by default regardless of how many discovery providers return related material.
