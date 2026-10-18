"""Recompute only test static/modal cases after a support change; retain flight."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import shutil
import yaml
import numpy as np
from wingcheck.excel import Workbook,dump_json
from wingcheck.model import normalize
from wingcheck.sandwich_fem import mesh,input_file
from wingcheck.fem import run_command,reaction_balance
from wingcheck.postprocess import parse_dat,convergence
from wingcheck.gallery import render_gallery

out=Path('results')
archive=Path('results_partial_section_supports') # Unterbrochener Zwischenstand, kein abgeschlossener Vergleichslauf.
if not archive.exists():
    shutil.copytree(out,archive)
cfg=yaml.safe_load(Path('config.yaml').read_text(encoding='utf-8'))
model=normalize(Workbook(cfg['excel']),cfg)
result=json.loads((out/'fem_progress.json').read_text(encoding='utf-8'))
(out/'used_config.yaml').write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False),encoding='utf-8')
dump_json(out/'normalized_input.json',model)
result['complete']=False
result['status']='läuft – untere Kontaktlinien, Biegeneigung frei; Last auf hinterem Steg'
dump_json(out/'fem_progress.json',result)
for variant,record in result['variants'].items():
    for row in record['meshes']:
        level=row['level']
        folder=out/'fem_sandwich_q20'/variant/f'level_{level}'/'test'
        raw=mesh(model,cfg,variant,True,level)
        row.pop('test_averaged_support_reactions',None)
        for job,modal in [('static',False),('modal',True)]:
            print(f'{variant} Netz {level}: {job}',flush=True)
            old=(folder/f'{job}.inp').read_text(encoding='ascii')
            meta=input_file(folder/f'{job}.inp',raw,model,cfg,'test',modal=modal)
            log=(folder/f'{job}.log').read_text(errors='replace')
            if old!=(folder/f'{job}.inp').read_text(encoding='ascii') or 'Job finished' not in log or '*ERROR' in log.upper():
                log=run_command([cfg['paths']['calculix'],'-i',job],folder,folder/f'{job}.log',cfg['fem']['timeout_s'])
            assert 'Job finished' in log and '*ERROR' not in log.upper()
            data=parse_dat(folder/f'{job}.dat')
            # Every physical node in both support bands must be fixed vertically.
            a=model['parameters']['support_fraction']*model['half_span']
            supports=cfg['test']['supports_m'] or [-a,a]
            half_width=0. if cfg['test']['fem_support_model'] in ['fixed_vertical_section','bottom_contact_line'] else cfg['test']['support_width_m']/2
            ids=[n for n,p in raw['nodes'].items() if any(abs(p[0]-s)<=half_width+1e-10 for s in supports) and (cfg['test']['fem_support_model']!='bottom_contact_line' or abs(p[2]+np.interp(abs(p[0]),[s['x'] for s in model['stations']],[s['height'] for s in model['stations']])/2)<1e-7)]
            shapes=data['mode_shapes'] if modal else [data['displacements']]
            assert all(max(abs(shape[n][2]) for n in ids)<1e-12 for shape in shapes)
            row['test_support_nodes']=len(ids)
            row['test_support_max_abs_uz_m']=max(abs(data['displacements'][n][2]) for n in ids)
            if modal:
                fractions=[float(np.sum(np.array(list(s.values()))[:,2]**2)/np.sum(np.array(list(s.values()))**2)) for s in data['mode_shapes']]
                selected=next((j for j,f in enumerate(fractions) if f>=.5),0)
                row.update(frequency_Hz=data['frequencies'][selected],frequencies_Hz=data['frequencies'],selected_mode=selected+1,vertical_fractions=fractions)
            else:
                h=model['stations'][0]['height']/2
                ids=sorted([n for n,p in raw['nodes'].items() if abs(p[0])<1e-9 and abs(p[2]-h)<1e-9],key=lambda n:raw['nodes'][n][1])
                yy=[raw['nodes'][n][1] for n in ids];ww=[data['displacements'][n][2] for n in ids]
                c=cfg['geometry']['sandwich'];low=c['rear_center_y_m']+c['core_width_m']/2+model['stations'][0]['web_required'];high=low+c['pocket_width_m']
                sample=sorted(set([low,high]+[y for y in yy if low<y<high]))
                row['test_root_m']=float(np.trapezoid(np.interp(sample,yy,ww),sample)/(high-low))
                reaction,residual=reaction_balance(data,meta)
                row['test_reaction_N']=reaction;row['test_reaction_residual_N']=residual
                if level in [record['meshes'][0]['level'],record['meshes'][-1]['level']]:
                    render_gallery(folder,raw['nodes'],raw['elements'],raw['faces'],data,folder/'geometry.json',f'Biest {variant}: untere Kontaktlinien; Last auf hinterem Steg',prefix='static_')
            dump_json(folder/f'{job}.summary.json',dict(frequencies=data['frequencies'],displacement_nodes=len(data['displacements']),stress_elements=len(data['stresses'])))
            dump_json(out/'fem_progress.json',result)
    record['convergence']=convergence(record['meshes'],cfg['fem']['convergence_relative'])
result['status']='ausgeführt'
result['complete']=True
dump_json(out/'fem_progress.json',result)
print('Alle zwölf Versuchsläufe abgeschlossen; uz=0 an allen Auflagerknoten geprüft.',flush=True)
