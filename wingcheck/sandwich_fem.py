"""3D swept partition mesh (C3D20R by default) for sleeved Depron spars.

Within an interval all materials share nodes. At discrete ply drops nonmatching
interface nodes use displacement interpolation equations (no rigid spiders).
Mesh, material assignment and equations are exported and auditable.
"""
import math
import shutil
import re
from pathlib import Path
import numpy as np
from .sandwich import rectangles,breaks
from .excel import dump_json
from .postprocess import parse_dat,convergence


HEX_FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
HEX_EDGES = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]


def quad_weights(nodes,face,weight_fn=None):
    xyz=np.array([nodes[n] for n in face[:4]])
    gs,ws=np.polynomial.legendre.leggauss(3)
    result=np.zeros(len(face))
    signs=np.array([[-1,-1],[1,-1],[1,1],[-1,1]])
    for u,wu in zip(gs,ws):
        for v,wv in zip(gs,ws):
            N=(1+signs[:,0]*u)*(1+signs[:,1]*v)/4
            du=signs[:,0]*(1+signs[:,1]*v)/4;dv=signs[:,1]*(1+signs[:,0]*u)/4
            jac=abs(np.cross(xyz.T@du,xyz.T@dv)[2]) # projected area for vertical forces
            shape=[(1-u)*(1-v)*(-u-v-1)/4,(1+u)*(1-v)*(u-v-1)/4,
                   (1+u)*(1+v)*(u+v-1)/4,(1-u)*(1+v)*(-u+v-1)/4,
                   (1-u*u)*(1-v)/2,(1+u)*(1-v*v)/2,(1-u*u)*(1+v)/2,(1-u)*(1-v*v)/2] if len(face)==8 else N
            factor=1 if weight_fn is None else weight_fn(N@xyz)
            result+=np.asarray(shape)*jac*wu*wv*factor
    return result


def quadratic_mesh(data,interfaces):
    nodes=data['nodes']; ids={tuple(round(v*1e10) for v in xyz):n for n,xyz in nodes.items()}
    edges={}
    def middle(a,b):
        key=tuple(sorted([a,b]))
        if key not in edges:
            xyz=(nodes[a]+nodes[b])/2
            coord=tuple(round(v*1e10) for v in xyz)
            if coord not in ids:
                ids[coord]=len(nodes)+1;nodes[ids[coord]]=xyz
            edges[key]=ids[coord]
        return edges[key]
    def quad(q):return q+[middle(q[j],q[(j+1)%4]) for j in range(4)]
    data['elements']=[conn+[middle(conn[a],conn[b]) for a,b in HEX_EDGES] for conn in data['elements']]
    data['faces']=[quad(q) for q in data['faces']]
    equations=[]
    for previous,current,x in interfaces:
        # Always use the inboard (thicker/superset) section as master. Choosing
        # the thin section as master leaves the thin cap's inner edge untied on
        # the negative half-span and creates an unintended interface hinge.
        master_faces,slave_faces=(current,previous) if x<0 else (previous,current)
        masters=[quad(q) for q in master_faces]
        master_nodes={n for q in masters for n in q}
        slaves={n for q in slave_faces for n in quad(q)}-master_nodes
        boxes=[(q,np.array([nodes[n][1:] for n in q[:4]])) for q in masters]
        for slave in sorted(slaves):
            p=nodes[slave][1:]
            for q,xyz in boxes:
                low,high=xyz.min(axis=0),xyz.max(axis=0)
                if np.all(p>=low-1e-10) and np.all(p<=high+1e-10):
                    u,v=2*np.clip((p-low)/(high-low),0,1)-1
                    w=[(1-u)*(1-v)*(-u-v-1)/4,(1+u)*(1-v)*(u-v-1)/4,
                       (1+u)*(1+v)*(u+v-1)/4,(1-u)*(1+v)*(-u+v-1)/4,
                       (1-u*u)*(1-v)/2,(1+u)*(1-v*v)/2,
                       (1-u*u)*(1+v)/2,(1-u)*(1-v*v)/2]
                    equations.append((slave,[(n,float(a)) for n,a in zip(q,w) if abs(a)>1e-10]))
                    break
    data['equations']=equations
    data['element_type']='C3D20R'
    return data


