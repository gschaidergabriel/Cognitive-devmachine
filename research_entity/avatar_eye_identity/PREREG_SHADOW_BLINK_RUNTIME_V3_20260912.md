# Eye shadow blink runtime v3 — preregistration

The v2 Real-Host failure is classified as HARNESS/CDP transport overload: during the 2.8 s blink observation loop the validator performed synchronous CDP `Runtime.evaluate` state reads every ~12 ms; one read blocked until the 8 s transport timeout. The semantic shadow was built exactly and no product negative was established.

V3 changes only instrumentation. State and rAF intervals are sampled inside the browser on every animation frame. CDP is used only to arm the collector, trigger blink, coarsely detect the closed phase for one screenshot, wait for completion, and retrieve the final sample array. No thresholds are weakened.

Hard subject hashes, semantic shadow, blink routes, special-expression continuity, eye/glow checks, >=9 distinct blink frames, restoration checks, FPS >=58, p95 <=18 ms, and live-source invariance remain required.

Scope: isolated scratch/headless browser only. No live source write and no production activation credit.
