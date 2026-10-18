"""Independent 3D orthotropic solid FEM using FreeCAD, Gmsh and CalculiX.

No 1D result enters solver result tables. C3D10 uses positive-volume Gmsh
quadratic tetrahedra (Gmsh and CalculiX edge order differ: last two nodes swap).
Loads act on finite top-surface bands, supports on finite bottom bands.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
from .excel import dump_json
from .sections import section
from .postprocess import parse_dat,convergence


def run_command(args,cwd,log,timeout=300):
    env = dict(os.environ,OMP_NUM_THREADS='2')
    try:
        proc = subprocess.run([str(a) for a in args],cwd=cwd,env=env,
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        Path(log).write_bytes(exc.stdout or b'')
        raise RuntimeError(f'Zeitlimit {timeout}s überschritten; kein abgeschlossenes Volllastergebnis. Siehe {log}') from exc
    Path(log).write_bytes(proc.stdout)
    if proc.returncode:
        raise RuntimeError(f'Programmfehler {proc.returncode}; siehe {log}')
    return proc.stdout.decode(errors='replace')


def diagnose(cfg):
    output = {'python':sys.version,'packages':{}}
    import importlib.metadata
    for name in ['numpy','scipy','matplotlib','xlrd','openpyxl','PyYAML']:
        try:
            output['packages'][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            output['packages'][name] = 'FEHLT'
    probes = {'freecad_python':['-c','import FreeCAD; print(FreeCAD.Version())'],
              'calculix':['-v'],'gmsh':['-version']}
    for name,flags in probes.items():
        exe = cfg['paths'].get(name) or shutil.which({'freecad_python':'FreeCADCmd','calculix':'ccx','gmsh':'gmsh'}[name])
        try:
            p = subprocess.run([exe]+flags,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=25)
            version = p.stdout.decode(errors='replace').strip()
            # ccx -v prints its version but exits with 201 on the Windows build.
            available = p.returncode==0 or (name=='calculix' and 'This is Version' in version)
            output[name] = {'path':exe,'available':available,'returncode':p.returncode,'version':version}
        except (OSError,TypeError,subprocess.TimeoutExpired) as exc:
            output[name] = {'path':exe,'available':False,'error':str(exc)}
    return output


def geometry_request(model,cfg,variant,out,full=True):
    blocks = []
    ss = model['stations']
    intervals = [(s['x'],t['x']) for s,t in zip(ss[:-1],ss[1:])]
    if full:
        intervals = [(-b,-a) for a,b in intervals[::-1]]+intervals
    for a,b in intervals:
        mid = section(model,cfg,(a+b)/2,variant)
        for part in mid['parts']:
            ends = []
            for x in [a,b]:
                # Sample inside interval to retain exact discrete ply count at drops.
                e = x+(1 if x==a else -1)*min((b-a)*1e-7,1e-9)
                s = section(model,cfg,e,variant)
                p = next(p for p in s['parts'] if p['name']==part['name'])
                ends.append([x,p['width'],p['z']-p['thickness']/2,p['z']+p['thickness']/2])
            blocks.append({'component':part['name'],'ends':ends})
    return {'blocks':blocks,'fcstd':str((out/'spar.FCStd').resolve()),
            'step':str((out/'spar.step').resolve()),'version_file':str((out/'freecad_version.json').resolve())}


def read_msh(path):
    lines = Path(path).read_text().splitlines()
    i = lines.index('$Nodes')
    n = int(lines[i+1])
    nodes = {int(t[0]):np.array([float(v)*.001 for v in t[1:4]])
             for t in [s.split() for s in lines[i+2:i+2+n]]}
    i = lines.index('$Elements')
    n = int(lines[i+1])
    elements = []
    faces = []
    for line in lines[i+2:i+2+n]:
        t = [int(v) for v in line.split()]
        conn = t[3+t[2]:]
        if t[1] == 11:
            conn[-2],conn[-1] = conn[-1],conn[-2]
            elements.append(conn)
        elif t[1] == 9:
            faces.append(conn)
    if not elements:
        raise ValueError('Gmsh lieferte keine quadratischen Tetraeder Typ 11')
    return nodes,elements,faces


def surface_weights(nodes,faces,predicate):
    weights = {}
    for face in faces:
        xyz = np.array([nodes[i] for i in face[:3]])
        centroid = xyz.mean(axis=0)
        if predicate(centroid):
            area = np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))/2
            # Consistent constant traction on quadratic triangular face:
            # zero corner force, one third area on each midside node.
            for node in face[3:]:
                weights[node] = weights.get(node,0)+area/3
    return weights


def write_input(path,nodes,elements,faces,model,cfg,variant,case,modal=False,nonlinear=False):
    L = model['half_span']
    pars = model['parameters']
    test = case == 'test'
    a = pars['support_fraction']*L
    supports = cfg['test']['supports_m'] or [-a,a]
    sw,lw = cfg['test']['support_width_m'],cfg['test']['load_width_m']
    def top(xyz):
        p = section(model,cfg,xyz[0],variant)['parts'][0]
        return abs(xyz[2]-(p['z']+p['thickness']/2)) < 2e-6
    def bottom(xyz):
        p = section(model,cfg,xyz[0],variant)['parts'][1]
        return abs(xyz[2]-(p['z']-p['thickness']/2)) < 2e-6
    bcs = []
    if test:
        for loc in supports:
            band = [i for i,xyz in nodes.items() if abs(xyz[0]-loc)<=sw/2 and bottom(xyz)]
            if not band:
                raise ValueError('Auflagenband ohne Netzknoten: Netz verfeinern oder Breite prüfen')
            bcs += [(i,3) for i in band]
        # Both bands constrain z only; three additional DOFs remove in-plane rigid motions.
        left = [i for i,xyz in nodes.items() if abs(xyz[0]-supports[0])<=sw/2 and bottom(xyz)]
        right = [i for i,xyz in nodes.items() if abs(xyz[0]-supports[1])<=sw/2 and bottom(xyz)]
        il,ir = min(left,key=lambda i:abs(nodes[i][1])),min(right,key=lambda i:abs(nodes[i][1]))
        bcs += [(il,1),(il,2),(ir,2)]
    else:
        bcs = [(i,d) for i,xyz in nodes.items() if abs(xyz[0])<1e-9 for d in [1,2,3]]
    force = cfg['test']['force_N'] if cfg['test']['force_N'] is not None else pars['test_mass']*cfg['test']['gravity']
    weights = surface_weights(nodes,faces,lambda xyz:top(xyz) and (abs(xyz[0])<=lw/2 if test else True))
    if not weights:
        raise ValueError('Keine Flächen im Lastband; Netz/Breite prüfen')
    total = sum(weights.values())
    loads = {i:(-force if test else pars['total_lift']/2)*v/total for i,v in weights.items()}
    # For flight, local surface width varies: weight each face by 1/b(x), then normalise.
    if not test:
        if cfg['flight']['distribution'] != 'uniform' or cfg['flight']['mass_relief']:
            raise ValueError('Räumlicher Adapter derzeit nur belegte Gleichlast ohne Massenentlastung')
        weights = {i:v/section(model,cfg,nodes[i][0],variant)['parts'][0]['width'] for i,v in weights.items()}
        total = sum(weights.values())
        F = pars['total_lift']/2
        if cfg['flight']['load_kind']=='ultimate':
            F /= cfg['flight']['safety_factor']
        loads = {i:F*v/total for i,v in weights.items()}
    m = model['material']
    lines = ['*HEADING','wingcheck SI m N kg s Pa; independent 3D C3D10','*NODE,NSET=ALL']
    lines += [f'{i},'+','.join(f'{v:.12g}' for v in xyz) for i,xyz in nodes.items()]
    groups = {'CAP':[],'WEB':[]}
    mesh_mass = 0.
    gravity_loads = {}
    lines += ['*ELEMENT,TYPE=C3D10,ELSET=SOLIDS']
    for e,conn in enumerate(elements,1):
        lines.append(f'{e},'+','.join(map(str,conn)))
        xyz = np.mean([nodes[i] for i in conn[:4]],axis=0)
        sec = section(model,cfg,xyz[0],variant)
        top_p,bot_p = sec['parts'][:2]
        cap = xyz[2] >= top_p['z']-top_p['thickness']/2-1e-9 or xyz[2] <= bot_p['z']+bot_p['thickness']/2+1e-9
        groups['CAP' if cap else 'WEB'].append(e)
        tet = np.array([nodes[i] for i in conn[:4]])
        volume = abs(np.linalg.det((tet[1:]-tet[0]).T))/6
        density = m['density'] if cap else cfg['geometry']['web']['density_kg_m3']
        mesh_mass += volume*density
        if test and cfg['test']['self_weight']:
            for k,node in enumerate(conn):
                fraction = -1/20 if k<4 else 1/5
                gravity_loads[node] = gravity_loads.get(node,0)-density*volume*cfg['test']['gravity']*fraction
    for name,ids in groups.items():
        if not ids:
            raise ValueError('Leere Materialgruppe '+name)
        lines += [f'*ELSET,ELSET={name}']
        lines += [','.join(map(str,ids[k:k+16])) for k in range(0,len(ids),16)]
    lines += ['*ORIENTATION,NAME=FIBER','1,0,0,0,1,0','*MATERIAL,NAME=UD',
              '*ELASTIC,TYPE=ENGINEERING CONSTANTS',
              ','.join(str(m[k]) for k in ['E1','E2','E3','nu12','nu13','nu23','G12','G13']),
              str(m['G23']), '*DENSITY',str(m['density'])]
    web = cfg['geometry']['web']
    nu = web['E_Pa']/(2*web['G_Pa'])-1
    if not -1 < nu < .5:
        raise ValueError('Isotropes Stegmodell: E/G ergeben unzulässiges nu')
    lines += ['*MATERIAL,NAME=WEBMAT','*ELASTIC',f"{web['E_Pa']},{nu}",'*DENSITY',str(web['density_kg_m3']),
              '*SOLID SECTION,ELSET=CAP,MATERIAL=UD,ORIENTATION=FIBER',
              '*SOLID SECTION,ELSET=WEB,MATERIAL=WEBMAT']
    if test:
        # Distributed mass over the same top load band, no rigid spider coupling.
        for j,(node,w) in enumerate(weights.items(),len(elements)+1):
            lines += [f'*ELEMENT,TYPE=MASS,ELSET=M{j}',f'{j},{node}',f'*MASS,ELSET=M{j}',
                      str(pars['modal_mass']*w/total)]
    lines += ['*BOUNDARY']+[f'{i},{d},{d}' for i,d in sorted(set(bcs))]
    lines += ['*STEP'+(',NLGEOM' if nonlinear else '')]
    if modal:
        lines += ['*FREQUENCY',str(cfg['analysis']['modes'])]
    else:
        lines += ['*STATIC']+(['0.1,1,1e-6,0.1'] if nonlinear else [])+['*CLOAD']
        lines += [f'{i},3,{v:.12g}' for i,v in loads.items()]
        if cfg['test']['self_weight'] and test:
            lines += ['*DLOAD',f"SOLIDS,GRAV,{cfg['test']['gravity']},0,0,-1"]
    lines += ['*NODE PRINT,NSET=ALL','U,RF','*NODE FILE','U']
    if not modal:
        lines += ['*EL PRINT,ELSET=SOLIDS,GLOBAL=YES','S','*EL FILE','S']
    lines += ['*END STEP']
    path.write_text('\n'.join(lines)+'\n',encoding='ascii')
    gravity_force = -mesh_mass*cfg['test']['gravity'] if test and cfg['test']['self_weight'] else 0.
    return {'loads':loads,'boundary':bcs,'mesh_mass_kg':mesh_mass,'gravity_force_N':gravity_force,'gravity_loads':gravity_loads}


def reaction_balance(data,metadata):
    fixed = {i for i,d in metadata['boundary'] if d==3}
    # ccx RF is total nodal force Ku. Subtract equivalent applied force on fixed DOFs.
    reaction = sum(data['forces'].get(i,[0,0,0])[2]-metadata['loads'].get(i,0)-metadata['gravity_loads'].get(i,0) for i in fixed)
    applied = sum(metadata['loads'].values())+metadata['gravity_force_N']
    return float(reaction),float(reaction+applied)


def execute(model,cfg,out,diagnostics):
    if cfg['geometry'].get('sandwich',{}).get('enabled'):
        from .sandwich_fem import execute_sandwich
        return execute_sandwich(model,cfg,out,diagnostics)
    missing = list(model['missing'])
    if not cfg['geometry']['web']['enabled']:
        missing.append('Tragfähiger, gekoppelter Steg fehlt für räumliches Modell')
    if min(cfg['test']['support_width_m'],cfg['test']['load_width_m']) <= 0:
        missing.append('Positive reale Auflagen- und Lastbreiten für FEM fehlen')
    if cfg['test']['central_inertia_kg_m2']:
        missing.append('Räumlicher Adapter unterstützt keine zusätzliche zentrale Rotationsträgheit')
    if cfg['flight']['root_rotation_stiffness_Nm'] is not None:
        missing.append('Räumlicher Adapter unterstützt nur feste Flugwurzel')
    if any(cfg['geometry'][k] for k in ['shell_EI_Nm2','shell_mass_kg_m','nonstructural_mass_kg_m']):
        missing.append('Zusätzliche Schale/Masse benötigt räumliche Zuordnung; kein pauschaler FEM-Ersatz')
    for name in ['freecad_python','calculix','gmsh']:
        if not diagnostics[name]['available']:
            missing.append(f'{name} fehlt; Pfad unter paths konfigurieren')
    if missing:
        return {'status':'nicht ausgeführt','reasons':missing,'variants':{}}
    levels = cfg['fem']['mesh_levels']
    if len(levels)<3 or any(b<=a for a,b in zip(levels[:-1],levels[1:])):
        raise ValueError('Mindestens drei streng steigende Netzfaktoren erforderlich')
    result = {'status':'ausgeführt','variants':{}}
    script = Path(__file__).with_name('freecad_geometry.py').resolve()
    for variant in ['A','B']:
        rows = []
        for level in levels:
            folder = out/'fem'/variant/f'level_{level}'
            folder.mkdir(parents=True,exist_ok=True)
            row = {'level':level}
            for case,full in [('flight',False),('test',True)]:
                work = folder/case
                work.mkdir(exist_ok=True)
                request = geometry_request(model,cfg,variant,work,full)
                dump_json(work/'geometry.json',request)
                run_command([cfg['paths']['freecad_python'],script,work.resolve()/'geometry.json'],work,work/'freecad.log',cfg['fem']['timeout_s'])
                h = cfg['fem']['base_length_m']*1000/level
                geo = f'SetFactory("OpenCASCADE");\nMerge "spar.step";\nBooleanFragments{{ Volume{{:}}; Delete; }}{{}}\nMesh.MeshSizeMax={h};\nMesh.MeshSizeMin={h/5};\nMesh.ElementOrder=2;\nMesh.MshFileVersion=2.2;\nMesh.SaveAll=1;\n'
                (work/'mesh.geo').write_text(geo,encoding='utf-8')
                run_command([cfg['paths']['gmsh'],'mesh.geo','-3','-format','msh2','-o','mesh.msh','-v','3'],work,work/'gmsh.log',cfg['fem']['timeout_s'])
                nodes,elements,faces = read_msh(work/'mesh.msh')
                dump_json(work/'mesh_si.json',{'nodes':{i:v.tolist() for i,v in nodes.items()},'elements':elements,'faces':faces})
                row[case+'_nodes'] = len(nodes)
                for job,modal,nonlinear in [('static',False,False),('modal',True,False)]+([('nonlinear',False,True)] if cfg['fem']['nonlinear'] else []):
                    metadata = write_input(work/f'{job}.inp',nodes,elements,faces,model,cfg,variant,case,modal,nonlinear)
                    log = run_command([cfg['paths']['calculix'],'-i',job],work,work/f'{job}.log',cfg['fem']['timeout_s'])
                    if '*ERROR' in log.upper():
                        raise RuntimeError(f'CalculiX meldet Fehler: {work/job}')
                    data = parse_dat(work/f'{job}.dat')
                    dump_json(work/f'{job}.parsed.json',data)
                    if modal:
                        if not data['frequencies']:
                            raise ValueError('Keine tatsächlichen Eigenfrequenzen im Solveroutput')
                        from .visualization import fem_picture
                        fractions = []
                        for mode_no,(frequency,shape) in enumerate(zip(data['frequencies'],data['mode_shapes']),1):
                            uv = np.array(list(shape.values()))
                            fractions.append(float(np.sum(uv[:,2]**2)/np.sum(uv**2)))
                            amplitude = max(np.linalg.norm(uv,axis=1))
                            factor = .05*model['half_span']/amplitude if amplitude else 1
                            fem_picture(work/f'mode_{mode_no}',nodes,faces,shape,f'{variant} {case}: {frequency:.5g} Hz, normierte Eigenform',scale=factor,mode=True)
                        if case=='test':
                            relevant = [j for j,v in enumerate(fractions) if v>=.6]
                            if not relevant:
                                raise ValueError('Keine dominante vertikale Biegemode in den angeforderten 3D-Eigenformen; modes erhöhen')
                            row['frequency_Hz'] = data['frequencies'][relevant[0]]
                            row['selected_mode'] = relevant[0]+1
                            row['vertical_fractions'] = fractions
                            row['frequencies_Hz'] = data['frequencies']
                    else:
                        if not data['displacements']:
                            raise ValueError('Keine Verschiebungen im Solveroutput')
                        target = model['half_span'] if case=='flight' else 0.
                        ids = sorted(nodes,key=lambda i:abs(nodes[i][0]-target))[:max(1,len(nodes)//100)]
                        disp = float(np.mean([data['displacements'][i][2] for i in ids]))
                        row[case+('_nonlinear_m' if nonlinear else '_tip_m' if case=='flight' else '_root_m')] = disp
                        reaction,residual = reaction_balance(data,metadata)
                        row[case+'_reaction_N'] = reaction
                        row[case+'_reaction_residual_N'] = residual
                        row[case+'_mesh_mass_kg'] = metadata['mesh_mass_kg']
                        from .visualization import fem_picture
                        fem_picture(work/job,nodes,faces,data['displacements'],f'{variant} {case} {job}: Verschiebung [m]')
                        if data.get('stresses'):
                            from .gallery import render_gallery
                            render_gallery(work,nodes,elements,faces,data,work/'geometry.json',
                                           f'{variant}: {case}, {job}',prefix=job+'_')
            rows.append(row)
        result['variants'][variant] = {'meshes':rows,'convergence':convergence(rows,cfg['fem']['convergence_relative'])}
        from .visualization import convergence_picture
        convergence_picture(out/'fem'/variant/'convergence',rows)
    return result
