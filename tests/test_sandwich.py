from pathlib import Path
import numpy as np
import yaml
from wingcheck.excel import Workbook
from wingcheck.model import normalize
from wingcheck.sandwich import rectangles
from wingcheck.sandwich_fem import mesh,quad_weights


def inputs():
    cfg=yaml.safe_load(Path('config.yaml').read_text(encoding='utf-8'))
    return normalize(Workbook(cfg['excel']),cfg),cfg


def test_closed_sleeve_and_web_ends():
    m,c=inputs()
    root=rectangles(m,c,0,'A')
    assert len(root)==20 # two caps, two cores, sixteen oriented sleeve partitions
    assert len(rectangles(m,c,.8,'A'))==11
    assert len(rectangles(m,c,1.3,'A'))==11
    assert len(rectangles(m,c,m['half_span'],'B'))==11
    rear=[r for r in root if r['name']=='rear_core'][0]
    front=[r for r in root if r['name']=='front_core'][0]
    np.testing.assert_allclose(rear['y1']-rear['y0'],.005,atol=1e-12)
    wall=m['stations'][0]['web_required']
    np.testing.assert_allclose(front['y0']-wall-(rear['y1']+wall),.035,atol=1e-12)


def test_minimum_width_preserves_taper_and_positive_tip_connection():
    from wingcheck.sections import interpolate
    m,c=inputs()
    crossing=1.2861788617886178
    assert any(abs(s['x']-crossing)<1e-10 for s in m['stations'])
    assert interpolate(m,1.25,'width_top')>.006
    for x in [crossing,1.35,1.4]:
        np.testing.assert_allclose(interpolate(m,x,'width_top'),.006,atol=1e-12)
        parts=rectangles(m,c,x,'B')
        core=next(r for r in parts if r['name']=='rear_core')
        top=next(r for r in parts if r['name']=='top')
        assert min(core['y1'],top['y1'])-max(core['y0'],top['y0'])>0
        assert all(r['y0']>=top['y0']-1e-12 and r['y1']<=top['y1']+1e-12 for r in parts)
    assert interpolate(m,1.4,'web_required')==.0001


def test_mesh_materials_and_interface_affine_consistency():
    m,c=inputs()
    c['fem']['base_length_m']=.2
    data=mesh(m,c,'A',False,1)
    assert set(data['groups'])=={'CAP','CORE','V0','V1','H0','H1'}
    assert data['mass']>0
    for slave,masters in data['equations']:
        np.testing.assert_allclose(sum(w for _,w in masters),1,atol=1e-9)
        np.testing.assert_allclose(sum((data['nodes'][n]*w for n,w in masters)),data['nodes'][slave],atol=1e-9)


def test_thin_cap_inner_edges_tied_on_both_halves():
    m,c=inputs();c['fem']['base_length_m']=.2
    data=mesh(m,c,'A',True,1)
    slaves={n for n,_ in data['equations']}
    height=np.interp(1.3,[s['x'] for s in m['stations']],[s['height'] for s in m['stations']])
    inner=-height/2+.0002
    for x in [-1.3,1.3]:
        matches=[n for n,xyz in data['nodes'].items() if abs(xyz[0]-x)<1e-10 and abs(xyz[1])<1e-10 and abs(xyz[2]-inner)<1e-10]
        assert matches
        assert all(n in slaves for n in matches)


def test_quadratic_surface_load_conservation_on_taper():
    corner=[np.array(p,dtype=float) for p in [(0,0,0),(1,0,0),(1,1,0),(0,2,0)]]
    xyz=corner+[(corner[j]+corner[(j+1)%4])/2 for j in range(4)]
    nodes={i+1:p for i,p in enumerate(xyz)}
    w=quad_weights(nodes,list(nodes),lambda p:1/(2-p[0]))
    np.testing.assert_allclose(sum(w),1,atol=1e-12)
    np.testing.assert_allclose(sum(w[i]*xyz[i][0] for i in range(8)),.5,atol=1e-12)
