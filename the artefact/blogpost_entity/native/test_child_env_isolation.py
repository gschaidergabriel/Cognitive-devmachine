#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENTRY = HERE / "mini_entity.c"
HELPER = HERE / "mini_entity_child_env.inc"
PART02 = HERE / "mini_entity_part02.inc"


def test_native_entry_wires_isolated_execvp_only_around_inference_part() -> None:
    entry = ENTRY.read_text(encoding="utf-8")
    assert '#include "mini_entity_child_env.inc"' in entry
    assert "#define execvp mini_entity_execvp_isolated" in entry
    assert "#undef execvp" in entry
    assert entry.index('#include "mini_entity_child_env.inc"') < entry.index("#define execvp mini_entity_execvp_isolated")
    assert entry.index("#define execvp mini_entity_execvp_isolated") < entry.index('#include "mini_entity_part02.inc"')
    assert entry.index('#include "mini_entity_part02.inc"') < entry.index("#undef execvp")
    assert "execvp(argv[0],argv)" in PART02.read_text(encoding="utf-8")


def test_exact_helper_does_not_forward_ambient_secret_canaries() -> None:
    probe = r'''
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include "mini_entity_child_env.inc"

int main(void){
    int p[2];
    if(pipe(p)!=0) return 10;
    if(setenv("CLAY_AMBIENT_SECRET_CANARY","S3CRET-9f1b",1)!=0) return 11;
    if(setenv("MISTRAL_API_KEY","MISTRAL-CANARY",1)!=0) return 12;
    if(setenv("AWS_SECRET_ACCESS_KEY","AWS-CANARY",1)!=0) return 13;
    pid_t pid=fork();
    if(pid<0) return 14;
    if(pid==0){
        if(dup2(p[1],STDOUT_FILENO)<0) _exit(20);
        close(p[0]); close(p[1]);
        char *argv[]={(char*)"/usr/bin/env",NULL};
        mini_entity_execvp_isolated(argv[0],argv);
        _exit(127);
    }
    close(p[1]);
    char out[32768]; size_t used=0;
    while(used+1<sizeof(out)){
        ssize_t n=read(p[0],out+used,sizeof(out)-1-used);
        if(n<0) return 30;
        if(n==0) break;
        used+=(size_t)n;
    }
    close(p[0]); out[used]=0;
    int st=0; if(waitpid(pid,&st,0)<0) return 31;
    if(!WIFEXITED(st)||WEXITSTATUS(st)!=0) return 32;
    if(strstr(out,"CLAY_AMBIENT_SECRET_CANARY=")) return 40;
    if(strstr(out,"MISTRAL_API_KEY=")) return 41;
    if(strstr(out,"AWS_SECRET_ACCESS_KEY=")) return 42;
    if(!strstr(out,"PATH=")) return 43;
    if(!strstr(out,"LANG=C")) return 44;
    if(!strstr(out,"LC_ALL=C")) return 45;
    if(!strstr(out,"TZ=UTC")) return 46;
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="mini-entity-env-test-") as td:
        td_path = Path(td)
        source = td_path / "probe.c"
        binary = td_path / "probe"
        source.write_text(probe, encoding="utf-8")
        compile_proc = subprocess.run(
            ["gcc", "-O2", "-Wall", "-Wextra", "-Werror", "-I", str(HERE), str(source), "-o", str(binary)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert compile_proc.returncode == 0, compile_proc.stderr
        env = dict(os.environ)
        env["CLAY_AMBIENT_SECRET_CANARY"] = "PARENT-CANARY"
        env["MISTRAL_API_KEY"] = "PARENT-MISTRAL-CANARY"
        env["AWS_SECRET_ACCESS_KEY"] = "PARENT-AWS-CANARY"
        run_proc = subprocess.run(
            [str(binary)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            check=False,
        )
        assert run_proc.returncode == 0, f"rc={run_proc.returncode} stdout={run_proc.stdout!r} stderr={run_proc.stderr!r}"
