#!/bin/bash
# chatgpt_burst_worker_v2.sh
#
# v2 of chatgpt_burst_worker.sh. Key change vs v1: SEQUENTIAL single-tab
# discipline instead of many tabs open in parallel (v1 left 65 tabs open,
# crashed Chrome, ate all RAM). v2 rules:
#   - max 1 tab open at almost all times (briefly 2 during tab-recycle swap)
#   - resource guard checked before every worker (free RAM + tab count)
#   - hard hardware ceiling: if $B tabs ever shows >3 lines, force-close
#   - send verified by URL change (.../project -> .../c/<id>), not by
#     "no rate-limit modal" (v1's modal check was too pessimistic/unreliable)
#   - conversations are NOT polled to completion inline. Sent URLs are
#     recorded to a state file; a separate --harvest run opens them later,
#     one at a time, to check/collect results.
#
# Usage:
#   Send phase (default):
#     NUM_WORKERS=30 SLEEP_BETWEEN_WORKERS=2 ~/scripts/chatgpt_burst_worker_v2.sh
#   Harvest phase (separate, later, on saved URLs):
#     ~/scripts/chatgpt_burst_worker_v2.sh --harvest
#
# Config knobs (env vars, all optional):
#   NUM_WORKERS            default 30   - how many triggerwort2 sends to attempt
#   SLEEP_BETWEEN_WORKERS  default 2    - seconds between workers
#   RAM_THRESHOLD_MB       default 2000 - min available RAM (MB) required to proceed
#   TAB_RECYCLE_EVERY      default 5    - close+reopen fresh tab every N workers
#   TAB_HARDLIMIT          default 3    - if $B tabs ever exceeds this many lines, panic-close

set -uo pipefail

export PATH="$HOME/.bun/bin:$PATH"
B="$HOME/.claude/skills/gstack/browse/dist/browse"

# gstack browse scopes its daemon (+ browser context + cookies) to the
# CALLER'S cwd (~/.gstack/browse.json vs <other-dir>/.gstack/browse.json are
# separate daemons with separate logins). Pin to $HOME explicitly so this
# script always talks to the same daemon regardless of where it's invoked
# from — discovered the hard way: invoking from a different cwd silently
# creates/uses a brand-new, unauthenticated daemon.
cd "$HOME" || { echo "FATAL: cannot cd to \$HOME"; exit 1; }

PROJECT_URL="https://chatgpt.com/g/g-p-6a7644f542508191b324659134fb593b/project"
STATE_DIR="$HOME/scripts/chatgpt_burst_state"
# TRIGGER overridable via env (stern.py chatgpt-senden wrapper sets this
# per distinct prompt text); default unchanged from original v2 behavior.
TRIGGER="${TRIGGER:-triggerwort2}"

NUM_WORKERS="${NUM_WORKERS:-30}"
SLEEP_BETWEEN_WORKERS="${SLEEP_BETWEEN_WORKERS:-2}"
RAM_THRESHOLD_MB="${RAM_THRESHOLD_MB:-2000}"
TAB_RECYCLE_EVERY="${TAB_RECYCLE_EVERY:-5}"
TAB_HARDLIMIT="${TAB_HARDLIMIT:-3}"
# Gabriel, 2026-08-26 (verbally, re-confirmed 2026-08-27): after spawning a
# burst of workers, a real ChatGPT rate-limit needs a STUBBORN wait of 5-7
# minutes before it clears -- the previous single fixed 90s here was too
# short and just ran straight into Phase B still blocked. 360s = 6min,
# middle of that band. Overridable for testing.
RATE_LIMIT_WAIT_S="${RATE_LIMIT_WAIT_S:-360}"

INPUT_SEL='#prompt-textarea'
SEND_SEL='[data-testid="send-button"]'
DISMISS_SEL='button:has-text("Got it")'
RATE_LIMIT_TEXT="Too many requests"
# LESSON (2026-08-27, found live via a real multi-paragraph review $TRIGGER):
# `$B type` is Playwright's page.keyboard.type(), which sends every char as
# a real keypress -- a literal newline (0x0A) inside $TRIGGER is typed as an
# actual Enter keypress, and ChatGPT's compose box submits-on-Enter (only
# Shift+Enter inserts a newline). A multi-line $TRIGGER therefore gets
# submitted PARTWAY THROUGH typing, the box goes empty, and the script's
# own text-match retry logic marks it FAILED_TYPE even though a (truncated,
# garbage) message actually went out. Callers (incl. stern.py chatgpt-senden
# --prompts) MUST pass single-line $TRIGGER text -- join paragraphs with
# " " or " || ", never a real newline. Literal two-char "\n" (backslash+n,
# e.g. inside a quoted training-sample excerpt) is fine, that's not 0x0A.

