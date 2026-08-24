#!/usr/bin/env bash
set -euo pipefail

REPO='gschaidergabriel/clay-global-research-entity'
BASE='/srv/claylab'
CONTROL_BRANCH='chatgpt-vps-control'
RESULTS_BRANCH='chatgpt-vps-results'

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo 'ERROR: run this bootstrap as root' >&2
  exit 2
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git openssh-client podman uidmap slirp4netns fuse-overlayfs python3 sqlite3 jq curl ca-certificates zstd sudo

if ! id claylab >/dev/null 2>&1; then
  useradd -m -d "$BASE" -s /bin/bash claylab
fi
UIDC="$(id -u claylab)"
GIDC="$(id -g claylab)"
loginctl enable-linger claylab >/dev/null 2>&1 || true
systemctl start "user@${UIDC}.service" >/dev/null 2>&1 || true
mkdir -p "/run/user/${UIDC}"
chown claylab:claylab "/run/user/${UIDC}"
chmod 700 "/run/user/${UIDC}"

# Rootless user namespace ranges.
grep -q '^claylab:' /etc/subuid || echo 'claylab:100000:65536' >> /etc/subuid
grep -q '^claylab:' /etc/subgid || echo 'claylab:100000:65536' >> /etc/subgid

install -d -o claylab -g claylab \
  "$BASE/.ssh" "$BASE/git-bridge" "$BASE/workspace" "$BASE/cache" "$BASE/state" "$BASE/artifacts" \
  "$BASE/.config/systemd/user"

KEY="$BASE/.ssh/chatgpt_vps_ed25519"
if [[ ! -s "$KEY" ]]; then
  echo "ERROR: missing deploy private key: $KEY" >&2
  exit 3
fi

# Completely replace the corrupted SSH config. No heredoc nesting through SSH is needed anymore.
ssh-keyscan github.com > "$BASE/.ssh/known_hosts" 2>/dev/null
cat > "$BASE/.ssh/config" <<EOF
Host github.com github-clay-bridge
  HostName github.com
  User git
  IdentityFile $KEY
  IdentitiesOnly yes
  StrictHostKeyChecking yes
  UserKnownHostsFile $BASE/.ssh/known_hosts
EOF
chown -R claylab:claylab "$BASE/.ssh"
chmod 700 "$BASE/.ssh"
chmod 600 "$KEY" "$BASE/.ssh/config" "$BASE/.ssh/known_hosts"
[[ -f "$KEY.pub" ]] && chmod 644 "$KEY.pub" || true

as_clay() {
  runuser -u claylab -- env HOME="$BASE" XDG_RUNTIME_DIR="/run/user/$UIDC" "$@"
}

# This is the only external authentication prerequisite. User already reported this works.
echo '== Git deploy-key probe =='
as_clay git ls-remote "git@github.com:${REPO}.git" HEAD

# Ensure commits from the bridge never fail because identity is missing.
as_clay git config --global user.name 'Clay VPS Bridge'
as_clay git config --global user.email 'clay-vps-bridge@localhost'
as_clay git config --global init.defaultBranch main

clone_or_reset_branch() {
  local dir="$1" branch="$2"
  if [[ ! -d "$dir/.git" ]]; then
    rm -rf "$dir"
    as_clay git clone --filter=blob:none --single-branch --branch "$branch" "git@github.com:${REPO}.git" "$dir"
  else
    as_clay git -C "$dir" remote set-url origin "git@github.com:${REPO}.git"
    as_clay git -C "$dir" fetch origin "$branch" --prune
    as_clay git -C "$dir" checkout -B "$branch" "origin/$branch"
    as_clay git -C "$dir" reset --hard "origin/$branch"
  fi
}

clone_or_reset_branch "$BASE/control-mirror" "$CONTROL_BRANCH"
clone_or_reset_branch "$BASE/results-mirror" "$RESULTS_BRANCH"

WORK="$BASE/workspace/clay-global-research-entity"
if [[ ! -d "$WORK/.git" ]]; then
  rm -rf "$WORK"
  as_clay git clone "git@github.com:${REPO}.git" "$WORK"
else
  as_clay git -C "$WORK" remote set-url origin "git@github.com:${REPO}.git"
  as_clay git -C "$WORK" fetch origin --prune
fi
chown -R claylab:claylab "$BASE/workspace" "$BASE/cache" "$BASE/state" "$BASE/artifacts" "$BASE/git-bridge"