def mesh(model,cfg,variant,full,level):
    L=model['half_span']
    support = model['parameters']['support_fraction']*L
    sw,lw=cfg['test']['support_width_m'],cfg['test']['load_width_m']
    positive = breaks(model,cfg)+[lw/2,support-sw/2,support,support+sw/2]
    if not full:positive=sorted(set(round(x,12) for x in positive+[p['x'] for p in model.get('planform',[])]))
    stations=sorted(set([-x for x in positive]+positive)) if full else sorted(set(positive))
    nodes,elements,groups,equations = {},[],{},[]
    ids={}
    def node(x,y,z):
        key=tuple(round(v*1e10) for v in [x,y,z])
        if key not in ids:
            ids[key]=len(nodes)+1
            nodes[ids[key]]=np.array([x,y,z])
        return ids[key]
    previous=[]
    interfaces=[]
    volume,mass=0.,0.
    for a,b in zip(stations[:-1],stations[1:]):
        mid=(a+b)/2
        rs=rectangles(model,cfg,mid,variant)
        ends=[{r['name']:r for r in rectangles(model,cfg,x,variant,sample_x=mid)} for x in [a,b]]
        def tracks(keys,span):
            candidates=sorted([(r[k],r['name'],k) for r in rs for k in keys])
            unique=[]
            for value,name,key in candidates:
                if unique and abs(value-unique[-1][0])<1e-12:
                    continue
                unique.append((value,name,key))
            coords=[[],[]]
            for j in range(len(unique)-1):
                va,na,ka=unique[j]
                vb,nb,kb=unique[j+1]
                count=max(1,math.ceil((vb-va)/(span/level)))
                for u in np.linspace(0,1,count+1)[:-1]:
                    for side in [0,1]:
                        coords[side].append(ends[side][na][ka]*(1-u)+ends[side][nb][kb]*u)
            _,name,key=unique[-1]
            for side in [0,1]:
                coords[side].append(ends[side][name][key])
            if any(np.any(np.diff(v)<-1e-11) for v in coords):
                raise ValueError(f'Querschnittslinien kreuzen sich im Intervall {a}..{b}')
            return np.array(coords)
        yy,zz=tracks(['y0','y1'],.025),tracks(['z0','z1'],.012)
        ny,nz=yy.shape[1],zz.shape[1]
        occupied=[]
        for j in range(ny-1):
            for k in range(nz-1):
                ym=np.mean(yy[:,j:j+2]); zm=np.mean(zz[:,k:k+2])
                match=[r for r in rs if r['y0']<ym<r['y1'] and r['z0']<zm<r['z1']]
                if len(match)>1:
                    raise ValueError('Überlappende Materialvolumen')
                if match:
                    occupied.append((j,k,match[0]['mat']))
        count=max(1,math.ceil((b-a)/(cfg['fem']['base_length_m']/level)))
        planes=[]
        new_start=set()
        first_plane=[]
        last_plane=[]
        for ix,u in enumerate(np.linspace(0,1,count+1)):
            yc,zc=yy[0]*(1-u)+yy[1]*u,zz[0]*(1-u)+zz[1]*u
            plane={}
            for j,k,_ in occupied:
                for jj,kk in [(j,k),(j+1,k),(j+1,k+1),(j,k+1)]:
                    if (jj,kk) not in plane:
                        old=len(nodes)
                        plane[jj,kk]=node(a+u*(b-a),yc[jj],zc[kk])
                        if ix==0 and len(nodes)>old:
                            new_start.add(plane[jj,kk])
            planes.append(plane)
            if ix==0 or ix==count:
                quads=[[plane[j,k],plane[j+1,k],plane[j+1,k+1],plane[j,k+1]] for j,k,_ in occupied]
                if ix==0:first_plane=quads
                else:last_plane=quads
        if previous:
            interfaces.append((previous,first_plane,a))
            boxes=[(q,np.array([nodes[n][1:] for n in q])) for q in previous]
            for slave in sorted(new_start):
                p=nodes[slave][1:]
                for quad,xyz in boxes:
                    low,high=xyz.min(axis=0),xyz.max(axis=0)
                    if np.all(p>=low-1e-10) and np.all(p<=high+1e-10):
                        # Axis-aligned section quads: exact bilinear interpolation.
                        u,v=np.clip((p-low)/(high-low),0,1)
                        weights=[(1-u)*(1-v),u*(1-v),u*v,(1-u)*v]
                        if slave not in quad:
                            equations.append((slave,[(n,float(w)) for n,w in zip(quad,weights) if w>1e-10]))
                        break
                # Nodes outside the preceding material section form free ply shoulders.
        previous=last_plane
        for p0,p1 in zip(planes[:-1],planes[1:]):
            for j,k,mat in occupied:
                conn=[p0[j,k],p0[j+1,k],p0[j+1,k+1],p0[j,k+1],p1[j,k],p1[j+1,k],p1[j+1,k+1],p1[j,k+1]]
                if len(set(conn))<8:
                    raise ValueError('Kollabiertes Netzelement')
                elements.append(conn)
                groups.setdefault(mat,[]).append(len(elements))
                xyz=np.array([nodes[n] for n in conn])
                # Swept straight sides: 2x2x2 Jacobian integration.
                vol=0.
                signs=np.array([[-1,-1,-1],[-1,1,-1],[-1,1,1],[-1,-1,1],[1,-1,-1],[1,1,-1],[1,1,1],[1,-1,1]])
                for g1 in [-1/np.sqrt(3),1/np.sqrt(3)]:
                    for g2 in [-1/np.sqrt(3),1/np.sqrt(3)]:
                        for g3 in [-1/np.sqrt(3),1/np.sqrt(3)]:
                            g=np.array([g1,g2,g3]); B=np.empty((8,3))
                            for d in range(3):
                                other=[j for j in range(3) if j!=d]
                                B[:,d]=signs[:,d]*np.prod(1+signs[:,other]*g[other],axis=1)/8
                            det=np.linalg.det(xyz.T@B)
                            if det<=0:raise ValueError('Nichtpositiver Element-Jacobian')
                            vol+=det
                volume+=vol
                density=cfg['geometry']['sandwich']['core_density'] if mat=='CORE' else model['material']['density']
                mass+=vol*density
    owners={}
    for eid,conn in enumerate(elements,1):
        for face in HEX_FACES:
            q=[conn[i] for i in face]
            key=tuple(sorted(q))
            if key in owners:owners[key]=None
            else:owners[key]=(q,eid)
    faces=[]
    for value in owners.values():
        if value is None:continue
        q,eid=value
        coords=np.array([nodes[i] for i in q])
        if np.ptp(coords[:,0])<1e-10 and not np.isclose(abs(coords[0,0]),L) and not (not full and abs(coords[0,0])<1e-10):
            continue
        faces.append(q)
    data=dict(nodes=nodes,elements=elements,groups=groups,equations=equations,faces=faces,mass=mass,volume=volume,element_type='C3D8I')
    if cfg['fem'].get('sandwich_element')=='C3D20R':return quadratic_mesh(data,interfaces)
    return data