mkdir -p "$STATE_DIR"
RUN_TS="$(date +%Y%m%d_%H%M%S)"
LOG="$STATE_DIR/burst_v2_${RUN_TS}.log"
SENT_URLS_FILE="$STATE_DIR/sent_urls_v2.txt"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

# ---------------------------------------------------------------------------
# helpers: tab bookkeeping
# ---------------------------------------------------------------------------
tab_ids() {
    $B tabs 2>/dev/null | grep -oP '\[\K[0-9]+(?=\])'
}

active_tab_id() {
    local id
    id=$($B tabs 2>/dev/null | grep '→' | grep -oP '\[\K[0-9]+(?=\])')
    if [ -z "$id" ]; then
        id=$(tab_ids | tail -1)
    fi
    echo "$id"
}

close_all_except() {
    local keep="$1"
    local id
    for id in $(tab_ids); do
        if [ "$id" != "$keep" ]; then
            $B closetab "$id" >>"$LOG" 2>&1
            log "closed stray tab $id (keeping $keep)"
        fi
    done
}

enforce_tab_hardlimit() {
    local keep="$1"
    local n
    n=$(tab_ids | wc -l)
    if [ "$n" -gt "$TAB_HARDLIMIT" ]; then
        log "BUG_FOUND: tab hardlimit exceeded ($n tabs open, limit=$TAB_HARDLIMIT), force-closing all but $keep"
        close_all_except "$keep"
    fi
}

# ---------------------------------------------------------------------------
# CRITICAL: gstack browse's root/local CLI can NEVER recover from 0 open
# tabs. getActiveSession() (server.ts) is called unconditionally for every
# command except a scoped-token newtab path we don't use — so if the tab
# count ever hits 0, goto/newtab/tabs/text/etc. all fail with "No active
# page" forever, and the only fix is restarting the whole daemon process,
# which throws away the in-memory browser context and any imported cookies
# (confirmed by hand during v2 testing: a bricked daemon needed a full
# cookie-import-browser re-run to get chatgpt.com auth back at all, and
# even then Cloudflare's Turnstile challenge did not reliably clear on the
# fresh headless fingerprint). NEVER call close_all_except with a sentinel
# that matches no real tab id ("__none__") — that was v1-of-v2's bug and it
# bricked a real login. Always reuse an existing tab as the anchor; only
# ever ADD a tab (newtab) while at least one other tab is still alive, then
# close the old one after the new one is confirmed.
# ---------------------------------------------------------------------------
ensure_single_tab_at() {
    local url="$1"
    local ids first
    ids=$(tab_ids)
    if [ -z "$ids" ]; then
        log "FATAL: 0 tabs open on this daemon. This is NOT recoverable via the CLI (root client always needs an active page) — restarting the daemon would also drop the browser context/cookies. Manual fix needed (re-run cookie-import) before this script can proceed."
        return 1
    fi
    first=$(echo "$ids" | head -1)
    if [ "$(echo "$ids" | wc -l)" -gt 1 ]; then
        close_all_except "$first"
    fi
    $B tab "$first" >>"$LOG" 2>&1
    $B goto "$url" >>"$LOG" 2>&1
    CURRENT_TAB="$first"
    return 0
}

# ---------------------------------------------------------------------------
# helper: resource guard. Returns 0 = ok to proceed, 1 = abort cycle.
# ---------------------------------------------------------------------------
resource_guard() {
    local avail
    avail=$(free -m | awk '/^Mem:/{print $7}')
    if [ "$avail" -ge "$RAM_THRESHOLD_MB" ]; then
        return 0
    fi

    log "RESOURCE_GUARD: low RAM avail=${avail}MB < threshold=${RAM_THRESHOLD_MB}MB, pausing 30s"
    sleep 30

    local tcount active
    tcount=$(tab_ids | wc -l)
    if [ "$tcount" -gt 2 ]; then
        log "RESOURCE_GUARD: $tcount tabs open during low-RAM pause, trimming to active tab"
        active=$(active_tab_id)
        close_all_except "$active"
    fi

    avail=$(free -m | awk '/^Mem:/{print $7}')
    if [ "$avail" -lt "$RAM_THRESHOLD_MB" ]; then
        log "RESOURCE_GUARD_PAUSE: still low RAM avail=${avail}MB after tab cleanup, aborting cycle to avoid overload"
        return 1
    fi
    log "RESOURCE_GUARD: recovered, avail=${avail}MB, continuing"
    return 0
}

