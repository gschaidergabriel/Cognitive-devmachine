# ABSOLUTE AVATAR SINGLETON / SCREEN-2 POLICY

Owner authority: Gabriel, 2026-09-12.
Scope: `ai-core-node` production FranKenstein Avatar / `buehne.html` / kiosk Chrome.
Status: HARD OPERATING LAW for every current and future worker/agent/session touching the Avatar.

## One production instance only

There must be exactly ONE production Avatar browser instance/window in normal operation.

The production subject is the existing FranKenstein kiosk/page served from:

- host: `ai-core-node`
- service/app: `frankenstein-buehne.service` + `/home/ai-core-node/.claude/star/visual/`
- URL: `http://127.0.0.1:8788/`
- visible title: `FranKenstein -- live`
- target display: physical screen 2 / `HDMI-A-0` (`1024x600+1680+0` at the 2026-09-12 measured topology)

## Mandatory worker behavior

1. Before any Avatar/browser action, discover whether the production window is already open.
2. If it is open: REUSE IT. Do not launch another Chrome/kiosk/window. Apply source changes, then reload/refresh that existing production page only.
3. If it is not open: start exactly ONE production instance on screen 2, then treat that instance as the singleton and reuse it thereafter.
4. Keep the production Avatar visible on screen 2. Do not replace it with a scratch browser, move a validator over it, or hide it as a normal workflow side effect.
5. Never use “open a new Chrome to see the change” as a refresh mechanism.
6. Scratch/shadow browsers are allowed only for isolated tests, must be explicitly marked SCRATCH/SHADOW, must not occupy/replace the screen-2 production subject, and must be closed after the test.
7. A worker finding more than one production-like Avatar Chrome/window must treat that as a runtime-policy violation: preserve the intended existing screen-2 production subject, close only confirmed duplicates, then record/read back the resulting singleton state.
8. Window IDs and PIDs are ephemeral. Bind the production subject by service + URL + title/class + display geometry, not by hard-coded IDs.

## Update law

Normal Avatar update:

`identify existing production subject -> verify exact live source/service -> mutate admitted source -> reload existing page -> verify same screen-2 subject remains visible/healthy -> record readback`

Only when the singleton is absent:

`verify absent -> launch one production kiosk on screen 2 -> verify exactly one production subject -> reuse/refresh thereafter`

## Forbidden

- spawning a new production Chrome on every edit;
- creating a second/third production GUI;
- calling a newly-opened browser “the same instance”;
- replacing the chat-bearing production GUI with the empty/disconnected parallel GUI;
- using a scratch browser as production evidence;
- hard-coding a historical X11 window ID or PID as identity.

## Correct GUI target

There are currently two known GUI surfaces. The GUI that visibly contains the live chat transcript/messages and connected state is the production GUI to continue developing. The empty/disconnected parallel GUI is NOT the target for replacement or further parallel construction.

This policy is intentionally durable and must be read before Avatar work. It does not authorize unrelated host mutation; it defines the required singleton/runtime behavior whenever Avatar/browser work is otherwise authorized.
