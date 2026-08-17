from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
KATA_TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
GATEWAY = ROOT / "clayverse" / "terminal_gateway.py"


def test_oci_healthcheck_is_liveness_not_runtime_readiness():
    dockerfile = DOCKERFILE.read_text()
    healthcheck = next(
        line for line in dockerfile.splitlines() if line.startswith("HEALTHCHECK ")
    )

    assert "/healthz" in healthcheck
    assert "/readyz" not in healthcheck
    assert "Image health is liveness-only" in dockerfile
    assert "Runtime readiness" in dockerfile


def test_product_surfaces_keep_liveness_and_readiness_distinct():
    gateway = GATEWAY.read_text()
    template = KATA_TEMPLATE.read_text()

    assert '@app.get("/healthz")' in gateway
    assert '"scope": "liveness"' in gateway
    assert '@app.get("/readyz")' in gateway
    assert '"scope": "runtime"' in gateway

    stateful = template.split("kind: StatefulSet", 1)[1]
    readiness = stateful.split("readinessProbe:", 1)[1].split("livenessProbe:", 1)[0]
    liveness = stateful.split("livenessProbe:", 1)[1].split("resources:", 1)[0]
    assert "path: /readyz" in readiness
    assert "path: /healthz" in liveness
    assert "path: /readyz" not in liveness
