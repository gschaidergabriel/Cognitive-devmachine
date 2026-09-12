# STOP — READ THIS BEFORE ANY AVATAR WORK

Owner law (Gabriel, 2026-09-12): the production FranKenstein Avatar is a **singleton**.

- Work on the existing **chat-bearing** FranKenstein GUI, not the empty/disconnected parallel GUI.
- Keep exactly **one** production Chrome/window.
- Keep that singleton visible on physical **screen 2 / HDMI-A-0**.
- After normal source changes, **refresh/reload the existing window**. Do not open another production Chrome to see the change.
- If the production window is absent, open exactly one through the existing `buehne_daemon.py` lifecycle, place it on screen 2, then reuse it thereafter.
- Scratch/shadow browsers are not production and must never replace the screen-2 subject.
- Canonical details: `AVATAR_SINGLETON_POLICY.md`.
- Canonical helper: `avatar_singleton_refresh.sh`.

Any worker that ignores this and spawns another production Avatar GUI is violating current owner authority.
