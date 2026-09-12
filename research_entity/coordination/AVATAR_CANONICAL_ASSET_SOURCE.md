# ABSOLUTE AVATAR ASSET SOURCE POLICY

Owner authority: Gabriel, 2026-09-12.
Scope: every current and future worker/agent/session doing FranKenstein Avatar, face, head, body, rig, expression, animation, compositor or visual-asset work on `ai-core-node`.
Status: HARD OPERATING LAW.

## Canonical ready-made rig / object source

The owner-designated canonical local source bundle is:

`/home/ai-core-node/Downloads/FRANK_AVATAR_RIG_V2_2026-09-11`

Owner statement: this directory contains the finished objects/assets and the material needed for the Avatar rig. Workers must treat it as the FIRST asset source to inspect before generating replacements, rebuilding equivalent objects, searching unrelated folders, or declaring an asset missing.

## Mandatory behavior

1. Before creating or regenerating any Avatar object/asset, recursively inspect this directory for an existing ready-made equivalent.
2. Do not claim that an object, rig element, expression asset, mask, layer, pose, body/head element or related visual resource is missing until this bundle has been checked.
3. Prefer reuse/adaptation of the finished bundle over duplicate asset generation.
4. Preserve exact provenance when copying/adapting anything from the bundle: source path, filename, hash where material, and target path.
5. Treat the bundle as a master/donor source by default. Do not destructively edit/delete the original files unless the owner explicitly authorizes that exact mutation.
6. If a worker cannot access the directory, it must report `ASSET_SOURCE_UNAVAILABLE` for that worker/runtime; it must not silently invent a replacement and call the source absent.
7. If a later verified manifest/hash proves a newer owner-designated bundle supersedes this path, update this policy explicitly. Chat memory or an older handoff does not supersede current owner authority.

## Relationship to production

This bundle is the canonical READY-MADE ASSET / RIG SOURCE, not the running production web root.

The running production Avatar remains:

`/home/ai-core-node/.claude/star/visual/`

served by `frankenstein-buehne.service` at `http://127.0.0.1:8788/`, using the single production Chrome/window on screen 2.

Therefore the normal flow is:

`inspect canonical rig bundle -> select exact existing asset -> test/adapt in an isolated/reversible way -> admitted copy/integration into the live visual source -> refresh the existing singleton production page -> verify readback`

Never replace the production GUI with a file-browser preview of this bundle, and never spawn another production Chrome to inspect an asset.

## Anti-duplication law

For Avatar work, "make a new asset" is no longer the default action. The default action is:

`CHECK FRANK_AVATAR_RIG_V2_2026-09-11 FIRST.`

Only build a new asset when the exact required thing is genuinely absent or the existing donor demonstrably fails the current technical gate.

This policy must be read together with `AVATAR_SINGLETON_POLICY.md` and `AVATAR_HANDOFF_STATUS.md`.