def cad_request(model,cfg,variant,folder,full):
    stations=breaks(model,cfg)
    if full:stations=sorted(set([-x for x in stations]+stations))
    blocks=[]
    for a,b in zip(stations[:-1],stations[1:]):
        mid=(a+b)/2
        ea,eb=[{r['name']:r for r in rectangles(model,cfg,x,variant,sample_x=mid)} for x in [a,b]]
        for name in ea:
            ends=[]
            for x,rr in [(a,ea[name]),(b,eb[name])]:
                ends.append([x,rr['y1']-rr['y0'],rr['z0'],rr['z1'],(rr['y1']+rr['y0'])/2])
            blocks.append(dict(component=name,ends=ends))
    return dict(blocks=blocks,partitioned_only=True,fcstd=str((folder/'spar.FCStd').resolve()),
                step=str((folder/'spar.step').resolve()),version_file=str((folder/'freecad_version.json').resolve()))


def input_file(path,meshdata,model,cfg,case,modal=False,nonlinear=False):
    nodes,elements=meshdata['nodes'],meshdata['elements']
    test=case=='test'
    L=model['half_span']; p=model['parameters']; c=cfg['geometry']['sandwich']; m=model['material']
    lw,sw=cfg['test']['load_width_m'],cfg['test']['support_width_m']
    def top(x):
        return np.interp(abs(x),[s['x'] for s in model['stations']],[s['height'] for s in model['stations']])/2
    loads={}
    r0=model['stations'][0]['web_required']
    pocket0=c['rear_center_y_m']+c['core_width_m']/2+r0
    pocket1=pocket0+c['pocket_width_m']
    load_region=cfg['test'].get('load_region','pocket' if cfg['test'].get('load_across_pocket_only',False) else 'full_cap')
    if test and load_region not in ['rear_web','pocket','full_cap']:
        raise ValueError('Unbekannter Versuchslastbereich: '+load_region)
    for face in meshdata['faces']:
        xyz=np.array([nodes[n] for n in face]); xc=xyz[:,0].mean()
        if abs(xyz[:,2].mean()-top(xc))>1e-7 or (test and abs(xc)>lw/2+1e-10):continue
        if test:
            yc=xyz[:,1].mean()
            if load_region=='pocket' and not pocket0-1e-10<=yc<=pocket1+1e-10:continue
            if load_region=='rear_web':
                wall=np.interp(abs(xc),[s['x'] for s in model['stations']],[s['web_required'] for s in model['stations']])
                half_width=c['core_width_m']/2+wall
                if not c['rear_center_y_m']-half_width-1e-10<=yc<=c['rear_center_y_m']+half_width+1e-10:continue
        from .loads import chord
        relative=None if test else lambda p:(chord(model,p[0]) if cfg['flight']['distribution']=='chord_proportional' else 1.)/np.interp(abs(p[0]),[s['x'] for s in model['stations']],[s['width_top'] for s in model['stations']])
        nodal=quad_weights(nodes,face,relative)
        for n,weight in zip(face,nodal):loads[n]=loads.get(n,0)+weight
    force=cfg['test']['force_N'] if cfg['test']['force_N'] is not None else p['test_mass']*cfg['test']['gravity']
    F=-force if test else p['total_lift']/2
    if not test and cfg['flight']['load_kind']=='ultimate':F/=cfg['flight']['safety_factor']
    norm=sum(loads.values())
    if norm<=0:raise ValueError('Keine Lastflächen')
    weights=dict(loads)
    loads={n:F*w/norm for n,w in loads.items()}
    bc=set()
    if test:
        support_model=cfg['test'].get('fem_support_model','bottom_surface')
        if support_model not in ['averaged_roller','fixed_vertical_band','fixed_vertical_section','bottom_contact_line','bottom_surface']:
            raise ValueError('Unbekanntes FEM-Auflagermodell: '+support_model)
        supports=cfg['test']['supports_m'] or [-p['support_fraction']*L,p['support_fraction']*L]
        bands=[]
        support_half_width=0. if support_model in ['fixed_vertical_section','bottom_contact_line'] else sw/2
        for location in supports:
            band=[n for n,v in nodes.items() if abs(v[0]-location)<=support_half_width+1e-10 and
                  (support_model in ['fixed_vertical_band','fixed_vertical_section'] or abs(v[2]+top(v[0]))<1e-7)]
            if not band:raise ValueError('Keine Auflagenknoten')
            bands.append(band)
            bc.update((n,3) for n in band)
        left=min(bands[0],key=lambda n:abs(nodes[n][1]-.003))
        right=min(bands[1],key=lambda n:abs(nodes[n][1]-.003))
        bc.update([(left,1),(left,2),(right,2)])
    else:
        bc={(n,d) for n,v in nodes.items() if abs(v[0])<1e-10 for d in [1,2,3]}
    support_equations=[];references={};reaction_nodes=set()
    if test and cfg['test'].get('fem_support_model')=='averaged_roller':
        support_groups=[{}, {}, {}]
        for face in meshdata['faces']:
            xyz=np.array([nodes[n] for n in face]);xc=xyz[:,0].mean();yc=xyz[:,1].mean()
            if abs(xyz[:,2].mean()+top(xc))>1e-7:continue
            if abs(xc-supports[0])<=sw/2+1e-10:
                width=np.interp(abs(xc),[s['x'] for s in model['stations']],[s['width_top'] for s in model['stations']])
                group=0 if yc<width/2 else 1
            elif abs(xc-supports[1])<=sw/2+1e-10:group=2
            else:continue
            for n,w in zip(face,quad_weights(nodes,face)):
                support_groups[group][n]=support_groups[group].get(n,0)+w
        dependent={n for n,_ in meshdata['equations']}
        bc={(n,d) for n,d in bc if d!=3}
        for group in support_groups:
            norm_g=sum(group.values())
            if norm_g<=0:raise ValueError('Leere gemittelte Auflagenfläche')
            normalized={n:w/norm_g for n,w in group.items() if abs(w)>1e-15}
            candidates=[n for n in normalized if n not in dependent]
            if not candidates:raise ValueError('Kein unabhängiger Auflagenknoten für Mittelungsbedingung')
            dep=max(candidates,key=lambda n:abs(normalized[n]));dependent.add(dep)
            reference=max(nodes)+len(references)+1
            position=sum((nodes[n]*w for n,w in normalized.items()))
            references[reference]=position
            support_equations.append([(dep,3,normalized[dep])]+[(n,3,w) for n,w in normalized.items() if n!=dep]+[(reference,3,-1.)])
            bc.update((reference,d) for d in [1,2,3])
            reaction_nodes.update(normalized)
    lines=['*HEADING','Biest accepted sandwich assumptions; SI; 3D '+meshdata['element_type'],'*NODE,NSET=ALL']
    lines += [f'{n},'+','.join(f'{v:.13g}' for v in xyz) for n,xyz in nodes.items()]
    lines += [f'{n},'+','.join(f'{v:.13g}' for v in xyz) for n,xyz in references.items()]
    lines += ['*ELEMENT,TYPE='+meshdata['element_type']+',ELSET=SOLIDS']
    for e,conn in enumerate(elements,1):
        if len(conn)==20:
            lines += [f'{e},'+','.join(map(str,conn[:15]))+',',','.join(map(str,conn[15:]))]
        else:lines.append(f'{e},'+','.join(map(str,conn)))
    for slave,masters in meshdata['equations']:
        for d in [1,2,3]:
            if (slave,d) in bc:
                if not all((n,d) in bc for n,w in masters if abs(w)>1e-14):
                    raise ValueError('Fixierter Interfaceknoten hat freie Masterknoten')
                # Both traces are prescribed zero: this equation is redundant.
                continue
            terms=[(slave,d,1.)]+[(n,d,-w) for n,w in masters]
            lines+=['*EQUATION',str(len(terms))]
            for j in range(0,len(terms),3):
                lines.append(','.join(f'{n},{dd},{w:.13g}' for n,dd,w in terms[j:j+3]))
    for terms in support_equations:
        lines+=['*EQUATION',str(len(terms))]
        for j in range(0,len(terms),3):lines.append(','.join(f'{n},{d},{w:.13g}' for n,d,w in terms[j:j+3]))
    lines += ['*MATERIAL,NAME=UD','*ELASTIC,TYPE=ENGINEERING CONSTANTS',
              ','.join(str(m[k]) for k in ['E1','E2','E3','nu12','nu13','nu23','G12','G13']),str(m['G23']),
              '*DENSITY',str(m['density']), '*MATERIAL,NAME=FOAM','*ELASTIC',f"{c['core_E']},{c['core_nu']}",'*DENSITY',str(c['core_density'])]
    for group,ids in meshdata['groups'].items():
        lines += [f'*ELSET,ELSET={group}']+[','.join(map(str,ids[j:j+16])) for j in range(0,len(ids),16)]
        if group=='CORE':
            lines += ['*SOLID SECTION,ELSET=CORE,MATERIAL=FOAM']
            continue
        theta=0 if group=='CAP' else math.radians(c['sleeve_angles_deg'][int(group[1])])
        co,si=math.cos(theta),math.sin(theta)
        a,bv=([co,si,0],[-si,co,0]) if not group.startswith('V') else ([co,0,si],[-si,0,co])
        lines += [f'*ORIENTATION,NAME=O{group}',','.join(map(str,a+bv)),f'*SOLID SECTION,ELSET={group},MATERIAL=UD,ORIENTATION=O{group}']
    if test:
        positive={n:w for n,w in weights.items() if w>0};mass_norm=sum(positive.values())
        for j,(n,w) in enumerate(positive.items(),len(elements)+1):
            lines += [f'*ELEMENT,TYPE=MASS,ELSET=M{j}',f'{j},{n}',f'*MASS,ELSET=M{j}',str(p['modal_mass']*w/mass_norm)]
    lines += ['*BOUNDARY']+[f'{n},{d},{d}' for n,d in sorted(bc)]
    lines += ['*STEP'+(',NLGEOM,INC=300' if nonlinear else '')]
    if modal:lines+=['*FREQUENCY',str(cfg['analysis']['modes'])]
    else:
        lines+=['*STATIC']+([f"{cfg['fem'].get('nonlinear_initial_increment',.0001)},1,1e-8,0.05"] if nonlinear else [])+['*CLOAD']+[f'{n},3,{v:.13g}' for n,v in loads.items()]
    frequency=',FREQUENCY=999999' if nonlinear else ''
    lines+=['*NODE PRINT,NSET=ALL'+frequency,'U,RF','*NODE FILE'+frequency,'U']
    if not modal:lines+=['*EL PRINT,ELSET=SOLIDS,GLOBAL=YES'+frequency,'S','*EL FILE'+frequency,'S']
    lines+=['*END STEP']
    path.write_text('\n'.join(lines)+'\n',encoding='ascii')
    # With interpolation MPCs a roller force can be transferred to interface
    # masters outside its footprint. Sum the complete physical-node residual;
    # internal interface forces cancel (including their first moments).
    reaction_boundary=[(n,3) for n in nodes] if test else sorted(bc)
    return dict(loads=loads,boundary=reaction_boundary,gravity_loads={},gravity_force_N=0.)


