#!/usr/bin/env python3
"""Source-bound, repeat-build provenance wrapper for the native Mini Entity.

This tool does not make a build globally reproducible by declaration. It fails closed
unless repeated builds inside the same admitted environment produce identical ELF bytes,
and it records the complete repository-local C source closure plus compiler/dependency/
artifact identities needed to replicate or compare the build elsewhere.
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
LOCAL_INCLUDE_RE = re.compile(rb'^\s*#\s*include\s*"([^"\r\n]+)"', re.MULTILINE)
INCLUDE_DIRECTIVE_RE = re.compile(rb'^\s*#\s*include\s+([^\r\n]+)', re.MULTILINE)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_source_closure(source: Path) -> dict[str, Any]:
    """Hash the complete repository-local quoted-include closure.

    The native entry unit is intentionally split into local .inc implementation parts.
    Binding only mini_entity.c would therefore leave semantic source bytes outside the
    declared provenance identity. System/header dependencies using <...> remain bound by
    compiler/package/runtime dependency evidence rather than this repository source set.
    """
    entry = source.resolve()
    root = entry.parent.resolve()
    if not entry.is_file():
        raise RuntimeError("SOURCE_MISSING:" + str(entry))

    pending = [entry]
    visited: set[Path] = set()
    members: list[dict[str, Any]] = []

    while pending:
        path = pending.pop()
        if path in visited:
            continue
        if path.is_symlink():
            raise RuntimeError("LOCAL_SOURCE_SYMLINK_FORBIDDEN:" + str(path))
        if path != root and root not in path.parents:
            raise RuntimeError("LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT:" + str(path))
        if not path.is_file():
            raise RuntimeError("LOCAL_INCLUDE_MISSING:" + str(path))

        data = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        for raw_target in INCLUDE_DIRECTIVE_RE.findall(data):
            target = raw_target.lstrip()
            if target.startswith(b"\"") or target.startswith(b"<"):
                continue
            raise RuntimeError("DYNAMIC_INCLUDE_FORBIDDEN:" + relative)
        members.append(
            {
                "path": relative,
                "size": len(data),
                "sha256": sha256_bytes(data),
            }
        )
        visited.add(path)

        for raw_name in LOCAL_INCLUDE_RE.findall(data):
            try:
                name = raw_name.decode("utf-8", "strict")
            except UnicodeDecodeError as exc:
                raise RuntimeError("LOCAL_INCLUDE_NAME_NOT_UTF8:" + relative) from exc
            candidate = path.parent / name
            if candidate.is_symlink():
                raise RuntimeError("LOCAL_SOURCE_SYMLINK_FORBIDDEN:" + str(candidate))
            resolved = candidate.resolve()
            if resolved != root and root not in resolved.parents:
                raise RuntimeError("LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT:" + name)
            if not resolved.is_file():
                raise RuntimeError("LOCAL_INCLUDE_MISSING:" + name)
            pending.append(resolved)

    members.sort(key=lambda item: item["path"])
    manifest_bytes = json.dumps(
        members,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "root": str(root),
        "entry": entry.relative_to(root).as_posix(),
        "sha256": sha256_bytes(manifest_bytes),
        "members": members,
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
    source_set_sha: str,
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
        f"-frandom-seed={source_set_sha}",
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

    source_entry_sha = sha256_file(source)
    source_set = discover_source_closure(source)
    source_set_sha = str(source_set["sha256"])
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
                source_set_sha=source_set_sha,
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
            "source": {"path": str(source), "sha256": source_entry_sha},
            "source_set": source_set,
            "compiler": compiler,
            "pkg_config_packages": package_versions,
            "pkg_config_flags": flags,
            "source_date_epoch": args.source_date_epoch,
            "repeat_builds": args.repeat,
            "repeat_hashes": hashes,
            "repeat_byte_identity": len(set(hashes)) == 1,
            "fixed_environment": {"LC_ALL": "C", "LANG": "C", "TZ": "UTC"},
            "determinism_flags": [
                f"-frandom-seed={source_set_sha}",
                f"-ffile-prefix-map={source.parent.resolve()}=/clay/native",
                f"-fdebug-prefix-map={source.parent.resolve()}=/clay/native",
                "-Wl,--build-id=sha1",
            ],
        },
        "resolved_runtime_dependencies": linked_libraries(output),
        "generated_at_unix": time.time(),
        "acceptance_scope": "SAME_ENV_REPEAT_BUILD_AND_COMPLETE_LOCAL_SOURCE_CLOSURE_BINDING_ONLY",
        "not_claimed": [
            "cross-environment reproducibility until independently rebuilt from the same recorded inputs",
            "system-header byte identity beyond recorded compiler/package environment",
            "model quality",
            "application acceptance",
            "whole Mini Entity final acceptance",
        ],
    }
    receipt = args.receipt.resolve()
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
