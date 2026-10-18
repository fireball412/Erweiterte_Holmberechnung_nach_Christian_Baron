"""Finalize actual Biest results from audited checkpoint without rerunning solvers.

Run only after both variants and all three mesh levels completed.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hashlib
import json
import yaml
from wingcheck.excel import Workbook,dump_json
from wingcheck.model import normalize
from wingcheck.analysis import compute
from wingcheck.postprocess import parse_dat,convergence
from wingcheck.gallery import render_gallery
from wingcheck.visualization import plots,convergence_picture
from wingcheck.report import write_report

out=Path('results')
cfg=yaml.safe_load((out/'used_config.yaml').read_text(encoding='utf-8'))
fem=json.loads((out/'fem_progress.json').read_text(encoding='utf-8'))
assert set(fem['variants'])=={'A','B'}
for variant,record in fem['variants'].items():
    assert len(record['meshes'])==3
    assert all(all(k in row for k in ['flight_tip_m','test_root_m','frequency_Hz']) for row in record['meshes'])
    record['convergence']=convergence(record['meshes'],cfg['fem']['convergence_relative'])
    convergence_picture(out/'fem_sandwich_q20'/variant/'convergence',record['meshes'])
    finest=record['meshes'][-1]
    for case in ['flight','test']:
        folder=out/'fem_sandwich_q20'/variant/f"level_{finest['level']}"/case
        mesh=json.loads((folder/'mesh_si.json').read_text(encoding='utf-8'))
        import numpy as np
        nodes={int(k):np.array(v) for k,v in mesh['nodes'].items()}
        for job in ['static']+(['nonlinear'] if case=='flight' and 'flight_nonlinear_m' in finest else []):
            data=parse_dat(folder/f'{job}.dat')
            assert data['displacements'] and data['stresses']
            expected=[folder/(job+'_'+name+suffix) for name in ['model','mesh','deformation','stress_xx'] for suffix in ['.png','.svg']]
            if all(p.exists() and p.stat().st_mtime>=(folder/f'{job}.dat').stat().st_mtime for p in expected):
                maximum=max(np.linalg.norm(v) for v in data['displacements'].values())
                meta=dict(label=f'Biest {variant}, {case}, {job}: bestätigte Annahmen',nodes=len(nodes),elements=len(mesh['elements']),
                          deformation_scale=.05*np.ptp(np.array(list(nodes.values()))[:,0])/maximum,
                          max_displacement_m=float(maximum),
                          max_abs_sigma_xx_integration_point_Pa=float(max(abs(v[0]) for values in data['stresses'].values() for v in values)),
                          images=[dict(file=job+'_'+name+'.png') for name in ['model','mesh','deformation','stress_xx']],
                          image_policy='Vorhandene Bilder aus demselben Solverlauf wiederverwendet; alle Bilddateien neuer als DAT.')
            else:
                meta=render_gallery(folder,nodes,mesh['elements'],mesh['faces'],data,folder/'geometry.json',f'Biest {variant}, {case}, {job}: bestätigte Annahmen',prefix=job+'_')
            meta.update(scope='Biest_assumed_materials',solver_dat=str(folder/f'{job}.dat'),
                        input_sha256=hashlib.sha256((folder/f'{job}.inp').read_bytes()).hexdigest(),
                        dat_sha256=hashlib.sha256((folder/f'{job}.dat').read_bytes()).hexdigest())
            dump_json(folder/f'{job}.gallery.json',meta)
            finest[case+'_'+job+'_sigma_xx_max_abs_Pa']=meta['max_abs_sigma_xx_integration_point_Pa']
fem['complete']=True
dump_json(out/'fem_progress.json',fem)
book=Workbook(cfg['excel']);model=normalize(book,cfg,cfg.get('cli_overrides'))
analysis=compute(model,cfg)
images=plots(model,cfg,analysis,out,fem)
diagnostics=json.loads((out/'diagnostics.json').read_text(encoding='utf-8'))
write_report(out,model,cfg,analysis,fem,diagnostics,images,book.inventory())
print('Original-FEM, Detailbilder und Report aktualisiert.')
