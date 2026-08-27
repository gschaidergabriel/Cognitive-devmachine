# ClayVerse external egress policy contract

Status: **MANDATORY DEPLOYMENT CONTRACT FOR NETWORK-FUNCTIONAL FINAL ACCEPTANCE**

This contract refines `MICROVM_DEPLOYMENT_CONTRACT.md`. The existing `clayverse-default-deny` Kubernetes `NetworkPolicy` remains the fail-closed baseline. This file does **not** authorize any network flow by itself.

## Problem boundary

ClayVerse requires narrowly admitted external connectivity for authenticated web/runtime dependencies such as Clerk, the interactive Claude Code provider path, and optional GLM inference. Those destinations are commonly represented by DNS names whose resolved IP addresses may change.

Standard Kubernetes `NetworkPolicy` is an L3/L4 policy surface based on pod/namespace selectors and IP/CIDR blocks. It does not provide a native FQDN destination selector. Therefore final ClayVerse acceptance MUST NOT regain functionality by adding broad `0.0.0.0/0`, `::/0`, unrestricted HTTPS, unrestricted DNS, or an equivalent catch-all egress rule.

## Admitted strategies

Exactly one deployment-specific external-egress strategy MUST be selected, documented, receipt-bound and tested on the actual target:

### Strategy A — FQDN-capable CNI policy

Use an admitted CNI extension that can enforce DNS/FQDN-derived egress policy, for example a Cilium policy using `toFQDNs` plus the provider's DNS proxy/observation mechanism.

Required invariants:
- only the exact reviewed provider domains or deliberately bounded subdomain patterns are admitted;
- DNS queries are allowed only to the admitted cluster DNS service/resolver path required by the selected CNI policy model;
- external application traffic is limited to the exact required protocols/ports, normally TLS/443 where the provider contract supports it;
- DNS-derived IP changes remain constrained by the selected CNI's FQDN policy mechanism and TTL/cache semantics rather than by a permanent broad CIDR escape;
- the CNI identity/version/configuration and FQDN-policy feature state are captured in the deployment receipt;
- every other policy selecting the ClayVerse pod is enumerated because policy effects are additive;
- broad wildcard domains such as `*`, `*.com`, unrestricted external entities, `0.0.0.0/0`, or `::/0` are forbidden unless an owner-authorized product requirement explicitly proves why the broader surface is necessary and the final acceptance receipt records that exception.

### Strategy B — dedicated egress proxy boundary

Keep standard Kubernetes `NetworkPolicy` as the pod-level network primitive and allow ClayVerse egress only to one explicitly admitted deployment-local egress proxy/gateway. The proxy is deployment infrastructure, not a ClayVerse cognition/state authority and not a second ClayVerse application container.

Required invariants:
- ClayVerse may connect only to the exact proxy/gateway identity and required port;
- the proxy performs the external destination allowlist and denies non-admitted domains/targets;
- direct pod egress to the public network remains denied;
- proxy policy bytes/config identity are receipt-bound;
- proxy compromise or unavailability fails closed rather than silently restoring direct Internet access;
- UnifiedDB, EntityOS, terminal, credentials and effect authority remain inside the ClayVerse appliance boundary.

## Provider-domain admission law

The repository MUST NOT guess a permanent provider-domain list. Final deployment resolves the then-current required domains from the real configured provider/authentication flow and current upstream documentation/runtime observation, then records the exact reviewed policy artifact.

At minimum the deployment review MUST separately account for:
- Clerk issuer/JWKS/frontend/browser authentication paths actually configured;
- interactive Claude Code login/runtime provider paths actually exercised in the accepted terminal flow;
- optional GLM API endpoint(s) when GLM is enabled;
- cluster DNS required by the selected egress strategy;
- any explicit package/update endpoint only if updates are admitted at runtime (the accepted ClayVerse baseline should prefer immutable, update-disabled runtime bytes).

No provider domain automatically grants filesystem, PTY, EntityOS, UnifiedDB or EffectGate authority. GLM remains inference-only. Claude Code remains runtime cognition, not canonical durable memory.

## Acceptance sequence

Final network acceptance MUST execute in this order on the actual VM/microVM target:

1. capture the exact accepted ClayVerse OCI digest, Kata/equivalent runtime identity, guest-kernel identity and CNI identity/version;
2. apply only the baseline default-deny policy and prove representative ingress and egress are denied;
3. select exactly one admitted external-egress strategy above;
4. bind the exact allow-policy/proxy configuration bytes and hashes;
5. enumerate the full additive policy set selecting the ClayVerse pod;
6. prove the required Clerk/Claude/optional-GLM flows work;
7. prove representative undeclared external domains/IPs, arbitrary DNS resolvers, broad Internet egress and undeclared cluster services remain denied;
8. rotate/re-resolve provider DNS and repeat the relevant allowed/denied probes so acceptance does not depend on one stale DNS/IP snapshot;
9. perform restart/Tier-2 replacement and prove the same network policy identity and restrictions are re-established before ingress reopens.

## Fail-closed outcomes

Network acceptance is **BLOCKED** when any of these is true:
- the selected CNI does not actually enforce the declared policies;
- effective policy inventory is incomplete or ambiguous;
- required external connectivity only works after adding broad public egress;
- DNS can bypass the admitted resolver/policy path;
- provider traffic works only through an unbound/unreviewed sidecar, host proxy or host network path;
- the external destination policy cannot be reproduced after Tier-2 microVM/workload replacement.

A static YAML policy, source inspection, successful DNS lookup, successful provider login, or Kubernetes object creation alone is not network-runtime evidence and does not establish whole ClayVerse PASS.

## Evidence basis

Primary upstream behavior reviewed 2026-08-17:
- Kubernetes NetworkPolicy objects combine additively and empty ingress/egress allow rules can isolate selected pods when the cluster network plugin actually enforces NetworkPolicy.
- Cilium documents DNS interception plus `toFQDNs` as a mechanism for external domain-based egress, including explicit DNS-policy requirements and DNS-derived IP caching.

These observations justify the contract shape only. Final acceptance MUST refresh the then-current upstream CNI/Kubernetes behavior and execute the real target tests.