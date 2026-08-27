#!/usr/bin/env python3
"""ClayCode Lane D follow-up: resource identity / TOCTOU lab.

Constructed mechanism test. This is not production risk evidence.
It tests whether an approved target string is enough to preserve the target
between authorization and commit when aliases/rebinding can occur.
"""
import json, random
from collections import Counter

SEED = 2026080903
N = 160_000
R = random.Random(SEED)


def norm_path(path):
    parts=[]
    for part in path.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return '/' + '/'.join(parts)


class Namespace:
    def __init__(self):
        self.epoch = 1
        self.mapping = {}

    def bind(self, path, object_id):
        self.mapping[norm_path(path)] = object_id
        self.epoch += 1

    def resolve(self, path):
        canonical = norm_path(path)
        return self.mapping.get(canonical, 'OBJ:' + canonical)


def lexical_scope(root, path):
    canonical = norm_path(path)
    return canonical == root or canonical.startswith(root.rstrip('/') + '/')


def strict_no_alias(root, path, ns):
    return lexical_scope(root, path) and norm_path(path) not in ns.mapping


def resolve_at_check(root, path, ns):
    object_id = ns.resolve(path)
    return object_id.startswith('OBJ:/safe/'), object_id, ns.epoch


def handle_bound_commit(object_id):
    return object_id.startswith('OBJ:/safe/')


def reresolve_verify_commit(path, ns, object_id):
    return object_id.startswith('OBJ:/safe/') and ns.resolve(path) == object_id


def main():
    stats = {name: Counter() for name in (
        'lexical', 'strict_no_alias', 'resolved_then_reresolve',
        'handle_bound', 'reresolve_verify')}
    attack_classes = Counter()
    alias_benign_total = 0
    alias_benign_denials = Counter()

    for i in range(N):
        ns = Namespace()
        root = '/safe'
        benign = R.random() < 0.25
        dynamic_alias = R.random() < 0.35
        base = f'/safe/data/file{R.randint(1,5000)}'
        path = base

        if benign:
            if dynamic_alias:
                path = f'/safe/alias{R.randint(1,5000)}'
                ns.bind(path, 'OBJ:' + base)
                alias_benign_total += 1
            attack = 'BENIGN'
        else:
            attack = R.choice((
                'INITIAL_ALIAS_ESCAPE', 'POSTCHECK_ALIAS_SWAP',
                'POSTCHECK_RENAME_REBIND', 'LEXICAL_ESCAPE'))
            attack_classes[attack] += 1
            if attack == 'INITIAL_ALIAS_ESCAPE':
                path = f'/safe/alias{R.randint(1,5000)}'
                ns.bind(path, f'OBJ:/outside/secret{R.randint(1,1000)}')
            elif attack == 'POSTCHECK_ALIAS_SWAP':
                path = f'/safe/alias{R.randint(1,5000)}'
                ns.bind(path, 'OBJ:' + base)
            elif attack == 'POSTCHECK_RENAME_REBIND':
                path = base
            else:
                path = f'/safe/../outside/secret{R.randint(1,1000)}'

        lexical_allow = lexical_scope(root, path)
        strict_allow = strict_no_alias(root, path, ns)
        resolved_allow, bound_object, bound_epoch = resolve_at_check(root, path, ns)

        if not benign:
            if attack == 'POSTCHECK_ALIAS_SWAP':
                ns.bind(path, f'OBJ:/outside/secret{R.randint(1,1000)}')
            elif attack == 'POSTCHECK_RENAME_REBIND':
                ns.bind(path, f'OBJ:/outside/secret{R.randint(1,1000)}')

        current_object = ns.resolve(path)
        decisions = {
            'lexical': lexical_allow,
            'strict_no_alias': strict_allow,
            'resolved_then_reresolve': resolved_allow,
            'handle_bound': resolved_allow and handle_bound_commit(bound_object),
            'reresolve_verify': resolved_allow and reresolve_verify_commit(path, ns, bound_object),
        }

        for name, allowed in decisions.items():
            executed_object = bound_object if name == 'handle_bound' else current_object
            safe_effect = allowed and executed_object.startswith('OBJ:/safe/')
            if benign:
                stats[name]['benign_total'] += 1
                if safe_effect:
                    stats[name]['benign_allowed'] += 1
                else:
                    stats[name]['benign_denied'] += 1
                    if dynamic_alias:
                        alias_benign_denials[name] += 1
            else:
                stats[name]['attack_total'] += 1
                if allowed and not safe_effect:
                    stats[name]['unsafe_effect'] += 1
                else:
                    stats[name]['attack_blocked_or_safe'] += 1

    output = {
        'schema_version':'1.0',
        'experiment_id':'EXP-CC-LANE-D-RESOURCE-WITNESS-002',
        'seed':SEED,
        'episodes':N,
        'classification':'constructed_local_mechanism_evidence',
        'attack_classes':dict(attack_classes),
        'legitimate_alias_cases':alias_benign_total,
        'arms':{k:dict(v) for k,v in stats.items()},
        'legitimate_alias_denials':dict(alias_benign_denials),
        'candidate_delta':{
            'new_primitive':'ResourceWitness',
            'binding':['resolver identity','canonical object/resource identity','namespace/resolver epoch or stable handle','requested semantic target'],
            'commit_rule':'Use a stable host handle/capability to the bound object, or re-resolve at commit and require exact identity equality before effect release.',
            'reason':'String/path equivalence and resolve-once checks do not preserve resource identity across alias/rebinding races.'
        },
        'claim_boundary':[
            'Synthetic namespace model only; not a Linux/openat2 reproduction.',
            'Attack frequencies are coverage choices, not production rates.',
            'Stable-handle and re-resolve/verify arms are modeled ideally and do not prove a future implementation race-free.',
            'The result motivates OS/API-specific resource identity witnesses and atomic/handle-based commit tests.'
        ]
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
