#!/usr/bin/env python3
import math
from grid10_face_drive import derive_grid_face_drive


def close(a,b,eps=1e-9):
    assert abs(a-b) <= eps, (a,b)

# Concentrated state must be less entropic / more dominant than distributed state.
concentrated={f'G{i}':(10.0 if i==4 else 0.0) for i in range(1,11)}
distributed={f'G{i}':1.0 for i in range(1,11)}
a=derive_grid_face_drive(concentrated,3.0,winner='G4')
b=derive_grid_face_drive(distributed,3.0,winner='G4')
assert a.dominance>b.dominance
assert a.entropy<b.entropy
assert a.participation<b.participation

# Scale invariance: multiplying GRID and broadcast by the same positive factor
# must not alter the normalized structural drive.
base={f'G{i}':((-1)**i)*(i/7.0) for i in range(1,11)}
scaled={k:v*37.0 for k,v in base.items()}
x=derive_grid_face_drive(base,1.4,winner='G10')
y=derive_grid_face_drive(scaled,1.4*37.0,winner='G10')
for k in ('entropy','dominance','participation','broadcast_strength','arousal','tension','curiosity','dispersion','event_rate_multiplier','hold_scale'):
    close(getattr(x,k),getattr(y,k),1e-8)

# Permutation safety: no G-number is assigned a fixed emotion meaning.
perm={f'G{i}':base[f'G{11-i}'] for i in range(1,11)}
p=derive_grid_face_drive(perm,1.4,winner='G1')
for k in ('entropy','dominance','participation','broadcast_strength'):
    close(getattr(x,k),getattr(p,k),1e-10)

# Transition should react to geometry change and winner change without semantic labels.
prev={f'G{i}':(1.0 if i==1 else 0.0) for i in range(1,11)}
cur_same=dict(prev)
cur_flip={f'G{i}':(-1.0 if i==1 else 0.0) for i in range(1,11)}
stable=derive_grid_face_drive(cur_same,1.0,winner='G1',previous_cell_states=prev,previous_winner='G1')
changed=derive_grid_face_drive(cur_flip,1.0,winner='G2',previous_cell_states=prev,previous_winner='G1')
assert stable.transition==0.0 and not stable.winner_changed
assert changed.transition>stable.transition and changed.winner_changed
assert changed.novelty_kick>stable.novelty_kick
assert changed.event_rate_multiplier>stable.event_rate_multiplier

print({'pass':True,'concentrated':a.to_dict(),'distributed':b.to_dict(),'stable':stable.to_dict(),'changed':changed.to_dict()})