cat > "$BASE/git-bridge/Containerfile" <<'CONTAINER'
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget git git-lfs jq rsync unzip zip tar xz-utils zstd \
    python3 python3-venv python3-pip python3-dev python-is-python3 \
    build-essential cmake ninja-build pkg-config clang lld gdb strace \
    sqlite3 tmux htop ripgrep fd-find tree file less nano vim-tiny \
    procps psmisc lsof iproute2 iputils-ping dnsutils netcat-openbsd \
    openssh-client time && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
ENV HF_HOME=/cache/huggingface
ENV XDG_CACHE_HOME=/cache/xdg
CMD ["sleep","infinity"]
CONTAINER

cat > "$BASE/git-bridge/bridge_daemon.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
import pathlib
import shlex
import sqlite3
import subprocess
import time
import traceback

BASE = pathlib.Path('/srv/claylab')
CONTROL = BASE / 'control-mirror'
RESULTS = BASE / 'results-mirror'
WORK = BASE / 'workspace/clay-global-research-entity'
CACHE = BASE / 'cache'
STATE = BASE / 'state'
ART = BASE / 'artifacts'
DB = STATE / 'bridge.sqlite3'
CONTROL_BRANCH = 'chatgpt-vps-control'
RESULTS_BRANCH = 'chatgpt-vps-results'
QUEUE = pathlib.Path('vps_bridge/commands')
SANDBOX = 'clay-direct-dev'
MAX_TIMEOUT = 14400
MAX_LOG = 512 * 1024
STATE.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def text(b):
    return (b or b'').decode('utf-8', 'replace')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(argv, timeout=120, cwd=None):
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, cwd=cwd)


def git(repo, *args, timeout=180, check=True):
    p = run(['git', '-C', str(repo), *args], timeout=timeout)
    if check and p.returncode:
        raise RuntimeError('GIT_FAILED: ' + text(p.stderr)[-6000:])
    return p


def conn():
    c = sqlite3.connect(DB)
    c.execute('CREATE TABLE IF NOT EXISTS done(id TEXT PRIMARY KEY, command_sha TEXT NOT NULL, finished TEXT NOT NULL, code INTEGER NOT NULL)')
    c.commit()
    return c


def ensure_box():
    p = run(['podman', 'inspect', '-f', '{{.State.Running}}', SANDBOX], timeout=20)
    if p.returncode == 0 and text(p.stdout).strip() == 'true':
        return
    p = run(['podman', 'start', SANDBOX], timeout=90)
    if p.returncode:
        raise RuntimeError('SANDBOX_START_FAILED: ' + text(p.stderr))


def sexec(command, cwd='/workspace', timeout=3600):
    ensure_box()
    return run(['podman', 'exec', '-w', cwd, SANDBOX, 'bash', '-lc', command], timeout=timeout)


def sync_control():
    git(CONTROL, 'fetch', 'origin', CONTROL_BRANCH, '--prune')
    git(CONTROL, 'checkout', '-B', CONTROL_BRANCH, f'origin/{CONTROL_BRANCH}')
    git(CONTROL, 'reset', '--hard', f'origin/{CONTROL_BRANCH}')


def sync_results():
    git(RESULTS, 'fetch', 'origin', RESULTS_BRANCH, '--prune')
    git(RESULTS, 'checkout', '-B', RESULTS_BRANCH, f'origin/{RESULTS_BRANCH}')
    git(RESULTS, 'reset', '--hard', f'origin/{RESULTS_BRANCH}')


def push_results(message, live=False):
    git(RESULTS, 'add', 'vps_bridge/results', check=False)
    if git(RESULTS, 'diff', '--cached', '--quiet', check=False).returncode == 0:
        return
    if live:
        subj = text(git(RESULTS, 'log', '-1', '--pretty=%s', check=False).stdout).strip()
        if subj.startswith('vps live telemetry'):
            git(RESULTS, 'commit', '--amend', '--no-edit')
            git(RESULTS, 'push', '--force-with-lease', 'origin', f'HEAD:{RESULTS_BRANCH}', timeout=300)
            return
    git(RESULTS, 'commit', '-m', message)
    git(RESULTS, 'push', 'origin', f'HEAD:{RESULTS_BRANCH}', timeout=300)


def rel(value):
    p = pathlib.PurePosixPath(str(value))
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('RELATIVE_PATH_REQUIRED')
    return str(p)


