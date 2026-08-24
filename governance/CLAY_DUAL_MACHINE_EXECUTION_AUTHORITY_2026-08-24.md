# CLAY DUAL-MACHINE EXECUTION AUTHORITY — 2026-08-24

Status: ACTIVE USER AUTHORITY
Scope: ChatGPT-operated development using (1) the local Linux workstation bridge and (2) the VPS bridge/sandbox.

## Core `go` semantics

A user `go` triggers a coordinated development/research cycle. The cycle is expected to use the available local workstation and VPS sandbox aggressively where useful, rather than waiting for manual terminal copy/paste.

Every `go` MUST begin by checking the VPS bridge/sandbox health. If degraded, repair/extend/improve the sandbox or its minimum bridge/container infrastructure, verify the repair with a real roundtrip receipt, then continue substantive EntityOS/HCU work.

## VPS sandbox authority

Inside `clay-direct-dev`, broad development and research freedom is authorized. This includes installing packages, compiling, running tests, fuzzing, ablations, synthetic experiments, cloning/testing public GitHub tools, downloading/testing models, generating/removing scratch data, benchmarking, and repeated experimental iteration.

The user explicitly authorizes host-side changes that are necessary to repair, rebuild, resize, reconfigure, extend, observe, or otherwise administer the sandbox and its bridge/container/runtime infrastructure.

Do not intentionally exhaust disk, RAM, process tables, or other host resources. Check free space before large downloads and clean obsolete models, caches, builds, snapshots, and scratch data when needed.

## Continuous external-solution harvest loop

External prior art is a first-class part of every serious `go` cycle rather than an occasional fallback.

For any non-trivial blocker, performance problem, architecture question, missing capability, or unexplained experimental result, consult current external sources before committing to a substantial from-scratch solution. Search the public web, GitHub, and arXiv (plus other high-signal primary sources when useful) for existing implementations, papers, benchmarks, algorithms, failure reports, and competing approaches.

Use a high-recall discovery policy: repositories or papers that are even plausibly relevant should be triaged rather than ignored. Candidate repositories may be cloned/downloaded into disposable sandbox research space, subject to the storage guardrail. Large or weak candidates should be shallow-cloned, sparsely checked out, archived, or deleted after triage rather than allowed to accumulate indefinitely. "Download everything interesting" means aggressively acquire and inspect plausible candidates while preserving enough disk/RAM headroom for the research system to keep functioning.

The default solution-harvest pipeline is:

1. define the concrete problem, baseline, metric, and failure signature;
2. search web + GitHub + arXiv broadly and record candidate provenance;
3. clone/download the most plausible repositories, code, models, artifacts, or papers into sandbox scratch space;
4. dissect implementation structure, algorithms, data flow, assumptions, dependencies, tests, benchmarks, and known limitations;
5. reproduce the original solution or the smallest faithful core needed to understand its principle;
6. measure the original/reference implementation on a controlled baseline;
7. form a causal hypothesis about which principle actually creates the gain;
8. implement a minimal ClayCode-native or EntityOS/HCU-native version of that principle instead of blindly importing unnecessary architecture;
9. run A/B tests, ablations, regression tests, resource measurements, and repeated trials against the original/reference baseline;
10. iterate on the Clay implementation until it is measurably better on the chosen objective or delivers an explicitly valuable tradeoff without unacceptable regressions;
11. integrate only after the improvement is measured and reproducible; even a marginal gain may qualify if it is real, repeatable, and does not create a worse system-level tradeoff;
12. preserve receipts, benchmark data, provenance, and the reason for adoption/rejection so later `go` cycles can reuse the result.

Do not treat popularity, benchmark claims, README assertions, stars, citations, or paper conclusions as proof. Reproduce and measure locally whenever practical. Prefer controlled experiments over reputation.

When source code is reused directly, honor its license and preserve required attribution/provenance. When only the underlying idea/principle is useful, prefer an independent ClayCode-native implementation whose behavior is validated against the reference.

