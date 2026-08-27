#!/usr/bin/env python3
"""Monitoring publisher v6: coherent publication-set generations.

v5 atomically replaced each file, but a concurrent reader could still observe files from
multiple generations. v6 makes one generation directory authoritative and publishes one
small CURRENT pointer atomically. Readers that require authority/runtime provenance MUST
resolve CURRENT and read only files from that generation root. Legacy canonical files are
compatibility mirrors and are explicitly non-authoritative.

No provider/network calls are made by this wrapper.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
V5_PATH = HERE / "update_system_analysis_v5.py"
spec = importlib.util.spec_from_file_location("update_system_analysis_v5", V5_PATH)
v5 = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(v5)
v4 = v5.v4


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass


def build_generation(repo: Path, artifacts: Path, proc_root: Path, skip_legacy: bool=False):
    fs = repo / "free swarm"
    if skip_legacy:
        legacy_rc = None
        legacy_json = v4.load_json(fs / "SYSTEM_ANALYSIS_LIVE.json")
        staged_readme = (fs / "README.md").read_text(encoding="utf-8") if (fs/"README.md").exists() else "# Free Swarm\n"
    else:
        legacy_rc, legacy_json, staged_readme, err = v5.run_legacy_staged(repo, artifacts)
        if legacy_rc != 0 or not legacy_json:
            raise RuntimeError(f"staged legacy metrics failed rc={legacy_rc}: {err[:1000]}")
    p = v4.provenance(repo, artifacts, proc_root)
    canonical = v5.harden(legacy_json, p)
    gen_seed = json.dumps({"authority":p["authority"],"runtime":p["runtime"],"ts_ns":time.time_ns()}, sort_keys=True, separators=(",",":"))
    generation = hashlib.sha256(gen_seed.encode()).hexdigest()[:24]
    canonical["schema"] = "CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v6"
    canonical["publication_generation"] = generation
    p["publication_generation"] = generation
    readme = v5.replace_block_text(staged_readme, v4.render_block(p))
    provenance_text = json.dumps(p, indent=2, ensure_ascii=False)+"\n"
    canonical_text = json.dumps(canonical, indent=2, ensure_ascii=False)+"\n"
    files = {
        "SYSTEM_ANALYSIS_LIVE.json": canonical_text,
        "SYSTEM_ANALYSIS_PROVENANCE.json": provenance_text,
        "README.md": readme,
    }
    manifest = {
        "schema":"CLAY_MONITOR_PUBLICATION_SET/v1",
        "publication_generation":generation,
        "files":{k:sha256_text(v) for k,v in files.items()},
        "authority_state":p["authority"].get("authority_state"),
        "control_plane_coherent":bool(p["authority"].get("valid")),
    }
    manifest_text=json.dumps(manifest, indent=2, sort_keys=True)+"\n"
    return generation, files, manifest, manifest_text, legacy_rc


def publish(repo: Path, generation: str, files: dict[str,str], manifest: dict, manifest_text: str):
    fs=repo/"free swarm"; root=fs/"publication_generations"; gen_dir=root/generation
    if gen_dir.exists(): raise RuntimeError("publication generation collision")
    gen_dir.mkdir(parents=True, exist_ok=False)
    for name,text in files.items():
        p=gen_dir/name; p.write_text(text, encoding="utf-8")
        with p.open("rb") as f: os.fsync(f.fileno())
    (gen_dir/"MANIFEST.json").write_text(manifest_text, encoding="utf-8")
    with (gen_dir/"MANIFEST.json").open("rb") as f: os.fsync(f.fileno())
    # Single atomic authority switch. Readers resolve only this pointer.
    pointer={"schema":"CLAY_MONITOR_CURRENT/v1","publication_generation":generation,
             "generation_root":str(Path("publication_generations")/generation),
             "manifest_sha256":sha256_text(manifest_text)}
    atomic_text(fs/"SYSTEM_ANALYSIS_CURRENT.json", json.dumps(pointer, indent=2, sort_keys=True)+"\n")
    # Compatibility mirrors are intentionally non-authoritative; mixed mirror reads mint no credit.
    for name,text in files.items(): atomic_text(fs/name, text)
    atomic_text(fs/"SYSTEM_ANALYSIS_PROVENANCE_V6.json", files["SYSTEM_ANALYSIS_PROVENANCE.json"])
    return pointer


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",default="/workspace/clay-global-research-entity")
    ap.add_argument("--artifacts",default="/artifacts/clay-entityos-swarm"); ap.add_argument("--proc-root",default="/proc")
    ap.add_argument("--skip-legacy",action="store_true"); args=ap.parse_args()
    repo=Path(args.repo)
    try:
        generation,files,manifest,manifest_text,legacy_rc=build_generation(repo,Path(args.artifacts),Path(args.proc_root),args.skip_legacy)
        pointer=publish(repo,generation,files,manifest,manifest_text)
    except Exception as e:
        print(json.dumps({"state":"FAIL_CLOSED_PUBLICATION_SET","error":str(e)})); return 2
    valid=bool(manifest["control_plane_coherent"])
    print(json.dumps({"state":"PASS_COHERENT_PUBLICATION_SET" if valid else "FAIL_CLOSED_AUTHORITY",
                      "publication_generation":generation,"current_pointer":pointer,
                      "legacy_rc":legacy_rc,"authoritative_read_rule":"CURRENT_POINTER_GENERATION_ROOT_ONLY"}))
    return 0 if valid else 2

if __name__=="__main__": raise SystemExit(main())