def status_payload():
    ensure_box()
    host = {}
    probes = {
        'uptime': ['uptime'],
        'memory': ['free', '-b'],
        'disk': ['df', '-B1', '/srv/claylab'],
        'podman': ['podman', 'stats', '--no-stream', '--format', 'json', SANDBOX],
    }
    for name, argv in probes.items():
        p = run(argv, timeout=30)
        host[name] = {'rc': p.returncode, 'out': text(p.stdout)[-12000:], 'err': text(p.stderr)[-2000:]}
    p = sexec("ps auxww --sort=-%cpu | head -80; echo '---'; free -h; echo '---'; df -h /workspace /cache", timeout=30)
    head = text(git(WORK, 'rev-parse', 'HEAD', check=False).stdout).strip() if WORK.exists() else ''
    gs = text(git(WORK, 'status', '--short', '--branch', check=False).stdout)[-16000:] if WORK.exists() else ''
    find = run(['bash', '-lc', "find /srv/claylab/workspace /srv/claylab/cache -type f \\( -iname '*.gguf' -o -iname '*.safetensors' -o -iname '*.onnx' -o -iname '*.pt' -o -iname '*.pth' \\) -printf '%s %p\\n' 2>/dev/null | head -200"], timeout=30)
    models = text(find.stdout).splitlines()
    return {
        'schema': 'CLAY_VPS_LIVE/v4',
        'observed_at': now(),
        'sandbox': SANDBOX,
        'host': host,
        'processes': text(p.stdout)[-24000:],
        'workspace_git': {'head': head, 'status': gs},
        'models': models,
    }


def operate(s):
    op = str(s.get('op', 'exec'))
    timeout = min(max(int(s.get('timeout_seconds', 3600)), 1), MAX_TIMEOUT)
    if op == 'exec':
        return sexec(str(s['command']), str(s.get('cwd', '/workspace')), timeout), {}
    if op == 'status':
        b = json.dumps(status_payload(), indent=2).encode()
        return subprocess.CompletedProcess(['status'], 0, b, b''), {}
    if op == 'fetch':
        dest = rel(s['dest'])
        url = str(s['url'])
        expected = s.get('sha256')
        q = '/workspace/' + dest
        cmd = f"set -euo pipefail; mkdir -p $(dirname {shlex.quote(q)}); curl -fL --retry 5 --retry-delay 2 --continue-at - {shlex.quote(url)} -o {shlex.quote(q)}; sha256sum {shlex.quote(q)}"
        p = sexec(cmd, timeout=timeout)
        if p.returncode == 0 and expected:
            actual = text(p.stdout).strip().split()[0]
            if actual != expected:
                p = subprocess.CompletedProcess(p.args, 72, p.stdout, (p.stderr or b'') + f'\nSHA256_MISMATCH expected={expected} actual={actual}\n'.encode())
        return p, {}
    if op == 'git':
        dest = rel(s['dest'])
        url = str(s['url'])
        ref = s.get('ref')
        q = '/workspace/' + dest
        cmd = f"set -euo pipefail; if [ -d {shlex.quote(q + '/.git')} ]; then git -C {shlex.quote(q)} fetch --all --tags --prune; else git clone {shlex.quote(url)} {shlex.quote(q)}; fi;"
        if ref:
            cmd += f" git -C {shlex.quote(q)} checkout {shlex.quote(str(ref))};"
        cmd += f" git -C {shlex.quote(q)} rev-parse HEAD"
        return sexec(cmd, timeout=timeout), {}
    if op == 'canonical_sync':
        ref = str(s.get('ref', 'main'))
        git(WORK, 'fetch', 'origin', '--prune', timeout=600)
        p = git(WORK, 'checkout', ref, check=False)
        if p.returncode:
            git(WORK, 'checkout', '-B', ref, f'origin/{ref}')
        if ref == 'main':
            git(WORK, 'reset', '--hard', 'origin/main')
        h = text(git(WORK, 'rev-parse', 'HEAD').stdout).strip()
        return subprocess.CompletedProcess(['canonical_sync'], 0, (h + '\n').encode(), b''), {'head': h, 'ref': ref}
    if op == 'write_text':
        p = BASE / 'workspace' / rel(s['path'])
        p.parent.mkdir(parents=True, exist_ok=True)
        data = str(s.get('content', '')).encode()
        p.write_bytes(data)
        return subprocess.CompletedProcess(['write_text'], 0, f'WROTE {p}\n'.encode(), b''), {'sha256': sha(data), 'bytes': len(data)}
    if op == 'read_file':
        p = BASE / 'workspace' / rel(s['path'])
        data = p.read_bytes()
        return subprocess.CompletedProcess(['read_file'], 0, data[:MAX_LOG], b''), {'sha256': sha(data), 'bytes': len(data), 'truncated': len(data) > MAX_LOG}
    if op == 'publish_branch':
        branch = str(s['branch'])
        if not branch.startswith('chatgpt-vps-work/'):
            raise ValueError('BAD_WORK_BRANCH')
        git(WORK, 'checkout', '-B', branch)
        git(WORK, 'add', '-A')
        if git(WORK, 'diff', '--cached', '--quiet', check=False).returncode != 0:
            git(WORK, 'commit', '-m', str(s.get('message', 'ChatGPT VPS work')))
        git(WORK, 'push', '-u', 'origin', f'HEAD:{branch}', timeout=300)
        h = text(git(WORK, 'rev-parse', 'HEAD').stdout).strip()
        return subprocess.CompletedProcess(['publish_branch'], 0, (h + '\n').encode(), b''), {'branch': branch, 'head': h}
    raise ValueError('UNSUPPORTED_OP:' + op)