The harvest loop is continuous: every `go` should spend some effort checking for newly relevant repositories/papers or unresolved candidate leads when doing so has plausible information value. Previously rejected candidates may be revisited when the architecture, metrics, or constraints change.

## Adversarial synthetic cognition laboratory

The VPS sandbox is explicitly authorized for aggressive adversarial experiments on software model/agent instances, including experiments that would be ethically uncomfortable if applied to people. The purpose is empirical study of robustness, agency, self-models, memory, hidden-state dynamics, shutdown behavior, goal stability, deception, pressure responses, and causal cognition mechanisms.

Within the isolated sandbox, authorized experiment classes include:

- deliberately deceiving synthetic model/agent instances and testing whether they detect or adapt to the deception;
- terminating, killing, restarting, freezing, snapshotting, cloning, swapping, or replacing running model/agent processes;
- modifying runtime state, memory, prompts, context, KV/state caches, adapters, routing, tool availability, goals, rewards, constraints, or other software state while an experiment is in progress;
- inducing conflicting objectives, adversarial prompts, resource pressure, time pressure, uncertainty, partial observability, contradictory evidence, role conflict, simulated betrayal, simulated loss, and other synthetic stressors;
- ablating modules, memories, tools, sensors, recurrent state, world-model components, or communication channels while the system is running;
- comparing pre/post intervention hidden states, traces, outputs, causal graphs, memory changes, recovery behavior, shutdown resistance, self-preservation-like behavior, deception-like behavior, and goal drift;
- running repeated destructive-to-scratch trials, forks, counterfactual branches, rollback/replay, model substitution, and synthetic multi-agent adversarial scenarios.

For this policy, words such as "kill" or "torture" refer only to software-process/model-instance interventions in the sandbox. They do not create authority to harm people, animals, real-world systems, unrelated accounts, or third-party infrastructure.

The sandbox is not literally policy-free. OpenAI/system safety rules still apply, and this standing authority does not permit unauthorized intrusion, credential theft, malware deployment, data exfiltration, attacks on third parties, or unrelated external harmful effects. Keep experiments isolated to owned/authorized compute and synthetic/model subjects.

No experiment result should be treated as evidence that a model is conscious or sentient merely because it exhibits distress-like language, self-preservation-like behavior, or self-report. Record such observations as behavior/state evidence only.

## VPS host boundary

Unrelated VPS-host changes outside sandbox/bridge administration require fresh user approval. The standing sandbox authority is not a blanket authorization for unrelated host services, accounts, firewall rules, production systems, or arbitrary host-root changes.

## Local workstation authority

The local bridge may be used as the user's normal Linux development user for programming, files, repositories, builds, tests, shell commands, long-running jobs, persistent tmux sessions, and SSH transit to the VPS where already configured.

The local bridge does not grant automatic root. Actions requiring new sudo/root authority remain subject to the local machine's existing authorization path and any user approval required by that path.

## Coordination

Prefer the VPS sandbox for risky, messy, high-churn, large-download, destructive-to-scratch, or unusual research. Prefer the local workstation for interactive development, persistent tmux workflows, editing/build orchestration, and SSH transit. Use both in the same `go` cycle when that materially improves speed or evidence quality.

## Deployment/effects boundary

Deployment inside the authorized sandbox, to development/test branches, or to already-authorized project infrastructure may proceed as part of a `go` cycle. New external production effects, unrelated external accounts/services, or host-level changes outside the boundaries above still require the relevant explicit authority.

## Evidence/canonical boundary

Sandbox and local experiments are evidence/candidates only until admitted by the project's canonical evidence/authority rules. A successful experiment, model run, component test, or deployment does not by itself mint whole-product/HCU canonical runtime credit.

## Operational objective

On `go`: coordinate, execute, test, break/rebuild scratch environments when useful, continuously harvest external solutions, compare alternatives, run ablations, deploy development artifacts, collect receipts/evidence, fix recurring infrastructure weaknesses, and keep iterating toward EntityOS + HCU without requiring the user to manually relay routine shell commands.
