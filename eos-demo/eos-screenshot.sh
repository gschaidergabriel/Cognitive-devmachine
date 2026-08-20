#!/usr/bin/env bash
# eos-screenshot.sh -- host-side executor for the Andreas-demo screenshot flow.
#
# Runs on frank-api (the VPS host, NOT inside the entityos container). The
# entityos container has no ssh client, no credential for andreas-MACO, and a
# read-only rootfs -- so it cannot do this itself. This script is the proxy
# the container is missing (see CHECK REACH finding in the delivery notes).
#
# Contract (how Zero triggers this):
#   1. Zero (native Bash, inside the container) writes a request file to the
#      shared rw bind mount:
#        /var/lib/clay/eos-demo-requests/<id>.json
#        { "html_b64": "<base64 of the page to render>", "slug": "<id>" }
#      (base64 avoids any quoting/escaping problem with arbitrary HTML.)
#   2. Something on the HOST with andreas-MACO credentials runs:
#        eos-screenshot.sh <id>
#      which reads that request, drives the flow below, and writes the
#      result back to:
#        /var/lib/clay/eos-demo-requests/<id>.done.json
#        { "ok": true, "image_url": "/web/chat/demo-bilder/<id>.png" }
#   3. Zero (native Bash) polls/reads that .done.json file to know the image
#      landed, and can then hand image_url to the chat backend as
#      payload.image = {url, alt, label} (see web/chat/index.html change).
#
# STAND 2026-08-20: der Beobachter EXISTIERT inzwischen. eos-demo-screenshot.path
# horcht auf /var/lib/clay/eos-demo-requests und startet eos-demo-dispatch.sh,
# das diesen Befehl fuer jeden noch offenen Auftrag ausfuehrt. Der Absatz, der
# hier stand, sagte das Gegenteil -- ein veralteter Kommentar ueber eine
# Sicherheitsgrenze ist gefaehrlicher als gar keiner, deshalb ersetzt statt
# ergaenzt. Ein Mensch muss nichts mehr anstossen: Zero legt den Auftrag ab
# (runtime_CLAUDE.md 9j), der Wirt fuehrt ihn aus.
#
# Usage: eos-screenshot.sh <request-id>
set -euo pipefail

REQ_DIR="/var/lib/clay/eos-demo-requests"
WEB_OUT_DIR="/opt/entityos/the artefact/web/chat/demo-bilder"
ANDREAS_HOST="andreas@100.92.234.52"
ANDREAS_DIR="eos-demo"        # relative to andreas' $HOME -- the only dir we touch there

id="${1:?usage: eos-screenshot.sh <request-id>}"
req="$REQ_DIR/$id.json"
[ -f "$req" ] || { echo "no such request: $req" >&2; exit 1; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT   # local temp dir on the HOST -- not a remote rm, fine

python3 -c "
import json,base64,sys
d=json.load(open('$req'))
open('$tmp/page.html','wb').write(base64.b64decode(d['html_b64']))
"

# 4) write the page on Andreas' PC, ONLY inside ~/eos-demo/
ssh "$ANDREAS_HOST" "mkdir -p ~/$ANDREAS_DIR"
scp -q "$tmp/page.html" "$ANDREAS_HOST:$ANDREAS_DIR/$id.html"

# 5) headless screenshot, run there (chromium writes the file itself --
#    no shell redirect involved)
ssh "$ANDREAS_HOST" "/snap/bin/chromium --headless --disable-gpu --no-sandbox \
  --window-size=1000,700 --screenshot=\$HOME/$ANDREAS_DIR/$id.png \
  file://\$HOME/$ANDREAS_DIR/$id.html"

# 6) bring the png back to the VPS
scp -q "$ANDREAS_HOST:$ANDREAS_DIR/$id.png" "$tmp/$id.png"

# 7) publish it where the chat's static server already serves from
mkdir -p "$WEB_OUT_DIR"
cp "$tmp/$id.png" "$WEB_OUT_DIR/$id.png"

# 8) tell Zero it's ready
echo "{\"ok\": true, \"image_url\": \"/web/chat/demo-bilder/$id.png\"}" > "$REQ_DIR/$id.done.json"
echo "done: /web/chat/demo-bilder/$id.png"
