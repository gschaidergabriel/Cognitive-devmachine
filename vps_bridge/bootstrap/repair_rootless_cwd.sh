#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/repair_and_start.sh"
TMP="$(mktemp /tmp/clay-repair-and-start.XXXXXX.sh)"
trap 'rm -f "$TMP"' EXIT

python3 - "$SRC" "$TMP" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text()
old = '''as_clay() {
  runuser -u claylab -- env HOME="$BASE" XDG_RUNTIME_DIR="/run/user/$UIDC" "$@"
}
'''
new = '''as_clay() {
  # runuser inherits root's current directory. Podman fails before startup if that
  # directory is /root because claylab cannot chdir there. Enter claylab's home
  # before dropping privileges so every rootless Podman/systemd invocation has a
  # readable working directory.
  ( cd "$BASE" && runuser -u claylab -- env HOME="$BASE" XDG_RUNTIME_DIR="/run/user/$UIDC" "$@" )
}
'''
if old not in src:
    raise SystemExit('ERROR: expected as_clay block not found; refusing blind patch')
Path(sys.argv[2]).write_text(src.replace(old, new, 1))
PY

chmod 755 "$TMP"
echo '== Applying rootless cwd repair =='
exec bash "$TMP"
