import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "clayverse"

LIVE_ROOTS = {
    "service",
    "terminal_gateway",
    "terminal_sessions",
    "terminal_hooks",
    "mcp_server",
}
RETIRED = {
    "adapters",
    "api",
    "engine",
    "inference_protocol",
    "terminal",
}


def _local_imports(module: str) -> set[str]:
    path = PKG / f"{module}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    deps: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            deps.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("clayverse."):
                    deps.add(alias.name.split(".", 2)[1])
    return {dep for dep in deps if (PKG / f"{dep}.py").is_file()}


def _closure(roots: set[str]) -> set[str]:
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        module = stack.pop()
        if module in seen:
            continue
        seen.add(module)
        stack.extend(_local_imports(module) - seen)
    return seen


def test_live_product_import_closure_never_reaches_retired_runtimes():
    closure = _closure(LIVE_ROOTS)
    assert not (closure & RETIRED), f"retired modules leaked into live product closure: {sorted(closure & RETIRED)}"
    assert "clerk_auth" in closure
    assert "turn_lifecycle" in closure
    assert "effects" in closure
    assert "store" in closure


def test_dockerignore_excludes_every_retired_runtime_module():
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    for module in sorted(RETIRED):
        assert f"clayverse/{module}.py" in dockerignore
