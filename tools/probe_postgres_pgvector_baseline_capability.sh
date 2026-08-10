#!/usr/bin/env bash
set -euo pipefail

cmd_path() { command -v "$1" 2>/dev/null || true; }

export CLAY_PROBE_PSQL="$(cmd_path psql)"
export CLAY_PROBE_POSTGRES="$(cmd_path postgres)"
export CLAY_PROBE_PG_CONFIG="$(cmd_path pg_config)"
export CLAY_PROBE_DOCKER="$(cmd_path docker)"
export CLAY_PROBE_PODMAN="$(cmd_path podman)"

export CLAY_PROBE_PSQL_VERSION=""
export CLAY_PROBE_PG_CONFIG_VERSION=""
export CLAY_PROBE_DOCKER_VERSION=""
export CLAY_PROBE_PODMAN_VERSION=""
export CLAY_PROBE_VECTOR_CONTROL=""

if [[ -n "$CLAY_PROBE_PSQL" ]]; then
  export CLAY_PROBE_PSQL_VERSION="$(psql --version 2>&1 || true)"
fi
if [[ -n "$CLAY_PROBE_PG_CONFIG" ]]; then
  export CLAY_PROBE_PG_CONFIG_VERSION="$(pg_config --version 2>&1 || true)"
  SHAREDIR="$(pg_config --sharedir 2>/dev/null || true)"
  if [[ -n "$SHAREDIR" && -f "$SHAREDIR/extension/vector.control" ]]; then
    export CLAY_PROBE_VECTOR_CONTROL="$SHAREDIR/extension/vector.control"
  fi
fi
if [[ -n "$CLAY_PROBE_DOCKER" ]]; then
  export CLAY_PROBE_DOCKER_VERSION="$(docker --version 2>&1 || true)"
fi
if [[ -n "$CLAY_PROBE_PODMAN" ]]; then
  export CLAY_PROBE_PODMAN_VERSION="$(podman --version 2>&1 || true)"
fi

python3 - <<'PY'
import json, os, platform, sqlite3

def env(name):
    return os.environ.get(name, "")

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
    "psql":env("CLAY_PROBE_PSQL"),
    "postgres":env("CLAY_PROBE_POSTGRES"),
    "pg_config":env("CLAY_PROBE_PG_CONFIG"),
    "docker":env("CLAY_PROBE_DOCKER"),
    "podman":env("CLAY_PROBE_PODMAN"),
  },
  "versions":{
    "psql":env("CLAY_PROBE_PSQL_VERSION"),
    "pg_config":env("CLAY_PROBE_PG_CONFIG_VERSION"),
    "docker":env("CLAY_PROBE_DOCKER_VERSION"),
    "podman":env("CLAY_PROBE_PODMAN_VERSION"),
  },
  "pgvector_control":env("CLAY_PROBE_VECTOR_CONTROL"),
}
out["native_postgres_available"] = bool(out["commands"]["psql"] and out["commands"]["postgres"])
out["native_pgvector_detected"] = bool(out["pgvector_control"])
out["container_runtime_available"] = bool(out["commands"]["docker"] or out["commands"]["podman"])
out["baseline_executable_now_without_install"] = bool(out["native_postgres_available"] and out["native_pgvector_detected"])
out["containerized_baseline_possible_candidate"] = out["container_runtime_available"]
out["authority"] = "CAPABILITY_OBSERVATION_ONLY_NO_INSTALL_NO_SYSTEM_MUTATION"
print(json.dumps(out,indent=2,sort_keys=True))
PY