def execute_sandwich(model,cfg,out,diagnostics):
    from .fem import run_command,reaction_balance
    from .gallery import render_gallery
    if model['missing']:return dict(status='nicht ausgeführt',reasons=model['missing'],variants={})
    for name in ['freecad_python','calculix']:
        if not diagnostics[name]['available']:raise ValueError(name+' fehlt')
    if cfg['test']['self_weight']:raise ValueError('Schlauchadapter: Eigengewicht noch nicht aktiviert; keine stille Auslassung')
    if cfg['flight']['mass_relief'] or cfg['flight']['distribution'] not in ['uniform','chord_proportional']:raise ValueError('Schlauchadapter: nur Gleichlast/tiefenproportionale Last ohne Massenentlastung')
    levels=cfg['fem']['mesh_levels']
    result=dict(status='ausgeführt',variants={},method='Explizite Depronkerne und CFK-Schläuche, strukturierte '+cfg['fem'].get('sandwich_element','C3D8I')+'-Volumen; FreeCAD-CAD, eigener reproduzierbarer Netzgenerator (kein Gmsh-Tetraedernetz).')
    root=out/('fem_sandwich_q20' if cfg['fem'].get('sandwich_element')=='C3D20R' else 'fem_sandwich'); root.mkdir(parents=True,exist_ok=True)
    script=Path(__file__).with_name('freecad_geometry.py').resolve()
    def checkpoint():dump_json(out/'fem_progress.json',result)
    checkpoint()
    for variant in ['A','B']:
        rows=[]; result['variants'][variant]=dict(meshes=rows,convergence=dict(converged=False,reason='Lauf noch nicht vollständig'))
        for level in levels:
            row=dict(level=level)
            rows.append(row)
            for case,full in [('flight',False),('test',True)]:
                folder=root/variant/f'level_{level}'/case; folder.mkdir(parents=True,exist_ok=True)
                print(f'FEM {variant} Netz {level} {case}: Geometrie/Netz',flush=True)
                request=cad_request(model,cfg,variant,folder,full)
                request_path=folder/'geometry.json'
                same_cad=request_path.exists() and __import__('json').loads(request_path.read_text(encoding='utf-8'))==request and (folder/'spar.FCStd').exists() and (folder/'spar.step').exists()
                dump_json(request_path,request)
                if level==levels[0]:
                    if not same_cad:run_command([cfg['paths']['freecad_python'],script,(folder/'geometry.json').resolve()],folder,folder/'freecad.log',cfg['fem']['timeout_s'])
                else:
                    src=root/variant/f'level_{levels[0]}'/case
                    for file in ['spar.FCStd','spar.step','freecad_version.json']:shutil.copy2(src/file,folder/file)
                meshdata=mesh(model,cfg,variant,full,level)
                dump_json(folder/'mesh_si.json',dict(nodes={n:v.tolist() for n,v in meshdata['nodes'].items()},elements=meshdata['elements'],faces=meshdata['faces'],groups=meshdata['groups'],equations=meshdata['equations'],mass_kg=meshdata['mass']))
                row[case+'_nodes']=len(meshdata['nodes']); row[case+'_elements']=len(meshdata['elements']);row[case+'_mesh_mass_kg']=meshdata['mass']
                # Legacy VTK uses the same standard corner/edge order as C3D20R.
                vtk=['# vtk DataFile Version 3.0','Biest SI mesh','ASCII','DATASET UNSTRUCTURED_GRID',f'POINTS {len(meshdata["nodes"])} double']
                vtk += [' '.join(map(str,xyz)) for xyz in meshdata['nodes'].values()]
                vtk += [f'CELLS {len(meshdata["elements"])} {sum(len(c)+1 for c in meshdata["elements"])}']
                vtk += [str(len(c))+' '+' '.join(str(n-1) for n in c) for c in meshdata['elements']]
                vtk += [f'CELL_TYPES {len(meshdata["elements"])}']+[str(25 if len(c)==20 else 12) for c in meshdata['elements']]
                (folder/'mesh_si.vtk').write_text('\n'.join(vtk)+'\n',encoding='ascii')
                jobs=[('static',False,False)]+([('modal',True,False)] if full else [])
                for job,modal,nonlinear in jobs:
                    print(f'FEM {variant} Netz {level} {case}: {job}, {len(meshdata["nodes"])} Knoten',flush=True)
                    input_path=folder/f'{job}.inp'
                    old_input=input_path.read_text(encoding='ascii') if input_path.exists() else None
                    meta=input_file(input_path,meshdata,model,cfg,case,modal,nonlinear)
                    try:
                        log_path=folder/f'{job}.log'
                        old_log=log_path.read_text(errors='replace') if log_path.exists() else ''
                        version=re.search(r'Version\s+(\S+)',diagnostics['calculix']['version'])
                        same_version=version and ('CalculiX Version '+version.group(1)) in old_log
                        reused=old_input==input_path.read_text(encoding='ascii') and (folder/f'{job}.dat').exists() and 'Job finished' in old_log and '*ERROR' not in old_log.upper() and same_version
                        if reused:
                            log=old_log
                            print('  identischer Solverinput / gleiche CalculiX-Version: Ergebnis wiederverwendet',flush=True)
                        else:log=run_command([cfg['paths']['calculix'],'-i',job],folder,log_path,cfg['fem']['timeout_s'])
                        if '*ERROR' in log.upper():raise ValueError('CalculiX-Fehler: '+str(folder/job))
                        data=parse_dat(folder/f'{job}.dat')
                        if modal:
                            if not data['frequencies']:raise ValueError('Keine Solver-Eigenwerte')
                            fractions=[]
                            for shape in data['mode_shapes']:
                                u=np.array(list(shape.values()));fractions.append(float(np.sum(u[:,2]**2)/np.sum(u**2)))
                            relevant=[j for j,v in enumerate(fractions) if v>=.5]
                            selected=relevant[0] if relevant else 0
                            row.update(frequency_Hz=data['frequencies'][selected],frequencies_Hz=data['frequencies'],selected_mode=selected+1,vertical_fractions=fractions)
                            mirror={tuple(round(v*1e10) for v in xyz):n for n,xyz in meshdata['nodes'].items()}
                            pairs=[(n,mirror.get(tuple(round(v*1e10) for v in [-xyz[0],xyz[1],xyz[2]]))) for n,xyz in meshdata['nodes'].items()]
                            pairs=[(a,b) for a,b in pairs if b is not None]
                            classes=[]
                            for shape in data['mode_shapes']:
                                ua=np.array([shape[a][2] for a,b in pairs]);ub=np.array([shape[b][2] for a,b in pairs])
                                norm=max(np.linalg.norm(ua),1e-30)
                                classes.append('quasi-symmetrisch' if np.linalg.norm(ua-ub)/norm<.1 else 'quasi-antisymmetrisch' if np.linalg.norm(ua+ub)/norm<.1 else 'gemischt')
                            row['mode_symmetry']=classes
                            if level==levels[-1]:
                                from .visualization import fem_picture
                                for j,(f,shape) in enumerate(zip(data['frequencies'],data['mode_shapes']),1):
                                    amp=max(np.linalg.norm(u) for u in shape.values());fac=.03*model['half_span']/amp
                                    # Triangulate quads for the existing mode renderer.
                                    faces=[t for q in meshdata['faces'] for t in [[q[0],q[1],q[2]],[q[0],q[2],q[3]]]]
                                    fem_picture(folder/f'mode_{j}',meshdata['nodes'],faces,shape,f'{variant} Versuch: {f:.4g} Hz',fac,mode=True)
                        else:
                            if not data['displacements']:raise ValueError('Keine Solververschiebungen')
                            target=0 if full else model['half_span']
                            distances={n:abs(v[0]-target) for n,v in meshdata['nodes'].items()};closest=min(distances.values())
                            ids=[n for n,d in distances.items() if d<=closest+1e-10]
                            if full:
                                for side,xpos in [('left',-model['half_span']),('right',model['half_span'])]:
                                    tipids=[n for n,v in meshdata['nodes'].items() if abs(v[0]-xpos)<1e-9 and v[2]>0]
                                    row['test_'+side+'_tip_m']=float(np.mean([data['displacements'][n][2] for n in tipids]))
                                h=model['stations'][0]['height']/2
                                topnodes=sorted([n for n in ids if abs(meshdata['nodes'][n][2]-h)<1e-9],key=lambda n:meshdata['nodes'][n][1])
                                yy=np.array([meshdata['nodes'][n][1] for n in topnodes]); ww=np.array([data['displacements'][n][2] for n in topnodes])
                                c=cfg['geometry']['sandwich'];r0=model['stations'][0]['web_required']
                                low=c['rear_center_y_m']+c['core_width_m']/2+r0; high=low+c['pocket_width_m']
                                sample=sorted(set([low,high]+[y for y in yy if low<y<high]))
                                disp=float(np.trapezoid(np.interp(sample,yy,ww),sample)/(high-low))
                            else:
                                topids=[n for n in ids if meshdata['nodes'][n][2]>0]
                                bottomids=[n for n in ids if meshdata['nodes'][n][2]<0]
                                disp=float(np.mean([data['displacements'][n][2] for n in topids]))
                                row['flight'+('_nonlinear' if nonlinear else '')+'_bottom_tip_m']=float(np.mean([data['displacements'][n][2] for n in bottomids]))
                            key=case+('_nonlinear_m' if nonlinear else '_root_m' if full else '_tip_m')
                            row[key]=disp
                            reaction,residual=reaction_balance(data,meta)
                            row[case+'_reaction_N']=reaction;row[case+'_reaction_residual_N']=residual
                            if level==levels[-1] or level==levels[0]:
                                render_gallery(folder,meshdata['nodes'],meshdata['elements'],meshdata['faces'],data,folder/'geometry.json',f'Biest {variant}, {case}, {job}: bestätigte Annahmen',prefix=job+'_')
                        # Retain full solver DAT/FRD; lightweight parsed summary avoids huge duplicated JSON.
                        dump_json(folder/f'{job}.summary.json',dict(frequencies=data['frequencies'],displacement_nodes=len(data['displacements']),stress_elements=len(data['stresses'])))
                    except Exception as exc:
                        row.setdefault('errors',[]).append(job+': '+str(exc));checkpoint()
                        if job in ['static','modal']:raise
                    checkpoint()
            if all(k in row for k in ['flight_tip_m','test_root_m','frequency_Hz']):
                result['variants'][variant]['convergence']=convergence(rows,cfg['fem']['convergence_relative'])
                checkpoint()
        from .visualization import convergence_picture
        convergence_picture(root/variant/'convergence',rows)
    checkpoint()
    if cfg['fem']['nonlinear']:
        import json
        target=cfg['fem'].get('nonlinear_mesh_level',levels[0])
        for variant in ['A','B']:
            row=next(r for r in result['variants'][variant]['meshes'] if r['level']==target)
            folder=root/variant/f'level_{target}'/'flight'
            raw=json.loads((folder/'mesh_si.json').read_text(encoding='utf-8'))
            raw['nodes']={int(k):np.array(v) for k,v in raw['nodes'].items()}
            raw['element_type']='C3D20R' if len(raw['elements'][0])==20 else 'C3D8I'
            print(f'FEM {variant} Netz {target}: zusätzlicher nichtlinearer Flugvergleich',flush=True)
            try:
                meta=input_file(folder/'nonlinear.inp',raw,model,cfg,'flight',nonlinear=True)
                log=run_command([cfg['paths']['calculix'],'-i','nonlinear'],folder,folder/'nonlinear.log',cfg['fem'].get('nonlinear_timeout_s',600))
                if '*ERROR' in log.upper() or 'Job finished' not in log:raise ValueError('Nichtlinearer Solverlauf nicht erfolgreich abgeschlossen')
                data=parse_dat(folder/'nonlinear.dat')
                if not data['displacements']:raise ValueError('Keine nichtlinearen Volllastverschiebungen')
                ids=[n for n,v in raw['nodes'].items() if abs(v[0]-model['half_span'])<1e-9]
                row['flight_nonlinear_m']=float(np.mean([data['displacements'][n][2] for n in ids if raw['nodes'][n][2]>0]))
                row['flight_nonlinear_bottom_tip_m']=float(np.mean([data['displacements'][n][2] for n in ids if raw['nodes'][n][2]<0]))
                reaction,residual=reaction_balance(data,meta)
                row['flight_nonlinear_reaction_residual_N']=residual
                row['flight_nonlinear_qualitative_only']=True
                render_gallery(folder,raw['nodes'],raw['elements'],raw['faces'],data,folder/'geometry.json',f'Biest {variant}: nichtlinear, Netz {target}, qualitativer Vergleich',prefix='nonlinear_')
            except Exception as exc:
                row.setdefault('errors',[]).append('Nichtlinearer Vergleich: '+str(exc))
            checkpoint()
    return result