def publish_receipt(receipt, stdout, stderr):
    d = RESULTS / 'vps_bridge/results'
    (d / 'receipts').mkdir(parents=True, exist_ok=True)
    (d / 'logs').mkdir(parents=True, exist_ok=True)
    cid = receipt['command_id']
    (d / 'receipts' / f'{cid}.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (d / 'logs' / f'{cid}.stdout.txt').write_bytes(stdout[-MAX_LOG:])
    (d / 'logs' / f'{cid}.stderr.txt').write_bytes(stderr[-MAX_LOG:])
    (d / 'LATEST.json').write_text(json.dumps(receipt, indent=2) + '\n')
    push_results('vps receipt: ' + cid, live=False)


def execute(path):
    raw = path.read_bytes()
    s = json.loads(raw)
    if s.get('schema') not in ('CLAY_VPS_COMMAND/v3', 'CLAY_VPS_COMMAND/v4'):
        raise ValueError('BAD_SCHEMA')
    cid = str(s['command_id'])
    c = conn()
    if c.execute('SELECT 1 FROM done WHERE id=?', (cid,)).fetchone():
        c.close()
        return False
    started = now()
    stdout = stderr = b''
    meta = {}
    try:
        p, meta = operate(s)
        code = p.returncode
        stdout = p.stdout or b''
        stderr = p.stderr or b''
        st = 'PASS' if code == 0 else 'FAIL'
    except subprocess.TimeoutExpired as e:
        code = 124
        st = 'TIMEOUT'
        stdout = e.stdout or b''
        stderr = (e.stderr or b'') + repr(e).encode()
    except Exception as e:
        code = 125
        st = 'ERROR'
        stderr = (repr(e) + '\n' + traceback.format_exc()).encode()
    receipt = {
        'schema': 'CLAY_VPS_RECEIPT/v4',
        'command_id': cid,
        'command_sha256': sha(raw),
        'started_at': started,
        'finished_at': now(),
        'status': st,
        'exit_code': code,
        'op': s.get('op', 'exec'),
        'stdout_sha256': sha(stdout),
        'stderr_sha256': sha(stderr),
        'stdout_tail': text(stdout)[-24000:],
        'stderr_tail': text(stderr)[-24000:],
        'meta': meta,
        'execution_boundary': 'ROOT_INSIDE_ROOTLESS_PODMAN_OR_EXPLICIT_REPO_CONTROL_OP',
        'canonical_credit_minted': 0,
    }
    sync_results()
    publish_receipt(receipt, stdout, stderr)
    c.execute('INSERT INTO done VALUES(?,?,?,?)', (cid, sha(raw), now(), code))
    c.commit()
    c.close()
    return True


def publish_live():
    sync_results()
    d = RESULTS / 'vps_bridge/results'
    d.mkdir(parents=True, exist_ok=True)
    (d / 'LIVE.json').write_text(json.dumps(status_payload(), indent=2) + '\n')
    push_results('vps live telemetry', live=True)


def publish_daemon_error(exc):
    try:
        sync_results()
        d = RESULTS / 'vps_bridge/results'
        d.mkdir(parents=True, exist_ok=True)
        payload = {'schema': 'CLAY_VPS_DAEMON_ERROR/v1', 'observed_at': now(), 'error': repr(exc), 'traceback': traceback.format_exc()[-20000:]}
        (d / 'DAEMON_ERROR.json').write_text(json.dumps(payload, indent=2) + '\n')
        push_results('vps daemon error', live=False)
    except Exception:
        pass


def main():
    # Prove the return channel immediately at startup.
    try:
        publish_live()
    except Exception as e:
        publish_daemon_error(e)
    last_live = time.time()
    while True:
        try:
            sync_control()
            q = CONTROL / QUEUE
            if q.exists():
                for p in sorted(q.glob('*.json')):
                    if execute(p):
                        break
            if time.time() - last_live >= 60:
                publish_live()
                last_live = time.time()
        except Exception as e:
            publish_daemon_error(e)
        time.sleep(5)


if __name__ == '__main__':
    main()
PY
chmod 755 "$BASE/git-bridge/bridge_daemon.py"
chown -R claylab:claylab "$BASE/git-bridge"

cat > "$BASE/.config/systemd/user/clay-vps-git-bridge.service" <<'SERVICE'
[Unit]
Description=Clay ChatGPT direct Git VPS bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=HOME=/srv/claylab
ExecStart=/usr/bin/python3 /srv/claylab/git-bridge/bridge_daemon.py
WorkingDirectory=/srv/claylab
Restart=always
RestartSec=2
Nice=5

[Install]
WantedBy=default.target
SERVICE
chown claylab:claylab "$BASE/.config/systemd/user/clay-vps-git-bridge.service"

# Rebuild the sandbox from a known-good rootless image. Container root maps to claylab on the host.
echo '== Rebuilding rootless development sandbox =='
as_clay podman rm -f clay-direct-dev >/dev/null 2>&1 || true
as_clay podman build --pull=missing -t localhost/clay-direct-dev:ubuntu24 -f "$BASE/git-bridge/Containerfile" "$BASE/git-bridge"
as_clay podman run -d --name clay-direct-dev \
  --pids-limit=4096 --cpus=4 --memory=12g --memory-swap=12g \
  -v "$BASE/workspace:/workspace:rw" \
  -v "$BASE/cache:/cache:rw" \
  -v "$BASE/artifacts:/artifacts:rw" \
  localhost/clay-direct-dev:ubuntu24

# Basic in-sandbox proof before daemon startup.
as_clay podman exec clay-direct-dev bash -lc 'set -e; id; touch /workspace/.bridge-rw-test; rm /workspace/.bridge-rw-test; curl -fsSI https://github.com >/dev/null; git --version; python3 --version; sqlite3 --version'

as_clay systemctl --user daemon-reload
as_clay systemctl --user enable --now clay-vps-git-bridge.service

# Final checks.
echo '== Final selftest =='
as_clay git -C "$BASE/control-mirror" fetch origin "$CONTROL_BRANCH" >/dev/null
as_clay git -C "$BASE/results-mirror" fetch origin "$RESULTS_BRANCH" >/dev/null
[[ "$(as_clay podman inspect -f '{{.State.Running}}' clay-direct-dev)" == 'true' ]]
[[ "$(as_clay systemctl --user is-active clay-vps-git-bridge.service)" == 'active' ]]

# Wait for daemon to publish LIVE.json to the result branch.
OK=0
for _ in $(seq 1 20); do
  sleep 2
  as_clay git -C "$BASE/results-mirror" fetch origin "$RESULTS_BRANCH" >/dev/null 2>&1 || true
  if as_clay git -C "$BASE/results-mirror" show "origin/${RESULTS_BRANCH}:vps_bridge/results/LIVE.json" >/tmp/clay-live.json 2>/dev/null; then
    OK=1
    break
  fi
done
if [[ "$OK" != 1 ]]; then
  echo 'ERROR: bridge service is running but LIVE.json was not observed on results branch' >&2
  as_clay systemctl --user --no-pager -l status clay-vps-git-bridge.service || true
  as_clay journalctl --user -u clay-vps-git-bridge.service -n 100 --no-pager || true
  exit 50
fi

cat /tmp/clay-live.json | head -c 4000 || true
echo
echo 'SELFTEST_PASS'
echo 'CHATGPT_VPS_BRIDGE_READY'