is_rate_limited() {
    local txt
    txt=$($B text 2>/dev/null)
    echo "$txt" | grep -q "$RATE_LIMIT_TEXT"
}

dismiss_rate_limit() {
    $B click "$DISMISS_SEL" >>"$LOG" 2>&1
    sleep 1
}

# ---------------------------------------------------------------------------
# helper: verify send succeeded by URL transition (.../project -> .../c/<id>)
# echoes the new url and returns 0 on success, returns 1 on failure (still on /project)
# ---------------------------------------------------------------------------
verify_send() {
    local tries=3
    local t u
    for ((t = 1; t <= tries; t++)); do
        sleep 2
        u=$($B url 2>/dev/null)
        if [[ "$u" == *"/c/"* ]]; then
            echo "$u"
            return 0
        fi
        log "verify_send: attempt $t/$tries, url still '$u'"
    done
    return 1
}

# ---------------------------------------------------------------------------
# harvest mode
# ---------------------------------------------------------------------------
run_harvest() {
    log "=== HARVEST MODE START ==="
    if [ ! -f "$SENT_URLS_FILE" ]; then
        log "no $SENT_URLS_FILE found, nothing to harvest"
        exit 1
    fi

    local harvested_done=0 harvested_pending=0 harvested_lost=0

    while IFS=$'\t' read -r worker_id url sent_at; do
        [ -z "${url:-}" ] && continue

        if ! resource_guard; then
            log "HARVEST: aborting remaining harvest due to resource guard"
            break
        fi

        # single-tab discipline: reuse the existing tab, just navigate it.
        # (never close-then-reopen — see ensure_single_tab_at comment: closing
        # the last tab bricks the daemon beyond CLI repair.)
        if ! ensure_single_tab_at "$url"; then
            log "HARVEST: aborting remaining harvest, daemon has 0 tabs"
            break
        fi
        enforce_tab_hardlimit "$CURRENT_TAB"

        timeout 8 "$B" wait --networkidle >>"$LOG" 2>&1
        sleep 1

        txt=$($B text 2>/dev/null)
        stopping=$($B snapshot -i 2>/dev/null | grep -ic "Stop answering")

        if echo "$txt" | grep -q "Worked for" && [ "${stopping:-0}" -eq 0 ]; then
            log "HARVEST worker $worker_id: DONE ($url)"
            # worker_id alone collides across separate send runs (each run
            # restarts numbering at 1) -- 5/6 results silently overwrote each
            # other on 2026-08-26 when several single-worker runs were
            # harvested back to back. Key by the conversation id from the URL
            # (globally unique) instead; fall back to a worker_id+timestamp
            # key only if the URL doesn't have the expected /c/<id> shape.
            conv_id=$(echo "$url" | grep -oP '/c/\K[a-zA-Z0-9-]+' | head -1)
            if [ -n "$conv_id" ]; then
                result_key="$conv_id"
            else
                result_key="${worker_id}_$(date +%s%N)"
            fi
            echo "$txt" > "$STATE_DIR/result_${result_key}.txt"
            harvested_done=$((harvested_done + 1))
        else
            log "HARVEST worker $worker_id: still pending/running ($url)"
            harvested_pending=$((harvested_pending + 1))
        fi

        sleep 1
    done < "$SENT_URLS_FILE"

    log "HARVEST summary: done=$harvested_done pending=$harvested_pending lost=$harvested_lost"
    log "HARVEST_CYCLE_COMPLETE"
}

