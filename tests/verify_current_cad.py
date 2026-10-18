"""Generate a fresh CAD check request from the active solver checkpoint."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import yaml
from wingcheck.excel import dump_json
from wingcheck.fem import run_command
out=Path('results').resolve()
cfg=yaml.safe_load((out/'used_config.yaml').read_text(encoding='utf-8'))
data=json.loads((out/'fem_progress.json').read_text(encoding='utf-8'))
cases=[]
for variant in ['A','B']:
    row=data['variants'][variant]['meshes'][0]
    for case in ['flight','test']:
        cases.append(dict(variant=variant,case=case,fcstd=str(out/'fem_sandwich_q20'/variant/f"level_{row['level']}"/case/'spar.FCStd'),mesh_mass_kg=row[case+'_mesh_mass_kg']))
request=dict(cases=cases,rho_core=cfg['geometry']['sandwich']['core_density'],rho_cfk=cfg['material']['density'],output=str(out/'cad_validation.json'))
path=out/'cad_check_request.json';dump_json(path,request)
run_command([cfg['paths']['freecad_python'],Path('wingcheck/cad_check.py').resolve(),path],Path.cwd(),out/'cad_validation.log',120)
print('Vier aktuelle CAD-Modelle geöffnet, gültige Körper und Massen geprüft.')
