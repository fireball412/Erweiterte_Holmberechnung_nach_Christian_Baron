"""Actual C3D20R solver verification: homogeneous solid cantilever, uniform load.

Synthetic reference only, independent of Biest dimensions and input values.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import yaml
import numpy as np
from wingcheck.sandwich_fem import quadratic_mesh,input_file,HEX_FACES
from wingcheck.fem import run_command,reaction_balance
from wingcheck.postprocess import parse_dat
from wingcheck.excel import dump_json

cfg=yaml.safe_load(Path('config.yaml').read_text(encoding='utf-8'))
L,b,h,E,nu,F=.3,.02,.02,70e9,.3,10.
nodes={};lookup={}
for i,x in enumerate(np.linspace(0,L,9)):
    for j,y in enumerate(np.linspace(0,b,3)):
        for k,z in enumerate(np.linspace(-h/2,h/2,3)):
            lookup[i,j,k]=len(nodes)+1;nodes[len(nodes)+1]=np.array([x,y,z])
elements=[]
for i in range(8):
    for j in range(2):
        for k in range(2):
            elements.append([lookup[i,j,k],lookup[i,j+1,k],lookup[i,j+1,k+1],lookup[i,j,k+1],
                             lookup[i+1,j,k],lookup[i+1,j+1,k],lookup[i+1,j+1,k+1],lookup[i+1,j,k+1]])
owners={}
for conn in elements:
    for face in HEX_FACES:
        q=[conn[i] for i in face];key=tuple(sorted(q))
        owners[key]=None if key in owners else q
data=quadratic_mesh(dict(nodes=nodes,elements=elements,faces=[q for q in owners.values() if q],
                        groups={'CAP':list(range(1,len(elements)+1))},equations=[],mass=L*b*h*2700,volume=L*b*h),[])
mat=dict(E1=E,E2=E,E3=E,G12=E/(2*(1+nu)),G13=E/(2*(1+nu)),G23=E/(2*(1+nu)),nu12=nu,nu13=nu,nu23=nu,density=2700)
model=dict(half_span=L,material=mat,stations=[dict(x=0,height=h,width_top=b,web_required=0),dict(x=L,height=h,width_top=b,web_required=0)],
           parameters=dict(total_lift=2*F,test_mass=1,modal_mass=1,support_fraction=.6))
folder=Path('results/c3d20r_reference');folder.mkdir(exist_ok=True)
meta=input_file(folder/'reference.inp',data,model,cfg,'flight')
run_command([cfg['paths']['calculix'],'-i','reference'],folder,folder/'reference.log')
actual=parse_dat(folder/'reference.dat')
ids=[n for n,xyz in data['nodes'].items() if abs(xyz[0]-L)<1e-12]
delta=float(np.mean([actual['displacements'][n][2] for n in ids]))
expected=F*L**3/(8*(E*b*h**3/12))
reaction,residual=reaction_balance(actual,meta)
result=dict(scope='synthetic_reference_not_Biest',element='C3D20R',E_Pa=E,nu=nu,L_m=L,b_m=b,h_m=h,F_N=F,
            tip_m=delta,Euler_Bernoulli_tip_m=expected,relative_deviation=(delta-expected)/expected,
            reaction_N=reaction,reaction_residual_N=residual)
input_file(folder/'reference_modal.inp',data,model,cfg,'flight',modal=True)
run_command([cfg['paths']['calculix'],'-i','reference_modal'],folder,folder/'reference_modal.log')
frequencies=parse_dat(folder/'reference_modal.dat')['frequencies']
expected_f=1.875104068711961**2/(2*np.pi*L**2)*np.sqrt((E*b*h**3/12)/(2700*b*h))
result.update(frequencies_Hz=frequencies,Euler_Bernoulli_frequency_Hz=float(expected_f),
              frequency_relative_deviation=float((frequencies[0]-expected_f)/expected_f))
dump_json(folder/'validation.json',result)
assert abs(result['relative_deviation'])<.02,result
assert abs(residual)<1e-4,result
assert abs(result['frequency_relative_deviation'])<.02,result
print('C3D20R-Referenz mit tatsächlichem Solver: '+str(result))