# ---------------------------------------------------------------------------
# send mode (default)
# ---------------------------------------------------------------------------
run_send() {
    log "=== BURST CYCLE V2 START (NUM_WORKERS=$NUM_WORKERS SLEEP_BETWEEN_WORKERS=$SLEEP_BETWEEN_WORKERS RAM_THRESHOLD_MB=$RAM_THRESHOLD_MB TAB_RECYCLE_EVERY=$TAB_RECYCLE_EVERY) ==="

    avail0=$(free -m | awk '/^Mem:/{print $7}')
    log "baseline available RAM: ${avail0}MB, tabs open: $(tab_ids | wc -l)"

    # start clean: exactly one tab, on project url. Reuse an existing tab as
    # anchor if one exists (never close down to 0 — see ensure_single_tab_at).
    if ! ensure_single_tab_at "$PROJECT_URL"; then
        log "FATAL: daemon has 0 tabs open and cannot self-recover. Fix manually (re-run cookie-import / restart daemon) before retrying."
        exit 1
    fi
    log "anchored on tab: $CURRENT_TAB"
    sleep 1.5

    # Phase A: ONE-SHOT rate-limit check, no reload-loop.
    # Reason: repeated goto/reload polling was found to itself trigger/hold
    # the "Too many requests" lock (observed live: 10 iters stuck in a row
    # even though a manual check right before script start was clean). So
    # check current page text ONCE (no goto/reload), if blocked dismiss +
    # wait a single fixed $RATE_LIMIT_WAIT_S once, then hand off to Phase B
    # regardless — Phase B's own per-worker URL-change verification +
    # BLOCKED marking already handles a still-active limit robustly. Do not
    # loop here (that's what caused the self-triggered lock above).
    log "--- Phase A: one-shot rate-limit check ---"
    if is_rate_limited; then
        log "Phase A: RATE LIMITED, dismissing dialog and waiting ${RATE_LIMIT_WAIT_S}s once (stubborn wait, Gabriel 2026-08-26)"
        dismiss_rate_limit
        sleep "$RATE_LIMIT_WAIT_S"
    else
        log "Phase A: clean"
    fi
    log "Phase A complete"

    # Phase B: sequential sends, one tab at a time
    log "--- Phase B: sequential sends (NUM_WORKERS=$NUM_WORKERS) ---"
    sent_count=0
    blocked_count=0
    failed_count=0
    # mid-burst stubborn-wait guard: Phase A only catches a limit that's
    # already active BEFORE the first send. If the limit kicks in partway
    # through the 30-worker burst instead, every remaining worker used to
    # blow straight through as BLOCKED_NO_URL_CHANGE with no recovery
    # (Gabriel's "5-7min wait, then click windows away, then continue"
    # never happened). Fire the same stubborn wait ONCE, only after 2
    # consecutive blocks (avoids treating one flaky send as a real limit).
    consec_blocked=0
    rate_limit_wait_used=0

    > /dev/null  # noop, keep shellcheck quiet about empty body possibilities

    for i in $(seq 1 "$NUM_WORKERS"); do
        ts_start="$(date -Iseconds)"
        result_json="$STATE_DIR/worker_${i}.json"

        if ! resource_guard; then
            log "Worker $i: RESOURCE_GUARD_PAUSE, stopping remaining cycle early"
            printf '{"worker":%d,"status":"RESOURCE_GUARD_PAUSE","sent_at":"%s","trigger":"%s"}\n' \
                "$i" "$ts_start" "$TRIGGER" > "$result_json"
            break
        fi

        $B tab "$CURRENT_TAB" >>"$LOG" 2>&1
        $B goto "$PROJECT_URL" >>"$LOG" 2>&1
        sleep 1.5

        timeout 6 "$B" wait "$INPUT_SEL" >>"$LOG" 2>&1
        sleep 0.5

        if is_rate_limited; then
            log "Worker $i: rate-limit modal visible before typing on tab $CURRENT_TAB, dismissing and continuing (not auto-blocking)"
            dismiss_rate_limit
        fi

        $B click "$INPUT_SEL" >>"$LOG" 2>&1
        $B js 'var el=document.querySelector("#prompt-textarea"); if(el) el.innerText="";' >>"$LOG" 2>&1
        sleep 0.2
        $B type "$TRIGGER" >>"$LOG" 2>&1
        sleep 0.3

        actual=$($B js 'document.querySelector("#prompt-textarea") ? document.querySelector("#prompt-textarea").innerText : "__MISSING__"' 2>/dev/null)
        if [ "$actual" != "$TRIGGER" ]; then
            log "Worker $i: text mismatch on tab $CURRENT_TAB (got '$actual'), retrying once"
            $B click "$INPUT_SEL" >>"$LOG" 2>&1
            $B js 'var el=document.querySelector("#prompt-textarea"); if(el) el.innerText="";' >>"$LOG" 2>&1
            sleep 0.2
            $B type "$TRIGGER" >>"$LOG" 2>&1
            sleep 0.3
            actual=$($B js 'document.querySelector("#prompt-textarea") ? document.querySelector("#prompt-textarea").innerText : "__MISSING__"' 2>/dev/null)
            if [ "$actual" != "$TRIGGER" ]; then
                log "Worker $i: text STILL mismatched ('$actual'), marking FAILED_TYPE"
                printf '{"worker":%d,"tab_id":%s,"status":"FAILED_TYPE","sent_at":"%s","trigger":"%s"}\n' \
                    "$i" "$CURRENT_TAB" "$ts_start" "$TRIGGER" > "$result_json"
                failed_count=$((failed_count + 1))
                enforce_tab_hardlimit "$CURRENT_TAB"
                sleep "$SLEEP_BETWEEN_WORKERS"
                continue
            fi
        fi

        $B click "$SEND_SEL" >>"$LOG" 2>&1

        # verification: trust URL transition, not modal presence
        if conv_url=$(verify_send); then
            log "Worker $i: SENT on tab $CURRENT_TAB -> $conv_url"
            printf '{"worker":%d,"tab_id":%s,"url":"%s","status":"SENT","sent_at":"%s","trigger":"%s"}\n' \
                "$i" "$CURRENT_TAB" "$conv_url" "$ts_start" "$TRIGGER" > "$result_json"
            printf '%s\t%s\t%s\n' "$i" "$conv_url" "$ts_start" >> "$SENT_URLS_FILE"
            sent_count=$((sent_count + 1))
            consec_blocked=0
        else
            log "Worker $i: URL never left /project after send, marking BLOCKED"
            if is_rate_limited; then
                dismiss_rate_limit
            fi
            printf '{"worker":%d,"tab_id":%s,"status":"BLOCKED_NO_URL_CHANGE","sent_at":"%s","trigger":"%s"}\n' \
                "$i" "$CURRENT_TAB" "$ts_start" "$TRIGGER" > "$result_json"
            blocked_count=$((blocked_count + 1))
            consec_blocked=$((consec_blocked + 1))

            if [ "$consec_blocked" -ge 2 ] && [ "$rate_limit_wait_used" -eq 0 ]; then
                log "Worker $i: $consec_blocked consecutive BLOCKED -- real rate limit mid-burst, stubborn wait ${RATE_LIMIT_WAIT_S}s once (Gabriel 2026-08-26), then dismiss + continue"
                sleep "$RATE_LIMIT_WAIT_S"
                if is_rate_limited; then
                    dismiss_rate_limit
                fi
                rate_limit_wait_used=1
                consec_blocked=0
            fi
        fi

        enforce_tab_hardlimit "$CURRENT_TAB"

        # tab recycle: every TAB_RECYCLE_EVERY workers, close + reopen fresh tab (RAM reset)
        if [ $((i % TAB_RECYCLE_EVERY)) -eq 0 ] && [ "$i" -lt "$NUM_WORKERS" ]; then
            log "Worker $i: recycle point (every $TAB_RECYCLE_EVERY), closing tab $CURRENT_TAB and opening fresh tab"
            old_tab="$CURRENT_TAB"
            out=$($B newtab "$PROJECT_URL" 2>&1)
            new_tab=$(echo "$out" | grep -o 'Opened tab [0-9]*' | grep -o '[0-9]*')
            if [ -n "$new_tab" ]; then
                $B closetab "$old_tab" >>"$LOG" 2>&1
                CURRENT_TAB="$new_tab"
                log "recycled: closed $old_tab, now on fresh tab $CURRENT_TAB"
            else
                log "recycle: failed to open fresh tab, keeping $old_tab"
            fi
            avail_now=$(free -m | awk '/^Mem:/{print $7}')
            log "post-recycle available RAM: ${avail_now}MB"
        fi

        sleep "$SLEEP_BETWEEN_WORKERS"
    done

    log "Phase B complete: sent=$sent_count blocked=$blocked_count failed=$failed_count attempted=$NUM_WORKERS"

    avail_end=$(free -m | awk '/^Mem:/{print $7}')
    log "final available RAM: ${avail_end}MB, tabs open: $(tab_ids | wc -l)"

    SUMMARY_FILE="$STATE_DIR/SUMMARY_v2_${RUN_TS}.json"
    cat > "$SUMMARY_FILE" <<EOF
{
  "run_ts": "$RUN_TS",
  "attempted": $NUM_WORKERS,
  "sent": $sent_count,
  "blocked": $blocked_count,
  "failed": $failed_count,
  "sent_urls_file": "$SENT_URLS_FILE",
  "log_file": "$LOG"
}
EOF
    log "Summary written to $SUMMARY_FILE"
    log "BURST_CYCLE_COMPLETE (send phase only; run --harvest separately to collect results)"
}

# ---------------------------------------------------------------------------
# entrypoint
# ---------------------------------------------------------------------------
if [ "${1:-}" = "--harvest" ]; then
    run_harvest
else
    run_send
fi
