"""Reproducible 3D CAD/mesh/displacement/stress images from real solver files.

python -m wingcheck.gallery --source benchmark_results/fem/A/level_3/flight \
    --output results/fem_reference/flight --solver ".../ccx.exe" --label "Synthetischer Prüffall: Flug"
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection,Line3DCollection
from .visualization import save
from .postprocess import parse_dat
from .excel import dump_json


def exterior_faces(elements,faces):
    """Keep only true external faces, excluding shared cap/web interfaces."""
    owners = {}
    for eid,conn in enumerate(elements,1):
        indices = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)] if len(conn) in [8,20] else [(0,1,2),(0,1,3),(0,2,3),(1,2,3)]
        for idx in indices:
            key = tuple(sorted(conn[j] for j in idx))
            owners.setdefault(key,[]).append(eid)
    external = []
    seen = set()
    for face in faces:
        key = tuple(sorted(face[:4] if len(face) in [4,8] else face[:3]))
        if len(owners.get(key,[]))==1 and key not in seen:
            seen.add(key)
            external.append((face,owners[key][0]))
    if not external:
        raise ValueError('Keine echten Außenflächen für FEM-Bilder gefunden')
    return external


def triangles(face):
    if len(face)==8:
        a,b,c,d,ab,bc,cd,da=face
        return [(a,ab,da),(ab,b,bc),(bc,c,cd),(cd,d,da),(ab,bc,da),(bc,cd,da)]
    if len(face)==4:
        return [(face[0],face[1],face[2]),(face[0],face[2],face[3])]
    if len(face)==6:
        a,b,c,ab,bc,ca = face
        return [(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]
    return [face[:3]]


def view(polygons,path,title,values=None,color_label=None,wire=False,reference=None,signed=False,face_colors=None):
    fig = plt.figure(figsize=(11,5.5))
    ax = fig.add_subplot(111,projection='3d')
    kwargs = dict(linewidths=.22 if wire else 0,edgecolors='#34495e' if wire else 'none',alpha=1)
    collection = Poly3DCollection(polygons,**kwargs)
    if values is None:
        collection.set_facecolor(face_colors if face_colors is not None else '#76afd0')
    else:
        values = np.asarray(values)
        limit = max(abs(values)) or 1.
        norm = Normalize(-limit,limit) if signed else Normalize(float(min(values)),float(max(values)) or 1.)
        cmap = plt.get_cmap('coolwarm' if signed else 'viridis')
        collection.set_facecolor(cmap(norm(values)))
        fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=ax,shrink=.7,pad=.08,label=color_label)
    ax.add_collection3d(collection)
    if reference is not None:
        outlines = [np.vstack([polygon,polygon[0]]) for polygon in reference]
        ax.add_collection3d(Line3DCollection(outlines,colors='#555555',linewidths=.18,alpha=.3))
    xyz = np.concatenate(polygons if reference is None else polygons+reference)
    low,high = xyz.min(axis=0),xyz.max(axis=0)
    span = np.maximum(high-low,1e-6)
    pad = span*.05
    ax.set(xlim=(low[0]-pad[0],high[0]+pad[0]),ylim=(low[1]-pad[1],high[1]+pad[1]),
           zlim=(low[2]-pad[2],high[2]+pad[2]),xlabel='x [mm]',ylabel='y [mm]',zlabel='z [mm]')
    ax.set_box_aspect(span,zoom=1.1)
    ax.xaxis.set_major_locator(MaxNLocator(5))
    ax.yaxis.set_major_locator(MaxNLocator(2))
    ax.zaxis.set_major_locator(MaxNLocator(3))
    ax.tick_params(labelsize=8,pad=1)
    ax.xaxis.labelpad = 12
    ax.yaxis.labelpad = 8
    ax.zaxis.labelpad = 8
    ax.grid(False)
    ax.view_init(elev=23,azim=-65)
    fig.suptitle(title,fontsize=10,y=.98)
    save(fig,path)


def render_gallery(out,nodes,elements,faces,data,geometry_path,label,prefix=''):
    out = Path(out)
    out.mkdir(parents=True,exist_ok=True)
    external = exterior_faces(elements,faces)
    geometry = json.loads(Path(geometry_path).read_text(encoding='utf-8'))
    model_polygons,model_colors = [],[]
    for block in geometry['blocks']:
        corners = []
        for end in block['ends']:
            x,b,z0,z1 = end[:4]
            yc = end[4] if len(end)>4 else 0.
            corners += [[x,yc-b/2,z0],[x,yc+b/2,z0],[x,yc+b/2,z1],[x,yc-b/2,z1]]
        corners = np.array(corners)*1000
        for idx in [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            model_polygons.append(corners[list(idx)])
            component=block['component']
            model_colors.append('#f0dca2' if component.endswith('core') else '#41647e' if component in ['top','bottom'] else '#444b50')
    view(model_polygons,out/(prefix+'model'),label+'\nParametrische CAD-Geometrie (Quelle: geometry.json / STEP)',face_colors=model_colors)
    surface = [(tri,eid) for face,eid in external for tri in triangles(face)]
    mesh = [np.array([nodes[i] for i in tri])*1000 for tri,_ in surface]
    view(mesh,out/(prefix+'mesh'),label+f'\n{len(nodes)} Knoten, {len(elements)} Volumenelemente',wire=True)
    u = data['displacements']
    if not u or not data.get('stresses'):
        raise ValueError('Echte Solververschiebungen und Integrationspunktspannungen erforderlich')
    missing = {i for tri,_ in surface for i in tri if i not in u}
    if missing:
        raise ValueError('Fehlende Solververschiebungen für Oberflächenknoten')
    umax = max(np.linalg.norm(v) for v in u.values())
    length = np.ptp(np.array(list(nodes.values()))[:,0])
    factor = .05*length/umax if umax else 1.
    deformed = [np.array([nodes[i]+factor*np.asarray(u[i]) for i in tri])*1000 for tri,_ in surface]
    magnitude = [np.mean([np.linalg.norm(u[i])*1000 for i in tri]) for tri,_ in surface]
    view(deformed,out/(prefix+'deformation'),label+f'\nVerformung ×{factor:.4g}; grau: unverformtes Netz',
         values=magnitude,color_label='|u| [mm] (reale Verschiebung)',reference=mesh)
    stress = {int(e):np.mean(v,axis=0) for e,v in data['stresses'].items()}
    if any(eid not in stress for _,eid in surface):
        raise ValueError('Fehlende Elementspannungen auf der Außenfläche')
    values = [stress[eid][0]/1e6 for _,eid in surface]
    view(mesh,out/(prefix+'stress_xx'),label+'\nLängsspannung σxx; Mittelwert je Element, unverformt',
         values=values,color_label='σxx [MPa]; + Zug / − Druck',signed=True)
    # Root details keep the thin sleeve/core layout legible for metre-long spars.
    if length>.5:
        limit=.2000001*1000
        mm=[i for i,p in enumerate(model_polygons) if np.min(p[:,0])>=-1e-6 and np.max(p[:,0])<=limit]
        mi=[i for i,p in enumerate(mesh) if np.min(p[:,0])>=-1e-6 and np.max(p[:,0])<=limit]
        if mm and mi:
            view([model_polygons[i] for i in mm],out/(prefix+'detail_model'),label+'\nWurzeldetail: Gurte blau, CFK-Schlauch grau, Depron beige',face_colors=[model_colors[i] for i in mm])
            view([mesh[i] for i in mi],out/(prefix+'detail_mesh'),label+'\nWurzeldetail: tatsächliches Volumennetz',wire=True)
            view([deformed[i] for i in mi],out/(prefix+'detail_deformation'),label+f'\nWurzeldetail, Verformung ×{factor:.4g}',values=[magnitude[i] for i in mi],color_label='|u| [mm]',reference=[mesh[i] for i in mi])
            view([mesh[i] for i in mi],out/(prefix+'detail_stress_xx'),label+'\nWurzeldetail: Längsspannung σxx',values=[values[i] for i in mi],color_label='σxx [MPa]',signed=True)
    return {'label':label,'images':[{'caption':caption,'file':prefix+name+'.png'} for name,caption in
            [('model','Parametrisches räumliches Modell'),('mesh','Quadratisches Volumennetz'),
             ('deformation','Verformung aus CalculiX'),('stress_xx','Längsspannung σxx aus CalculiX')]],
            'nodes':len(nodes),'elements':len(elements),'deformation_scale':factor,
            'max_displacement_m':float(umax),
            'max_abs_sigma_xx_integration_point_Pa':float(max(abs(v[0]) for points in data['stresses'].values() for v in points)),
            'stress_policy':'Globale Cauchy-Spannung; Darstellung mittelt Integrationspunkte nur innerhalb desselben Elements. Kein CFK-Versagenskriterium.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--solver',required=True)
    parser.add_argument('--label',required=True)
    parser.add_argument('--reuse-results',action='store_true',help='Vorhandene Solverdaten nur bei identischem Input erneut rendern')
    args = parser.parse_args()
    from .fem import read_msh,run_command
    source,out = Path(args.source).resolve(),Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=True)
    original = (source/'static.inp').read_text(encoding='ascii')
    if original.upper().count('*END STEP')!=1:
        raise ValueError('Galerie-Nachrechnung unterstützt genau einen statischen Schritt')
    additions = '*EL PRINT,ELSET=SOLIDS,GLOBAL=YES\nS\n*EL FILE\nS\n'
    content = original if '*EL PRINT' in original.upper() else original.replace('*END STEP',additions+'*END STEP')
    inp = out/'gallery_static.inp'
    if args.reuse_results:
        if not inp.exists() or inp.read_text(encoding='ascii')!=content or not (out/'gallery_static.dat').exists():
            raise ValueError('Wiederverwendung erfordert vorhandene Solverdatei und exakt identischen Input')
    else:
        inp.write_text(content,encoding='ascii')
        run_command([args.solver,'-i','gallery_static'],out,out/'gallery_static.log')
    data = parse_dat(out/'gallery_static.dat')
    dump_json(out/'gallery_static.parsed.json',data)
    nodes,elements,faces = read_msh(source/'mesh.msh')
    manifest = render_gallery(out,nodes,elements,faces,data,source/'geometry.json',args.label)
    manifest.update(source_directory=str(source),solver_input_sha256=hashlib.sha256(content.encode('ascii')).hexdigest(),
                    solver_dat_sha256=hashlib.sha256((out/'gallery_static.dat').read_bytes()).hexdigest(),
                    scope='synthetic_benchmark',solver_dat='gallery_static.dat')
    dump_json(out/'gallery.json',manifest)
    print(f'FEM-Galerie: {out}')


if __name__=='__main__':
    main()
