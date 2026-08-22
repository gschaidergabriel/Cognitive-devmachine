#!/usr/bin/env python3
"""Source-bound, repeat-build provenance wrapper for the native Mini Entity.

This tool does not make a build globally reproducible by declaration. It fails closed
unless repeated builds inside the same admitted environment produce identical ELF bytes,
and it records the complete local C source/include closure plus compiler/dependency/artifact
identities needed to replicate or compare the build elsewhere.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


DEFAULT_PACKAGES = ("sqlite3", "libcurl", "json-c")
LOCAL_INCLUDE_RE = re.compile(r'^\s*#\s*include\s*"([^"\n]+)"', re.MULTILINE)
MAX_SOURCE_FILE_BYTES = 16 * 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _assert_no_symlink_components(path: Path, root: Path) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("SOURCE_INCLUDE_ESCAPES_ROOT:" + str(path)) from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError("SOURCE_SYMLINK_FORBIDDEN:" + str(current))


def _regular_nosymlink(path: Path, root: Path) -> os.stat_result:
    _assert_no_symlink_components(path, root)
    st = path.stat()
    if not stat.S_ISREG(st.st_mode):
        raise RuntimeError("SOURCE_NOT_REGULAR:" + str(path))
    if st.st_size < 0 or st.st_size > MAX_SOURCE_FILE_BYTES:
        raise RuntimeError("SOURCE_SIZE_OUT_OF_BOUNDS:" + str(path))
    return st


def source_closure(source: Path) -> tuple[list[dict[str, Any]], str]:
    """Return a deterministic, fail-closed local quoted-include closure.

    System includes (<...>) are compiler/dependency inputs and remain covered by compiler,
    pkg-config and linked-library identities. Repository-local quoted includes are source
    identity and MUST be hashed together with the entry unit.
    """
    source = source.absolute()
    root = source.parent.absolute()
    if root.is_symlink():
        raise RuntimeError("SOURCE_ROOT_SYMLINK_FORBIDDEN:" + str(root))
    pending = [source]
    visited: set[Path] = set()
    records: list[tuple[str, bytes]] = []

    while pending:
        path = pending.pop().absolute()
        if path in visited:
            continue
        _regular_nosymlink(path, root)
        data = path.read_bytes()
        rel = path.relative_to(root).as_posix()
        records.append((rel, data))
        visited.add(path)

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError("SOURCE_NOT_UTF8:" + rel) from exc
        for include in LOCAL_INCLUDE_RE.findall(text):
            candidate = Path(os.path.normpath(str(path.parent / include))).absolute()
            try:
                candidate.relative_to(root)
            except ValueError as exc:
                raise RuntimeError("SOURCE_INCLUDE_ESCAPES_ROOT:" + include) from exc
            _assert_no_symlink_components(candidate, root)
            if not candidate.exists():
                raise RuntimeError("SOURCE_INCLUDE_MISSING:" + include)
            pending.append(candidate)

    records.sort(key=lambda item: item[0])
    closure = hashlib.sha256()
    entries: list[dict[str, Any]] = []
    for rel, data in records:
        digest = hashlib.sha256(data).hexdigest()
        entries.append({"path": rel, "sha256": digest, "size": len(data)})
        closure.update(rel.encode("utf-8"))
        closure.update(b"\0")
        closure.update(digest.encode("ascii"))
        closure.update(b"\0")
        closure.update(str(len(data)).encode("ascii"))
        closure.update(b"\n")
    return entries, closure.hexdigest()


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
    source_closure_sha: str,
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
        f"-frandom-seed={source_closure_sha}",
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

    source = args.source.absolute()
    if not source.is_file():
        raise SystemExit("SOURCE_MISSING:" + str(source))
    if args.repeat < 2:
        raise SystemExit("REPEAT_MUST_BE_AT_LEAST_2")

    source_sha = sha256_file(source)
    source_entries, closure_sha = source_closure(source)
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
                source_closure_sha=closure_sha,
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
        output = args.output.absolute()
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
            "source": {"path": str(source), "sha256": source_sha},
            "source_closure": {
                "root": str(source.parent.absolute()),
                "sha256": closure_sha,
                "files": source_entries,
            },
            "compiler": compiler,
            "pkg_config_packages": package_versions,
            "pkg_config_flags": flags,
            "source_date_epoch": args.source_date_epoch,
            "repeat_builds": args.repeat,
            "repeat_hashes": hashes,
            "repeat_byte_identity": len(set(hashes)) == 1,
            "fixed_environment": {"LC_ALL": "C", "LANG": "C", "TZ": "UTC"},
            "determinism_flags": [
                f"-frandom-seed={closure_sha}",
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
            "model quality",
            "application acceptance",
            "whole Mini Entity final acceptance",
        ],
    }
    receipt = args.receipt.absolute()
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
