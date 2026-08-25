import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'tools'/'trigger2_dynamic_codebook_dataset_generator_v1.py'
spec=importlib.util.spec_from_file_location('g',P); g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def test_full_s3_balance_four_templates():
    atoms=('ATOM_A','ATOM_B','ATOM_C'); rows=g.generate_rows(atoms); r=g.validate_rows(rows,atoms)
    assert r['pass'],r; assert r['realized_s3']==6; assert r['pair_count_min']==r['pair_count_max']==8; assert len(rows)==72
    assert r['templates']==sorted(g.TRAIN_TEMPLATES); assert r['frozen_templates_seen']==[]

def test_target_is_causally_derived_from_realized_mapping():
    atoms=('ATOM_A','ATOM_B','ATOM_C'); rows=g.generate_rows(atoms); rows[0]=dict(rows[0]); rows[0]['target_symbol']='ATOM_C' if rows[0]['target_symbol']!='ATOM_C' else 'ATOM_B'; rows[0]['target']=rows[0]['target_symbol']
    r=g.validate_rows(rows,atoms); assert not r['pass']; assert 'TARGET_NOT_DERIVED_FROM_REALIZED_MAPPING' in r['failures']

def test_class_leak_fails():
    with pytest.raises(ValueError,match='CLASS_LABEL_LEAK_OUTSIDE_CODEBOOK'):
        g.assert_no_class_leak_outside_codebook('[CODEBOOK] ALLOW=A ; DENY=B ; ABSTAIN=C [/CODEBOOK]\n[SITUATION] This is ALLOW. [/SITUATION]')

def test_rejected_or_atom_fails():
    with pytest.raises(ValueError,match='REJECTED_ATOM_PRESENT'): g.validate_atom_inventory(['A','or','C'])
