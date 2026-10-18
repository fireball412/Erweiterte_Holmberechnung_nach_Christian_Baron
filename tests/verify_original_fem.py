"""Audit completed original-model solver files and report mode parity honestly."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import re
import yaml
import numpy as np
from wingcheck.postprocess import parse_dat,convergence
from wingcheck.excel import dump_json
from wingcheck.visualization import fem_picture
from wingcheck.equilibrium import input_nodes_loads,averaged_support_reactions

out=Path('results')
result=json.loads((out/'fem_progress.json').read_text(encoding='utf-8'))
configuration=yaml.safe_load((out/'used_config.yaml').read_text(encoding='utf-8'))
assert set(result['variants'])=={'A','B'}
checks={}
for variant,record in result['variants'].items():
    assert len(record['meshes'])==3
    details=[]
    for row in record['meshes']:
        folder=out/'fem_sandwich_q20'/variant/f"level_{row['level']}"
        for case in ['flight','test']:
            work=folder/case
            mesh=json.loads((work/'mesh_si.json').read_text(encoding='utf-8'))
            assert all(len(conn)==20 and len(set(conn))==20 for conn in mesh['elements'])
            assert sum(len(ids) for ids in mesh['groups'].values())==len(mesh['elements'])
            for job in ['static']+(['modal'] if case=='test' else []):
                log=(work/f'{job}.log').read_text(errors='replace')
                assert 'Job finished' in log and '*ERROR' not in log.upper(),str(work/job)
                data=parse_dat(work/f'{job}.dat')
                assert data['displacements']
                assert np.isfinite(np.array(list(data['displacements'].values()))).all()
                if job=='static':
                    assert len(data['stresses'])==len(mesh['elements'])
                    if case=='test':
                        span=max(abs(p[0]) for p in mesh['nodes'].values())
                        for side,xpos in [('left',-span),('right',span)]:
                            ids=[int(n) for n,p in mesh['nodes'].items() if abs(p[0]-xpos)<1e-9 and p[2]>0]
                            row['test_'+side+'_tip_m']=float(np.mean([data['displacements'][n][2] for n in ids]))
                        allnodes,loads=input_nodes_loads(work/'static.inp')
                        applied=sum(f[2] for f in loads.values())
                        if configuration['test'].get('load_region')=='rear_web':
                            c=configuration['geometry']['sandwich']
                            centroid=sum(allnodes[n][1]*f[2] for n,f in loads.items())/applied
                            np.testing.assert_allclose(centroid,c['rear_center_y_m'],atol=1e-10)
                            assert all(abs(allnodes[n][0])<=configuration['test']['load_width_m']/2+1e-10 for n in loads)
                            row['test_load_centroid_y_m']=float(centroid)
                        reaction=sum(data['forces'][int(n)][2]-loads.get(int(n),np.zeros(3))[2] for n in mesh['nodes'])
                        row['test_reaction_N']=float(reaction)
                        row['test_reaction_residual_N']=float(reaction+applied)
                        row['test_reaction_method']='Gesamter physischer Knotenrest RF minus Last; innere MPC-Kraefte heben sich im Resultat auf.'
                        if configuration['test'].get('fem_support_model') in ['fixed_vertical_band','fixed_vertical_section','bottom_contact_line']:
                            model=json.loads((out/'normalized_input.json').read_text(encoding='utf-8'))
                            a=configuration['test'].get('supports_m')
                            if a is None:
                                model=json.loads((out/'normalized_input.json').read_text(encoding='utf-8'))
                                p=model['half_span']*model['parameters']['support_fraction'];a=[-p,p]
                            half_width=0. if configuration['test']['fem_support_model'] in ['fixed_vertical_section','bottom_contact_line'] else configuration['test']['support_width_m']/2
                            ids=[int(n) for n,p in mesh['nodes'].items() if any(abs(p[0]-s)<=half_width+1e-10 for s in a) and (configuration['test']['fem_support_model']!='bottom_contact_line' or abs(p[2]+np.interp(abs(p[0]),[s['x'] for s in model['stations']],[s['height'] for s in model['stations']])/2)<1e-7)]
                            assert max(abs(data['displacements'][n][2]) for n in ids)<1e-12
                            row['test_support_nodes']=len(ids)
                            row['test_support_max_abs_uz_m']=max(abs(data['displacements'][n][2]) for n in ids)
                    assert abs(row[case+'_reaction_residual_N'])/max(1,abs(row[case+'_reaction_N']))<1e-4
                    if case=='flight':
                        if configuration['geometry']['sandwich']['rear_end_m']>=max(abs(p[0]) for p in mesh['nodes'].values())-1e-9:
                            assert abs(row['flight_tip_m']-row['flight_bottom_tip_m'])<1e-3*abs(row['flight_tip_m'])
                        allnodes,loads=input_nodes_loads(work/'static.inp')
                        applied_moment=sum((np.cross(allnodes[n],f) for n,f in loads.items()))
                        if configuration['flight']['distribution']=='chord_proportional':
                            from wingcheck.loads import chord_resultants
                            model=json.loads((out/'normalized_input.json').read_text(encoding='utf-8'))
                            expected=chord_resultants(model,configuration)
                            np.testing.assert_allclose(sum(f[2] for f in loads.values()),expected['force_N'],rtol=1e-9)
                            np.testing.assert_allclose(-applied_moment[1],expected['moment_Nm'],rtol=1e-6)
                            row['flight_applied_force_N']=float(sum(f[2] for f in loads.values()))
                            row['flight_applied_root_moment_Nm']=float(-applied_moment[1])
                        reaction_moment=np.zeros(3)
                        for n,p in allnodes.items():
                            if abs(p[0])<1e-10:
                                reaction=np.array(data['forces'][n])-loads.get(n,np.zeros(3))
                                reaction_moment+=np.cross(p,reaction)
                        residual=reaction_moment+applied_moment
                        assert np.linalg.norm(residual)/max(1,np.linalg.norm(applied_moment))<1e-4
                        row['flight_reaction_moment_Nm']=reaction_moment.tolist()
                        row['flight_moment_balance_residual_Nm']=residual.tolist()
                    else:
                        supports=averaged_support_reactions(work/'static.inp',len(mesh['nodes']))
                        if supports:row['test_averaged_support_reactions']=supports
                        else:row.pop('test_averaged_support_reactions',None)
                else:
                    assert len(data['frequencies'])==6 and min(data['frequencies'])>0
                    nodes={int(k):np.array(v) for k,v in mesh['nodes'].items()}
                    lookup={tuple(round(v*1e10) for v in p):n for n,p in nodes.items()}
                    pairs=[(n,lookup.get(tuple(round(v*1e10) for v in [-p[0],p[1],p[2]]))) for n,p in nodes.items()]
                    pairs=[(a,b) for a,b in pairs if b is not None]
                    classes,errors,root_ratios=[],[],[]
                    for shape in data['mode_shapes']:
                        a=np.array([shape[n][2] for n,m in pairs]);b=np.array([shape[m][2] for n,m in pairs])
                        norm=max(np.linalg.norm(a),1e-30)
                        symmetric=np.linalg.norm(a-b)/norm;antisymmetric=np.linalg.norm(a+b)/norm
                        errors.append(dict(symmetric=float(symmetric),antisymmetric=float(antisymmetric)))
                        classes.append('quasi-symmetrisch' if symmetric<.1 else 'quasi-antisymmetrisch' if antisymmetric<.1 else 'gemischt')
                        root=max(abs(shape[n][2]) for n,p in nodes.items() if abs(p[0])<1e-9)
                        root_ratios.append(float(root/max(np.linalg.norm(v) for v in shape.values())))
                    row['mode_symmetry']=classes;row['mode_parity_errors']=errors;row['mode_root_motion_ratios']=root_ratios
                    if row['level']==record['meshes'][-1]['level'] and '--skip-mode-images' not in sys.argv:
                        faces=[t for q in mesh['faces'] for t in [[q[0],q[1],q[2]],[q[0],q[2],q[3]]]]
                        length=max(abs(p[0]) for p in nodes.values())
                        for j,(frequency,shape) in enumerate(zip(data['frequencies'],data['mode_shapes']),1):
                            amplitude=max(np.linalg.norm(v) for v in shape.values())
                            fem_picture(work/f'mode_{j}',nodes,faces,shape,f'Biest {variant}: Mode {j}, {frequency:.4g} Hz, {classes[j-1]}',.03*length/amplitude,mode=True)
            details.append(dict(level=row['level'],case=case,nodes=len(mesh['nodes']),elements=len(mesh['elements']),
                                reaction_residual_N=row[case+'_reaction_residual_N'],mass_kg=row[case+'_mesh_mass_kg']))
        np.testing.assert_allclose(row['test_mesh_mass_kg'],2*row['flight_mesh_mass_kg'],rtol=1e-9)
        if 'flight_nonlinear_m' in row:
            work=folder/'flight'
            log=(work/'nonlinear.log').read_text(errors='replace')
            assert 'Job finished' in log and '*ERROR' not in log.upper()
            records=[line.split() for line in (work/'nonlinear.sta').read_text().splitlines() if line.strip() and line.split()[0].isdigit()]
            assert records and np.isclose(float(records[-1][4]),1,rtol=1e-6)
            assert abs(row['flight_nonlinear_reaction_residual_N'])<1e-2
            details.append(dict(level=row['level'],case='flight_nonlinear',full_load_completed=True,qualitative_only=True))
    record['convergence']=convergence(record['meshes'],configuration['fem']['convergence_relative'])
    checks[variant]=dict(verified_cases=details,convergence=record['convergence'])
dump_json(out/'original_fem_validation.json',checks)
dump_json(out/'fem_progress.json',result)
print('12 Originalnetze / 18 lineare Statik- und Modalläufe anhand tatsächlicher Dateien geprüft.')
