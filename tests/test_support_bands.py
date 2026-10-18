"""The prescribed bands must not overlap dependent MPC degrees of freedom."""
from pathlib import Path
import yaml
from wingcheck.excel import Workbook
from wingcheck.model import normalize
from wingcheck.sandwich_fem import mesh,input_file
import numpy as np
import pytest


@pytest.mark.parametrize('support_model',['fixed_vertical_band','fixed_vertical_section','bottom_contact_line'])
def test_fixed_vertical_bands_at_ply_interface(tmp_path,support_model):
    cfg=yaml.safe_load(Path('config.yaml').read_text(encoding='utf-8'))
    cfg['test']['fem_support_model']=support_model
    model=normalize(Workbook(cfg['excel']),cfg)
    data=mesh(model,cfg,'A',True,2)
    path=tmp_path/'test.inp'
    input_file(path,data,model,cfg,'test')
    lines=path.read_text().splitlines()
    boundary=set();dependent=set();block=''
    for j,line in enumerate(lines):
        if line.startswith('*'):
            block=line.split(',')[0]
            if block=='*EQUATION':
                fields=lines[j+2].split(',')
                dependent.add((int(fields[0]),int(fields[1])))
        elif block=='*BOUNDARY':
            fields=line.split(',');boundary.add((int(fields[0]),int(fields[1])))
    a=model['half_span']*model['parameters']['support_fraction']
    half_width=0. if support_model in ['fixed_vertical_section','bottom_contact_line'] else cfg['test']['support_width_m']/2
    required={(n,3) for n,p in data['nodes'].items() if abs(abs(p[0])-a)<=half_width+1e-10 and (support_model!='bottom_contact_line' or abs(p[2]+np.interp(abs(p[0]),[s['x'] for s in model['stations']],[s['height'] for s in model['stations']])/2)<1e-7)}
    assert required and required<=boundary
    assert {entry for entry in boundary if entry[1]==3}==required
    assert not boundary & dependent


def test_rear_web_load_and_modal_mass_share_footprint(tmp_path):
    cfg=yaml.safe_load(Path('config.yaml').read_text(encoding='utf-8'))
    cfg['test']['load_region']='rear_web'
    model=normalize(Workbook(cfg['excel']),cfg)
    data=mesh(model,cfg,'B',True,1)
    path=tmp_path/'modal.inp'
    meta=input_file(path,data,model,cfg,'test',modal=True)
    yc=cfg['geometry']['sandwich']['rear_center_y_m']
    half=cfg['geometry']['sandwich']['core_width_m']/2+model['stations'][0]['web_required']
    assert all(abs(data['nodes'][n][0])<=.025+1e-10 and abs(data['nodes'][n][1]-yc)<=half+1e-10 for n in meta['loads'])
    force=sum(meta['loads'].values())
    np.testing.assert_allclose(force,-model['parameters']['test_mass']*cfg['test']['gravity'])
    np.testing.assert_allclose(sum(data['nodes'][n][1]*f for n,f in meta['loads'].items())/force,yc,atol=1e-12)
    masses={};node=None
    lines=path.read_text().splitlines()
    for j,line in enumerate(lines):
        if line.startswith('*ELEMENT,TYPE=MASS'):
            node=int(lines[j+1].split(',')[1])
        if line.startswith('*MASS,ELSET='):
            masses[node]=float(lines[j+1])
    assert masses and set(masses)<=set(meta['loads'])
    np.testing.assert_allclose(sum(masses.values()),model['parameters']['modal_mass'])
    np.testing.assert_allclose(sum(data['nodes'][n][1]*m for n,m in masses.items())/sum(masses.values()),yc,atol=1e-12)
