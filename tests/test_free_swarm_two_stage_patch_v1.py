from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))

import free_swarm_two_stage_patch_v1 as two  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    proc=subprocess.run(["git",*args],cwd=repo,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return proc.stdout.strip()


def _repo(tmp_path: Path):
    repo=tmp_path/"repo";repo.mkdir()
    _git(repo,"init","-q");_git(repo,"config","user.email","test@example.invalid");_git(repo,"config","user.name","Clay Test")
    (repo/"tools").mkdir();(repo/"tools/x.py").write_text("VALUE = 1\n",encoding="utf-8")
    _git(repo,"add","tools/x.py");_git(repo,"commit","-qm","seed")
    return repo,_git(repo,"rev-parse","HEAD"),_git(repo,"rev-parse","HEAD^{tree}"),_git(repo,"rev-parse","HEAD:tools/x.py")


def _delta(*, target="tools/x.py", patch="", ready=False):
    obj={
        "delta_id":"d-1","hypothesis":"exact source raises apply rate","mechanism":"replace exact line",
        "target_files":[target],"patch_unified_diff":patch,"test_commands":["python3 -m py_compile tools/x.py"],
        "negative_test_commands":[],"benchmark_command":"","metric":"git_apply_check_pass","expected_direction":"higher",
        "baseline_needed":True,"falsifier":"apply check still fails","risk":"small","ready_for_forge":ready,
    }
    return "DEUTSCHE_ZUSAMMENFASSUNG\nBefund\nARCHITECTURE_DELTA_JSON="+json.dumps(obj,separators=(",",":"))+"\nOPEN_RESEARCH_QUESTIONS_JSON=[]"


def _payload(text, tokens=1):
    return {"choices":[{"message":{"content":text}}],"usage":{"total_tokens":tokens}}


def _fake_v3(repo: Path, commit: str, tree: str, request):
    base=SimpleNamespace(request_chat=request)
    fabric=SimpleNamespace(base=base)
    return SimpleNamespace(fabric=fabric,_ROOT=repo,_SOURCE={"commit":commit,"tree":tree})


def test_stage2_receives_exact_committed_blob_and_only_apply_clean_result_is_promoted(tmp_path,monkeypatch):
    repo,commit,tree,blob=_repo(tmp_path)
    first=_payload(_delta(),3)
    patch="--- a/tools/x.py\n+++ b/tools/x.py\n@@ -1 +1 @@\n-VALUE = 1\n+VALUE = 2\n"
    second=_payload(_delta(patch=patch,ready=True),5)
    request=mock.Mock(side_effect=[(200,{"x":"1"},first),(200,{"x":"2"},second)])
    monkeypatch.setenv("CLAY_SWARM_ARTIFACT_ROOT",str(tmp_path/"artifacts"))
    v3=_fake_v3(repo,commit,tree,request);two.install(v3)
    status,headers,payload=v3.fabric.base.request_chat(SimpleNamespace(name="openrouter"),"key","model","stage1",1000,30)
    assert status==200 and headers=={"x":"2"}
    assert request.call_count==2
    stage2_prompt=request.call_args_list[1].args[3]
    assert commit in stage2_prompt and blob in stage2_prompt and "VALUE = 1" in stage2_prompt
    assert two._extract_text(payload)==two._extract_text(second)
    assert payload["usage"]["total_tokens"]==8
    events=(tmp_path/"artifacts/two_stage_patch/events.jsonl").read_text(encoding="utf-8")
    assert '"event":"CONTEXT_REHYDRATED"' in events and '"event":"APPLY_CHECK_PASS"' in events


def test_bad_stage2_apply_check_falls_back_to_original_candidate(tmp_path,monkeypatch):
    repo,commit,tree,_=_repo(tmp_path)
    first=_payload(_delta(),2)
    bad="--- a/tools/x.py\n+++ b/tools/x.py\n@@ -1 +1 @@\n-VALUE = 999\n+VALUE = 2\n"
    second=_payload(_delta(patch=bad,ready=True),4)
    request=mock.Mock(side_effect=[(200,{},first),(200,{},second)])
    monkeypatch.setenv("CLAY_SWARM_ARTIFACT_ROOT",str(tmp_path/"artifacts"))
    v3=_fake_v3(repo,commit,tree,request);two.install(v3)
    _,_,payload=v3.fabric.base.request_chat(SimpleNamespace(name="openrouter"),"key","model","stage1",1000,30)
    assert request.call_count==2 and two._extract_text(payload)==two._extract_text(first)
    assert payload["usage"]["total_tokens"]==6
    assert '"event":"APPLY_CHECK_FAILED"' in (tmp_path/"artifacts/two_stage_patch/events.jsonl").read_text(encoding="utf-8")


def test_stage2_provider_rate_limit_is_not_hidden_by_stage1_success(tmp_path,monkeypatch):
    repo,commit,tree,_=_repo(tmp_path)
    first=_payload(_delta(),2)
    second_error={"error":{"message":"rate limited"}}
    request=mock.Mock(side_effect=[(200,{},first),(429,{"retry-after":"7"},second_error)])
    monkeypatch.setenv("CLAY_SWARM_ARTIFACT_ROOT",str(tmp_path/"artifacts"))
    v3=_fake_v3(repo,commit,tree,request);two.install(v3)
    status,headers,payload=v3.fabric.base.request_chat(SimpleNamespace(name="openrouter"),"key","model","stage1",1000,30)
    assert request.call_count==2 and status==429 and headers["retry-after"]=="7"
    assert payload["error"]["message"]=="rate limited" and payload["usage"]["total_tokens"]==2
    assert '"event":"STAGE2_REQUEST_FAILED"' in (tmp_path/"artifacts/two_stage_patch/events.jsonl").read_text(encoding="utf-8")


def test_unsafe_target_never_triggers_second_call(tmp_path,monkeypatch):
    repo,commit,tree,_=_repo(tmp_path)
    first=_payload(_delta(target="../secret.env"),2)
    request=mock.Mock(return_value=(200,{},first))
    monkeypatch.setenv("CLAY_SWARM_ARTIFACT_ROOT",str(tmp_path/"artifacts"))
    v3=_fake_v3(repo,commit,tree,request);two.install(v3)
    _,_,payload=v3.fabric.base.request_chat(SimpleNamespace(name="openrouter"),"key","model","stage1",1000,30)
    assert request.call_count==1 and two._extract_text(payload)==two._extract_text(first)


def test_non_string_target_is_not_coerced_into_a_repository_path(tmp_path,monkeypatch):
    repo,commit,tree,_=_repo(tmp_path)
    first=_payload(_delta(target=123),2)
    request=mock.Mock(return_value=(200,{},first))
    monkeypatch.setenv("CLAY_SWARM_ARTIFACT_ROOT",str(tmp_path/"artifacts"))
    v3=_fake_v3(repo,commit,tree,request);two.install(v3)
    _,_,payload=v3.fabric.base.request_chat(SimpleNamespace(name="openrouter"),"key","model","stage1",1000,30)
    assert request.call_count==1 and two._extract_text(payload)==two._extract_text(first)


def test_source_head_drift_blocks_stage2_instead_of_guessing(tmp_path,monkeypatch):
    repo,commit,tree,_=_repo(tmp_path)
    (repo/"tools/y.py").write_text("Y=1\n",encoding="utf-8");_git(repo,"add","tools/y.py");_git(repo,"commit","-qm","move head")
    first=_payload(_delta(),2)
    request=mock.Mock(return_value=(200,{},first))
    monkeypatch.setenv("CLAY_SWARM_ARTIFACT_ROOT",str(tmp_path/"artifacts"))
    v3=_fake_v3(repo,commit,tree,request);two.install(v3)
    _,_,payload=v3.fabric.base.request_chat(SimpleNamespace(name="openrouter"),"key","model","stage1",1000,30)
    assert request.call_count==1 and two._extract_text(payload)==two._extract_text(first)
    assert '"event":"CONTEXT_REHYDRATION_BLOCKED"' in (tmp_path/"artifacts/two_stage_patch/events.jsonl").read_text(encoding="utf-8")
