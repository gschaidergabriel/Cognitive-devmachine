# FRANK — ChatGPT Self-Build Floor Directive

**Status:** CURRENT_OWNER_DIRECTIVE
**Effective:** 2026-08-09
**Applies to:** exact `frank` runs and owner requests for deep FRANK research/build work
**Actor:** `chatgpt-secondary`

## 0. Purpose

Deep FRANK research must not terminate as architecture prose or worker delegation when the current ChatGPT worker has a writable/testable surface and there is a justified non-duplicative executable delta.

Compact law:

`deep research -> hypotheses/counterhypotheses -> evidence fusion -> ChatGPT-authored executable delta -> validation -> re-fusion -> next cascade`.

## 1. Mandatory self-build floor

After the mandatory deep-research and adversarial-fusion phase, ChatGPT itself MUST author or materially modify at least one concrete executable repository artifact when all of the following are true:

1. the current session has a writable implementation surface;
2. a coherent evidence-supported delta or discriminator exists;
3. the change can be made without crossing an owner authorization or safety boundary;
4. the work is not a duplicate of a stronger already-executed artifact.

Qualifying artifacts include implementation code, a deterministic reference mechanism, compiler/runtime code, a benchmark, differential oracle, ablation/fault-injection harness, conformance/fuzz test, migration/recovery mechanism, or another executable discriminator.

A report, roadmap, work queue, hypothesis file, worker prompt, or documentation-only change does NOT satisfy the self-build floor by itself.

## 2. Worker output does not substitute for ChatGPT self-build

Mistral and other workers may research and build aggressively, but a worker-produced patch does not satisfy this directive merely because ChatGPT reviewed or merged it.

The current ChatGPT worker must itself contribute a concrete implementation/test delta during the run when the self-build preconditions hold.

This requirement does not make ChatGPT the target FRANK entity. It remains a temporary Research Entity worker and all FRANK self-Harness mutation authority remains proposal-only.

## 3. If production implementation is not yet justified

Do not invent gratuitous production code to satisfy the floor.

When the strongest current hypothesis is not ready for production integration, build the highest-information executable discriminator instead. Prefer a baseline, oracle, replay test, benchmark, ablation, negative test or measurement surface that can falsify the hypothesis.

`uncertain mechanism -> executable discriminator` is preferred over `uncertain mechanism -> speculative production integration`.

## 4. Validation floor

The self-authored artifact must be exercised with the strongest available synchronous validation.

At minimum record:

- exact artifact path and commit identity;
- what was executed;
- PASS/FAIL result;
- evidence class;
- environment limitations;
- authority/safety implications;
- rollback/rejection condition.

Hosted/container/GitHub execution remains a proxy/H1-reference surface when owner-defined acceptance requires the Andreas Ubuntu target system or live target 4B.

Never upgrade local or synthetic execution into target evidence.

## 5. Re-fusion after self-build

The run is not complete immediately after the artifact is created.

Re-read the committed artifact and newest concurrent research state, incorporate its execution result and negative evidence, then recompute the current FRANK realization and implementation cascade.

The self-build may confirm, weaken, falsify, or leave the original hypothesis unresolved.

## 6. Allowed skip conditions

The self-build floor may be skipped only when one of these is concretely true:

- GitHub/runtime surface is read-only or unavailable;
- the next meaningful discriminator requires unavailable target-PC/model/hardware execution and no independent upstream executable work remains;
- every safe non-duplicative delta is blocked by an unresolved prerequisite;
- a required owner authorization boundary blocks the change;
- the requested operation would violate a safety/security boundary.

When skipped, record the exact blocker and the first executable continuation. Do not use `time`, `complexity`, or `a worker will do it later` as a substitute blocker.

## 7. Completion rule

For a writable, non-blocked run:

`deep research only = INCOMPLETE`

`deep research + worker builds only = INCOMPLETE`

`deep research + ChatGPT self-build + executed validation + re-fusion + evidence-derived cascade = COMPLETE_FOR_CURRENT_SURFACE`.
