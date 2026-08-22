#!/usr/bin/env python3
"""Source-bound, repeat-build provenance wrapper for the native Mini Entity.

This tool does not make a build globally reproducible by declaration. It fails closed
unless repeated builds inside the same admitted environment produce identical ELF bytes,
and it records the source/compiler/dependency/artifact identities needed to replicate or
compare the build elsewhere.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


DEFAULT_PACKAGES = ("sqlite3", "libcurl", "json-c")
INCLUDE_DIRECTIVE_RE = re.compile(rb"^\s*#\s*include\s+([^\r\n]+)$", re.MULTILINE)
QUOTED_INCLUDE_RE = re.compile(rb'^"([^"\r\n]+)"(?:\s*(?://.*|/\*.*\*/\s*)?)?$')
ANGLE_INCLUDE_RE = re.compile(rb"^<[^>\r\n]+>(?:\s*(?://.*|/\*.*\*/\s*)?)?$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_closure(source: Path) -> dict[str, Any]:
    """Bind every project-local quoted include reachable from the entry translation unit.

    Angle-bracket includes are dependency/toolchain inputs and remain covered separately by
    pkg-config/compiler/runtime dependency identity. Macro/dynamic includes are rejected:
    a source-bound receipt may not silently omit bytes selected by preprocessor indirection.
    """
    source = source.resolve()
    root = source.parent.resolve()
    pending = [source]
    seen: dict[str, dict[str, Any]] = {}

    while pending:
        current = pending.pop()
        try:
            relative = current.relative_to(root).as_posix()
        except ValueError as exc:
            raise RuntimeError("LOCAL_INCLUDE_OUTSIDE_SOURCE_ROOT:" + str(current)) from exc
        if relative in seen:
            continue
        if not current.is_file():
            raise RuntimeError("LOCAL_INCLUDE_MISSING:" + str(current))

        data = current.read_bytes()
        seen[relative] = {
            "path": relative,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }
        for match in INCLUDE_DIRECTIVE_RE.finditer(data):
            target = match.group(1).strip()
            quoted = QUOTED_INCLUDE_RE.fullmatch(target)
            if quoted:
                try:
                    include_name = quoted.group(1).decode("utf-8", "strict")
                except UnicodeDecodeError as exc:
                    raise RuntimeError("LOCAL_INCLUDE_PATH_NOT_UTF8:" + relative) from exc
                include_path = (current.parent / include_name).resolve()
                try:
                    include_path.relative_to(root)
                except ValueError as exc:
                    raise RuntimeError("LOCAL_INCLUDE_OUTSIDE_SOURCE_ROOT:" + include_name) from exc
                pending.append(include_path)
                continue
            if ANGLE_INCLUDE_RE.fullmatch(target):
                continue
            raise RuntimeError(
                "DYNAMIC_OR_UNBOUND_INCLUDE:" + relative + ":" + target.decode("utf-8", "replace")
            )

    files = [seen[key] for key in sorted(seen)]
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "root": str(root),
        "sha256": hashlib.sha256(canonical).hexdigest(),
        "files": files,
    }


def run(argv: list[str], *, env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(
        argv,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "COMMAND_FAILED rc={} argv={} stderr={}".format(
                proc.returncode,
                shlex.join(argv),
                proc.stderr.strip(),
            )
        )
    return proc.stdout.strip()


def pkg_config(packages: tuple[str, ...]) -> tuple[list[str], dict[str, str]]:
    versions: dict[str, str] = {}
    for package in packages:
        versions[package] = run(["pkg-config", "--modversion", package])
    flags = shlex.split(run(["pkg-config", "--cflags", "--libs", *packages]))
    return flags, versions


def compiler_identity(compiler: str) -> dict[str, Any]:
    path_text = shutil.which(compiler)
    if not path_text:
        raise RuntimeError("COMPILER_NOT_FOUND:" + compiler)
    path = Path(path_text).resolve()
    return {
        "requested": compiler,
        "path": str(path),
        "sha256": sha256_file(path),
        "dumpmachine": run([str(path), "-dumpmachine"]),
        "version": run([str(path), "--version"]).splitlines()[0],
    }


def linked_libraries(binary: Path) -> list[dict[str, Any]]:
    text = run(["ldd", str(binary)])
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in text.splitlines():
        match = re.search(r"=>\s+(/[^\s]+)", line)
        if not match:
            match = re.match(r"\s*(/[^\s]+)", line)
        if not match:
            continue
        path = Path(match.group(1)).resolve()
        key = str(path)
        if key in seen or not path.is_file():
            continue
        seen.add(key)
        out.append({"path": key, "sha256": sha256_file(path)})
    return sorted(out, key=lambda item: item["path"])


def build_id(binary: Path) -> str | None:
    try:
        text = run(["readelf", "-n", str(binary)])
    except Exception:
        return None
    match = re.search(r"Build ID:\s*([0-9a-fA-F]+)", text)
    return match.group(1).lower() if match else None


def compile_once(
    *,
    compiler_path: str,
    source: Path,
    source_identity_sha: str,
    flags: list[str],
    env: dict[str, str],
    workdir: Path,
) -> Path:
    output = workdir / "mini_entity.clay"
    root = source.parent.resolve()
    argv = [
        compiler_path,
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-Wno-deprecated-declarations",
        f"-frandom-seed={source_identity_sha}",
        f"-ffile-prefix-map={root}=/clay/native",
        f"-fdebug-prefix-map={root}=/clay/native",
        "-Wl,--build-id=sha1",
        "-o",
        str(output),
        str(source),
        *flags,
    ]
    run(argv, env=env)
    if not output.is_file():
        raise RuntimeError("COMPILER_RETURNED_WITHOUT_OUTPUT")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).with_name("mini_entity.c"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("mini_entity.clay"))
    parser.add_argument("--receipt", type=Path, default=Path(__file__).with_name("native_build_provenance.json"))
    parser.add_argument("--compiler", default="gcc")
    parser.add_argument("--version-label", required=True)
    parser.add_argument("--source-date-epoch", type=int, required=True)
    parser.add_argument("--repeat", type=int, default=2)
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.is_file():
        raise SystemExit("SOURCE_MISSING:" + str(source))
    if args.repeat < 2:
        raise SystemExit("REPEAT_MUST_BE_AT_LEAST_2")

    entry_source_sha = sha256_file(source)
    closure = source_closure(source)
    source_identity_sha = str(closure["sha256"])
    compiler = compiler_identity(args.compiler)
    flags, package_versions = pkg_config(DEFAULT_PACKAGES)
    env = dict(os.environ)
    env.update(
        {
            "SOURCE_DATE_EPOCH": str(args.source_date_epoch),
            "LC_ALL": "C",
            "LANG": "C",
            "TZ": "UTC",
        }
    )

    hashes: list[str] = []
    retained: Path | None = None
    with tempfile.TemporaryDirectory(prefix="mini-entity-bound-build-") as tmp_text:
        tmp = Path(tmp_text)
        for index in range(args.repeat):
            workdir = tmp / f"build-{index}"
            workdir.mkdir()
            binary = compile_once(
                compiler_path=compiler["path"],
                source=source,
                source_identity_sha=source_identity_sha,
                flags=flags,
                env=env,
                workdir=workdir,
            )
            hashes.append(sha256_file(binary))
            if retained is None:
                retained = binary

        if len(set(hashes)) != 1:
            raise SystemExit("REPEAT_BUILD_HASH_MISMATCH:" + ",".join(hashes))

        assert retained is not None
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        temp_output = output.with_suffix(output.suffix + ".tmp")
        shutil.copy2(retained, temp_output)
        os.replace(temp_output, output)

    final_hash = sha256_file(output)
    if final_hash != hashes[0]:
        raise SystemExit("PUBLISHED_BINARY_HASH_MISMATCH")

    provenance = {
        "schema": "mini-entity-native-build-provenance/v2",
        "version_label": args.version_label,
        "subject": {
            "path": str(output),
            "sha256": final_hash,
            "elf_build_id": build_id(output),
        },
        "build_definition": {
            "source": {"path": str(source), "sha256": entry_source_sha},
            "source_closure": closure,
            "source_identity_sha256": source_identity_sha,
            "compiler": compiler,
            "pkg_config_packages": package_versions,
            "pkg_config_flags": flags,
            "source_date_epoch": args.source_date_epoch,
            "repeat_builds": args.repeat,
            "repeat_hashes": hashes,
            "repeat_byte_identity": len(set(hashes)) == 1,
            "fixed_environment": {"LC_ALL": "C", "LANG": "C", "TZ": "UTC"},
            "determinism_flags": [
                f"-frandom-seed={source_identity_sha}",
                f"-ffile-prefix-map={source.parent.resolve()}=/clay/native",
                f"-fdebug-prefix-map={source.parent.resolve()}=/clay/native",
                "-Wl,--build-id=sha1",
            ],
        },
        "resolved_runtime_dependencies": linked_libraries(output),
        "generated_at_unix": time.time(),
        "acceptance_scope": "SAME_ENV_REPEAT_BUILD_AND_TRANSITIVE_SOURCE_PROVENANCE_BINDING_ONLY",
        "not_claimed": [
            "cross-environment reproducibility until independently rebuilt from the same recorded inputs",
            "model quality",
            "application acceptance",
            "whole Mini Entity final acceptance"
        ],
    }
    receipt = args.receipt.resolve()
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
