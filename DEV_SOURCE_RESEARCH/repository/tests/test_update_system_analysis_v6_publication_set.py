from pathlib import Path
import importlib.util, json, tempfile

P=Path(__file__).resolve().parents[1]/"free swarm/update_system_analysis_v6.py"
spec=importlib.util.spec_from_file_location("m",P); m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m)


def fake_files(gen):
    p={"publication_generation":gen,"authority":{"authority_state":"HARD_OFF","valid":True},"runtime":{},"snapshot_provenance":{}}
    c={"schema":"CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v6","publication_generation":gen}
    files={"SYSTEM_ANALYSIS_LIVE.json":json.dumps(c)+"\n","SYSTEM_ANALYSIS_PROVENANCE.json":json.dumps(p)+"\n","README.md":f"gen {gen}\n"}
    manifest={"schema":"CLAY_MONITOR_PUBLICATION_SET/v1","publication_generation":gen,"files":{k:m.sha256_text(v) for k,v in files.items()},"authority_state":"HARD_OFF","control_plane_coherent":True}
    return files,manifest,json.dumps(manifest,indent=2,sort_keys=True)+"\n"


def read_authoritative(repo):
    fs=repo/"free swarm"; ptr=json.loads((fs/"SYSTEM_ANALYSIS_CURRENT.json").read_text())
    root=fs/ptr["generation_root"]; mt=(root/"MANIFEST.json").read_text(); assert m.sha256_text(mt)==ptr["manifest_sha256"]
    man=json.loads(mt); assert man["publication_generation"]==ptr["publication_generation"]
    out={}
    for name,digest in man["files"].items():
        text=(root/name).read_text(); assert m.sha256_text(text)==digest; out[name]=text
    return ptr,man,out


def test_pointer_switch_is_single_authority_boundary():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); (repo/"free swarm").mkdir(parents=True)
        f1,man1,mt1=fake_files("g1"); m.publish(repo,"g1",f1,man1,mt1)
        p1,_,_=read_authoritative(repo); assert p1["publication_generation"]=="g1"
        f2,man2,mt2=fake_files("g2")
        # prepare an unpointed generation: authoritative reader must still see g1
        root=repo/"free swarm/publication_generations/g2"; root.mkdir(parents=True)
        for n,t in f2.items(): (root/n).write_text(t)
        (root/"MANIFEST.json").write_text(mt2)
        pstill,_,_=read_authoritative(repo); assert pstill["publication_generation"]=="g1"


def test_mixed_compatibility_mirrors_cannot_change_authoritative_generation():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); (repo/"free swarm").mkdir(parents=True)
        f1,man1,mt1=fake_files("g1"); m.publish(repo,"g1",f1,man1,mt1)
        # Simulate adversarial interleaving on legacy mirror paths.
        (repo/"free swarm/SYSTEM_ANALYSIS_LIVE.json").write_text('{"publication_generation":"evil"}\n')
        ptr,man,out=read_authoritative(repo)
        assert ptr["publication_generation"]==man["publication_generation"]=="g1"
        assert json.loads(out["SYSTEM_ANALYSIS_LIVE.json"])["publication_generation"]=="g1"


def test_manifest_detects_generation_file_tamper():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); (repo/"free swarm").mkdir(parents=True)
        f,man,mt=fake_files("g1"); m.publish(repo,"g1",f,man,mt)
        (repo/"free swarm/publication_generations/g1/SYSTEM_ANALYSIS_LIVE.json").write_text('{}\n')
        try: read_authoritative(repo)
        except AssertionError: pass
        else: raise AssertionError("tampered generation file accepted")


def test_pointer_manifest_digest_detects_manifest_transplant():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); (repo/"free swarm").mkdir(parents=True)
        f,man,mt=fake_files("g1"); m.publish(repo,"g1",f,man,mt)
        mp=repo/"free swarm/publication_generations/g1/MANIFEST.json"; mp.write_text(mt.replace('"g1"','"other"'))
        try: read_authoritative(repo)
        except AssertionError: pass
        else: raise AssertionError("transplanted manifest accepted")


def test_generation_collision_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); (repo/"free swarm").mkdir(parents=True)
        f,man,mt=fake_files("g1"); m.publish(repo,"g1",f,man,mt)
        try: m.publish(repo,"g1",f,man,mt)
        except RuntimeError: pass
        else: raise AssertionError("generation collision accepted")
