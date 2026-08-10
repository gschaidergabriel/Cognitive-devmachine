#!/usr/bin/env bash
set -euo pipefail

json_escape() { python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'; }
cmd_path() { command -v "$1" 2>/dev/null || true; }

PSQL="$(cmd_path psql)"
POSTGRES="$(cmd_path postgres)"
PG_CONFIG="$(cmd_path pg_config)"
DOCKER="$(cmd_path docker)"
PODMAN="$(cmd_path podman)"

PSQL_VERSION=""
PG_CONFIG_VERSION=""
DOCKER_VERSION=""
PODMAN_VERSION=""
VECTOR_EXTENSION_CONTROL=""

if [[ -n "$PSQL" ]]; then PSQL_VERSION="$(psql --version 2>&1 || true)"; fi
if [[ -n "$PG_CONFIG" ]]; then
  PG_CONFIG_VERSION="$(pg_config --version 2>&1 || true)"
  SHAREDIR="$(pg_config --sharedir 2>/dev/null || true)"
  if [[ -n "$SHAREDIR" && -f "$SHAREDIR/extension/vector.control" ]]; then VECTOR_EXTENSION_CONTROL="$SHAREDIR/extension/vector.control"; fi
fi
if [[ -n "$DOCKER" ]]; then DOCKER_VERSION="$(docker --version 2>&1 || true)"; fi
if [[ -n "$PODMAN" ]]; then PODMAN_VERSION="$(podman --version 2>&1 || true)"; fi

python3 - <<PY
import json, os, platform, sqlite3
out={
  "schema":"clay.postgres_pgvector_capability_probe.v1",
  "host":{
    "platform":platform.platform(),
    "machine":platform.machine(),
    "processor":platform.processor() or "UNKNOWN",
    "python":platform.python_version(),
    "sqlite":sqlite3.sqlite_version,
  },
  "commands":{
    "psql":${PSQL@Q}, "postgres":${POSTGRES@Q}, "pg_config":${PG_CONFIG@Q},
    "docker":${DOCKER@Q}, "podman":${PODMAN@Q},
  },
  "versions":{
    "psql":${PSQL_VERSION@Q}, "pg_config":${PG_CONFIG_VERSION@Q},
    "docker":${DOCKER_VERSION@Q}, "podman":${PODMAN_VERSION@Q},
  },
  "pgvector_control":${VECTOR_EXTENSION_CONTROL@Q},
}
out["native_postgres_available"] = bool(out["commands"]["psql"] and out["commands"]["postgres"])
out["native_pgvector_detected"] = bool(out["pgvector_control"])
out["container_runtime_available"] = bool(out["commands"]["docker"] or out["commands"]["podman"])
out["baseline_executable_now_without_install"] = bool(out["native_postgres_available"] and out["native_pgvector_detected"])
out["containerized_baseline_possible_candidate"] = out["container_runtime_available"]
out["authority"] = "CAPABILITY_OBSERVATION_ONLY_NO_INSTALL_NO_SYSTEM_MUTATION"
print(json.dumps(out,indent=2,sort_keys=True))
PY
