"""Explicit synthetic integration benchmark, NEVER Excel/Biest results.

Run: .venv/Scripts/python.exe tests/run_fem_benchmark.py
Exercises installed FreeCAD, Gmsh, ccx and actual DAT parsing on three meshes.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import yaml
from wingcheck.fem import diagnose,execute
from wingcheck.excel import dump_json

cfg = yaml.safe_load(Path('config.yaml').read_text(encoding='utf-8'))
cfg['geometry']['sandwich']['enabled']=False # Homogener Referenzfall bleibt unabhängig vom aktiven Biest-Modell.
cfg['geometry'].update(ply_thickness_m=.001,manufacturing_plan_confirmed=True)
cfg['geometry']['web'].update(enabled=True,thickness_m=.002,E_Pa=70e9,G_Pa=70e9/2.6,density_kg_m3=2700)
cfg['test'].update(support_width_m=.015,load_width_m=.02)
cfg['flight']['load_kind']='limit'
cfg['flight']['distribution']='uniform' # Defined reference case, independent of the active wing load.
cfg['fem'].update(mesh_levels=[1,2,3],base_length_m=.03,nonlinear=False)
mat = {'E1':70e9,'E2':70e9,'E3':70e9,'G12':70e9/2.6,'G13':70e9/2.6,'G23':70e9/2.6,
       'nu12':.3,'nu13':.3,'nu23':.3,'density':2700,'provisional':True}
station = {'width_top':.02,'width_bottom':.02,'height':.02,'plies_top':2,'plies_bottom':2,
           'theoretical_thickness':.002,'web_required':.002,'source':'synthetic benchmark'}
model = {'missing':[],'half_span':.15,'stations':[{**station,'x':0},{**station,'x':.15}],
         'material':mat,'parameters':{'support_fraction':.6,'total_lift':20,'test_mass':1.,'modal_mass':1.}}
out = Path('benchmark_results')
out.mkdir(exist_ok=True)
result = execute(model,cfg,out,diagnose(cfg))
dump_json(out/'synthetic_benchmark.json',result)
print(result)
