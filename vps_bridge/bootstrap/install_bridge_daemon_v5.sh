#!/usr/bin/env bash
set -euo pipefail
BASE=/srv/claylab
SRC="$BASE/control-mirror/vps_bridge/bootstrap/bridge_daemon_v5.py"
DST="$BASE/git-bridge/bridge_daemon.py"
UIDC="$(id -u claylab)"
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo 'ERROR: root required' >&2
  exit 2
fi
if [[ ! -f "$SRC" ]]; then
  echo "ERROR: missing $SRC" >&2
  exit 3
fi
python3 -m py_compile "$SRC"
cp -a "$DST" "$DST.pre-v5.$(date -u +%Y%m%dT%H%M%SZ)"
install -o claylab -g claylab -m 0755 "$SRC" "$DST"
runuser -u claylab -- env HOME="$BASE" XDG_RUNTIME_DIR="/run/user/$UIDC" systemctl --user restart clay-vps-git-bridge.service
sleep 2
runuser -u claylab -- env HOME="$BASE" XDG_RUNTIME_DIR="/run/user/$UIDC" systemctl --user --no-pager --full status clay-vps-git-bridge.service
python3 - <<'PY'
import sqlite3
p='/srv/claylab/state/bridge.sqlite3'
c=sqlite3.connect(p)
print('done_rows', c.execute('select count(*) from done').fetchone()[0])
print('invalid_rows', c.execute('select count(*) from invalid').fetchone()[0] if c.execute("select count(*) from sqlite_master where type='table' and name='invalid'").fetchone()[0] else 0)
c.close()
PY
echo BRIDGE_V5_INSTALL_PASS
