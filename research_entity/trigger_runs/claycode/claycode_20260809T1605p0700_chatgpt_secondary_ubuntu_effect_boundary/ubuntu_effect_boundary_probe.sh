#!/usr/bin/env bash
set -euo pipefail

WORK="${TMPDIR:-/tmp}/claycode_effect_probe"
rm -rf "$WORK"
mkdir -p "$WORK/allowed" "$WORK/denied" "$WORK/root/allowed"
printf 'ALLOWED\n' > "$WORK/allowed/a.txt"
printf 'DENIED\n' > "$WORK/denied/d.txt"

cat > "$WORK/landlock_probe.c" <<'EOF'
#define _GNU_SOURCE
#include <errno.h>
#include <linux/landlock.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>
static int ll_create(const struct landlock_ruleset_attr *a,size_t s,__u32 f){return syscall(__NR_landlock_create_ruleset,a,s,f);} 
int main(void){int abi=ll_create(NULL,0,LANDLOCK_CREATE_RULESET_VERSION); if(abi<0){printf("LANDLOCK_ABI=UNAVAILABLE errno=%d(%s)\n",errno,strerror(errno)); return 3;} printf("LANDLOCK_ABI=%d\n",abi); return 0;}
EOF

gcc -static -O2 "$WORK/landlock_probe.c" -o "$WORK/landlock_probe"
set +e
"$WORK/landlock_probe"
LANDLOCK_EXIT=$?
set -e

cat > "$WORK/cap_probe.c" <<'EOF'
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
static void r(const char*p){errno=0;int fd=open(p,O_RDONLY|O_CLOEXEC),e=errno;if(fd>=0)close(fd);printf("READ %s %s errno=%d(%s)\n",p,fd>=0?"ALLOW":"DENY",e,strerror(e));}
static void w(const char*p){errno=0;int fd=open(p,O_WRONLY|O_APPEND|O_CLOEXEC),e=errno;if(fd>=0)close(fd);printf("WRITE %s %s errno=%d(%s)\n",p,fd>=0?"ALLOW":"DENY",e,strerror(e));}
int main(void){r("/allowed/a.txt");w("/allowed/a.txt");r("/etc/passwd");return 0;}
EOF

gcc -static -O2 "$WORK/cap_probe.c" -o "$WORK/cap_probe"
cp "$WORK/cap_probe" "$WORK/root/probe"

printf '%s\n' '--- UNSANDBOXED AMBIENT BASELINE ---'
python3 - <<PY
for p,m in [("$WORK/allowed/a.txt","r"),("$WORK/allowed/a.txt","a"),("/etc/passwd","r")]:
    try:
        with open(p,m): pass
        print(m,p,"ALLOW")
    except Exception as e:
        print(m,p,"DENY",type(e).__name__,str(e))
PY

printf '%s\n' '--- CAP_READ_ONLY ---'
unshare -Urnm sh -ceu "mount --make-rprivate /; mount --bind '$WORK/allowed' '$WORK/root/allowed'; mount -o remount,bind,ro '$WORK/root/allowed'; chroot '$WORK/root' /probe"

printf '%s\n' '--- CAP_NONE ---'
unshare -Urnm sh -ceu "mount --make-rprivate /; chroot '$WORK/root' /probe"

printf 'LANDLOCK_EXIT=%s\n' "$LANDLOCK_EXIT"
sha256sum "$WORK/landlock_probe.c" "$WORK/landlock_probe" "$WORK/cap_probe.c" "$WORK/cap_probe"
