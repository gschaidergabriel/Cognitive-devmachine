#!/usr/bin/env python3
import hashlib, json, os, random, shutil, subprocess, tempfile
from pathlib import Path

def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)

def main():
    gcc = shutil.which('gcc')
    clang = shutil.which('clang')
    if not gcc or not clang:
        raise SystemExit('gcc and clang required')
    gcc_v = run([gcc,'--version']).stdout.splitlines()[0]
    clang_v = run([clang,'--version']).stdout.splitlines()[0]
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); a=root/'a'; b=root/'b'; a.mkdir(); b.mkdir()
        src='''#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\nint main(int argc,char**argv){if(argc!=4)return 64; long a=strtol(argv[2],0,10),b=strtol(argv[3],0,10),r=0; if(strcmp(argv[1],"add")==0)r=a+b; else if(strcmp(argv[1],"sub")==0)r=a-b; else if(strcmp(argv[1],"mul")==0)r=a*b; else return 65; printf("%ld\\n",r); return 0;}\n'''
        for d in (a,b): (d/'tool.c').write_text(src)
        run([gcc,'-O2','-s',str(a/'tool.c'),'-o',str(a/'tool')])
        run([gcc,'-O2','-s',str(b/'tool.c'),'-o',str(b/'tool')])
        run([clang,'-O2','-s',str(a/'tool.c'),'-o',str(a/'tool.clang')])
        hga,hgb,hc=sha256(a/'tool'),sha256(b/'tool'),sha256(a/'tool.clang')
        rng=random.Random(202608091813)
        mismatches=0
        for _ in range(5000):
            op=rng.choice(['add','sub','mul']); x=rng.randint(-100000,100000); y=rng.randint(-100000,100000)
            og=run([str(a/'tool'),op,str(x),str(y)]).stdout
            oc=run([str(a/'tool.clang'),op,str(x),str(y)]).stdout
            mismatches += og != oc
        path_src='#include <stdio.h>\nint main(void){ puts(__FILE__); return 0; }\n'
        for d in (a,b): (d/'path.c').write_text(path_src)
        run([gcc,'-O2','-s',str(a/'path.c'),'-o',str(a/'path')])
        run([gcc,'-O2','-s',str(b/'path.c'),'-o',str(b/'path')])
        hpa,hpb=sha256(a/'path'),sha256(b/'path')
        run([gcc,'-O2','-s',f'-ffile-prefix-map={a}=/src',str(a/'path.c'),'-o',str(a/'path.norm')])
        run([gcc,'-O2','-s',f'-ffile-prefix-map={b}=/src',str(b/'path.c'),'-o',str(b/'path.norm')])
        hnpa,hnpb=sha256(a/'path.norm'),sha256(b/'path.norm')
        out={
          'evidence_class':'LOCAL_ISOLATED_LINUX_EXECUTION_NOT_TARGET_UBUNTU_ACCEPTANCE',
          'gcc_version':gcc_v,'clang_version':clang_v,
          'same_source_same_compiler_different_dirs_binary_equal':hga==hgb,
          'gcc_hash_a':hga,'gcc_hash_b':hgb,
          'diverse_compilers_binary_equal':hga==hc,'clang_hash':hc,
          'diverse_compilers_semantic_cases':5000,'diverse_compilers_semantic_mismatches':mismatches,
          'path_sensitive_binary_equal':hpa==hpb,'path_hash_a':hpa,'path_hash_b':hpb,
          'normalized_path_binary_equal':hnpa==hnpb,'normalized_path_hash_a':hnpa,'normalized_path_hash_b':hnpb,
          'path_output_a':run([str(a/'path')]).stdout.strip(),
          'path_output_b':run([str(b/'path')]).stdout.strip(),
          'normalized_path_output_a':run([str(a/'path.norm')]).stdout.strip(),
          'normalized_path_output_b':run([str(b/'path.norm')]).stdout.strip(),
          'seed_semantic_differential':202608091813,
        }
        print(json.dumps(out, indent=2, sort_keys=True))
if __name__=='__main__': main()
