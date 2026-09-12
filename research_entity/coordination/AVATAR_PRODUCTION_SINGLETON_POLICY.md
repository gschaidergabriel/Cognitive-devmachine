# HARD POLICY — FranKenstein Avatar Production Singleton

Status: **PERMANENT OWNER OPERATING RULE**
Owner instruction: Gabriel, 2026-09-12
Target host: `ai-core-node`
Target surface: the existing production Avatar served from `http://127.0.0.1:8788/` and shown on physical **screen 2 / HDMI-A-0**.

## Absolute invariant

There must be **at most one production Chrome/Kiosk Avatar instance**.

The production instance is the one bound to the existing FranKenstein Avatar runtime (`frankenstein-buehne.service`, `/home/ai-core-node/.claude/star/visual/`, `127.0.0.1:8788`) and displayed on screen 2.

Normal steady state:

- exactly one production Avatar window is open;
- it stays visible on screen 2;
- source/UI changes are applied to the existing runtime and the **existing page is reloaded/refreshed**;
- workers do **not** spawn a fresh Chrome/Kiosk merely to observe, test, refresh, or activate a change.

If the production Avatar is not open:

- first prove that no valid production window exists;
- then start **exactly one** production Chrome/Kiosk instance;
- place/bind it to screen 2;
- after that, return to refresh/reuse semantics only.

## Forbidden behavior

Workers MUST NOT:

1. open a second production Chrome/Kiosk while one already exists;
2. create a replacement window for every source change;
3. use a new browser instance as a substitute for refreshing the existing one;
4. move a scratch/shadow browser onto screen 2 and call it production;
5. leave duplicate production-looking windows/processes behind;
6. hard-code an old X11 window ID or PID as identity — those are ephemeral evidence only.

Scratch/shadow browsers are allowed only when a discriminator genuinely requires them. They must use isolated state/profile, be explicitly marked SCRATCH/SHADOW, must not replace the screen-2 production subject, and must be closed after the test.

## Required worker algorithm

Before any Avatar browser action:

1. Resolve the real host as `machine_id=ai-core-node`, `owner=gabriel`.
2. Check `frankenstein-buehne.service`, `127.0.0.1:8788`, and current visible windows/processes.
3. Identify the existing production subject by current runtime evidence (URL/title/class/service/live path + screen-2 geometry), not stale PID/window IDs.
4. If one valid production instance exists: **reuse it and refresh/reload that page**.
5. If none exists: start exactly one instance on screen 2, verify it, then reuse it thereafter.
6. If more than one production-looking instance exists: do not spawn another. Classify duplicates, preserve the intended production subject, and remove only proven duplicate/scratch subjects under an admitted effect boundary.
7. Read back the final state: one production window, on screen 2, healthy, correct URL/runtime.

## Worker broadcast rule

Every worker/agent touching Avatar, GUI, Chrome, browser, display, compositor, kiosk, visual validation, or live promotion must treat this file as a **hard precondition**. It is not an optimization and not a temporary preference.

The canonical Avatar handoff/status should point here. Any downstream prompt/handoff that could cause browser launch must include the short rule:

> ONE PRODUCTION AVATAR. KEEP IT ON SCREEN 2. REFRESH/RELOAD THE EXISTING INSTANCE. ONLY LAUNCH ONE IF NONE EXISTS. NEVER SPAWN A SECOND PRODUCTION CHROME.

## Relationship to existing Avatar law

This file strengthens and makes permanent the existing operating law already documented in `AVATAR_HANDOFF_STATUS.md` and the 2026-09-12 absolute bootstrap: the visible display-2 Avatar is a persistent production subject, not a disposable browser preview.

If any older instruction suggests opening a new production browser to verify a change, **this policy wins** unless Gabriel explicitly changes the rule later.
