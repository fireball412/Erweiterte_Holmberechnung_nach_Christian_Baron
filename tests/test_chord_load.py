import copy
from pathlib import Path
import numpy as np
import yaml
from wingcheck.model import normalize
from wingcheck.excel import Workbook
from wingcheck.loads import chord_load,chord_resultants
from wingcheck.sandwich_fem import mesh,input_file


def inputs():
    c=yaml.safe_load(Path('config.yaml').read_text(encoding='utf-8'))
    return normalize(Workbook(c['excel']),c),c


def test_planform_force_and_first_moment():
    m,c=inputs();r=chord_resultants(m,c)
    np.testing.assert_allclose(r['half_area_m2']*2,.521,rtol=1e-12)
    x=np.array(sorted(set(np.linspace(0,m['half_span'],10001).tolist()+[p['x'] for p in m['planform']])))
    q=chord_load(m,c,x)
    np.testing.assert_allclose(np.trapezoid(q,x),m['parameters']['total_lift']/2,rtol=1e-12)
    np.testing.assert_allclose(np.trapezoid(q*x,x),r['moment_Nm'],rtol=1e-8)
    assert r['moment_Nm']<m['reconstructed']['root_moment_Nm']
    assert r['root_q_N_m']>r['tip_q_N_m']>0


def test_fem_consistent_chord_resultants(tmp_path):
    m,c=inputs();data=mesh(m,c,'B',False,1)
    meta=input_file(tmp_path/'flight.inp',data,m,c,'flight')
    force=sum(meta['loads'].values())
    moment=sum(data['nodes'][n][0]*f for n,f in meta['loads'].items())
    r=chord_resultants(m,c)
    np.testing.assert_allclose(force,r['force_N'],rtol=1e-12)
    np.testing.assert_allclose(moment,r['moment_Nm'],rtol=1e-6)


def test_test_case_input_unchanged_by_flight_distribution(tmp_path):
    m,c=inputs();data=mesh(m,c,'B',True,1)
    input_file(tmp_path/'chord.inp',data,m,c,'test',modal=True)
    uniform=copy.deepcopy(c);uniform['flight']['distribution']='uniform'
    input_file(tmp_path/'uniform.inp',data,m,uniform,'test',modal=True)
    assert (tmp_path/'chord.inp').read_bytes()==(tmp_path/'uniform.inp').read_bytes()
