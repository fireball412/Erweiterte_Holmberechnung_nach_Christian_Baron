"""Headless Matplotlib figures; only actual solver data produce FEM images."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection

plt.rcParams.update({'axes.grid':True,'figure.dpi':130,'font.size':10})


def save(fig,path):
    fig.tight_layout()
    fig.savefig(str(path)+'.png')
    fig.savefig(str(path)+'.svg')
    plt.close(fig)


def fem_bending_line(folder):
    """Actual cross-section nodal mean and range, without displacement scaling."""
    import json
    from .postprocess import parse_dat
    mesh=json.loads((folder/'mesh_si.json').read_text(encoding='utf-8'))
    displacement=parse_dat(folder/'static.dat')['displacements']
    sections={}
    for key,point in mesh['nodes'].items():
        node=int(key)
        if node in displacement:
            sections.setdefault(round(point[0],10),[]).append(displacement[node][2]*1000)
    x=np.array(sorted(sections))
    return x, np.array([np.mean(sections[t]) for t in x]), np.array([min(sections[t]) for t in x]), np.array([max(sections[t]) for t in x])


def plots(model,cfg,result,out,fem=None):
    folder = out/'images'
    folder.mkdir(exist_ok=True)
    files = []
    s = model['stations']
    xx = [p['x'] for p in s]
    fig,axs = plt.subplots(2,1,figsize=(10,6))
    axs[0].plot(xx,[p['height']*1000 for p in s],label='Holm-Außenhöhe unter Schale')
    axs[0].plot(xx,[p['width_top']*1000 for p in s],label='Gurtbreite')
    axs[0].set(ylabel='mm',title='Geometrie nach Excel und YAML-Vorgaben; diskreter Lagenplan')
    axs[0].legend()
    axs[1].step(xx,[p['plies_top'] for p in s],where='post',label='A: Excel-Auslegung (Fertigung unbestätigt)' if not cfg['geometry']['manufacturing_plan_confirmed'] else 'A: diskreter Plan')
    axs[1].plot([xx[0],xx[-1]],[s[0]['plies_top']]*2,label='B: Wurzellagen durchgehend')
    if any(p['plies_bottom']!=p['plies_top'] for p in s):
        axs[1].step(xx,[p['plies_bottom'] for p in s],where='post',linestyle='--',label='A unten')
        axs[1].plot([xx[0],xx[-1]],[s[0]['plies_bottom']]*2,'--',label='B unten')
    axs[1].set(xlabel='x ab Wurzel [m]',ylabel='UD-Lagen je Gurt')
    axs[1].legend(fontsize=8)
    save(fig,folder/'geometry_plies')
    files.append('geometry_plies')
    fig,axs = plt.subplots(2,1,figsize=(10,5))
    L = model['half_span']
    a = model['parameters']['support_fraction']*L
    supports = cfg['test']['supports_m'] or [-a,a]
    axs[0].plot([0,L],[0,0],lw=4)
    axs[0].plot([0,0],[-.15,.15],lw=6,color='gray')
    for x in np.linspace(.1*L,L,9):
        scale=1.
        if cfg['flight']['distribution']=='chord_proportional':
            from .loads import chord
            scale=chord(model,x)/chord(model,0)
        axs[0].annotate('',(x,.02+.10*scale),(x,.02),arrowprops={'arrowstyle':'->'})
    axs[0].set(title='Flug: Halbflügel, Wurzel eingespannt; q positiv aufwärts in Rechnung',xlim=(-.1*L,1.1*L))
    axs[1].plot([-L,L],[0,0],lw=4)
    fixed=cfg['test'].get('fem_support_model')=='fixed_vertical_band'
    section_support=cfg['test'].get('fem_support_model')=='fixed_vertical_section'
    contact_line=cfg['test'].get('fem_support_model')=='bottom_contact_line'
    axs[1].scatter(supports,[0,0],marker='^',s=150,label='FEM: untere Kontaktlinie uz=0, Biegeneigung frei' if contact_line else 'FEM: Querschnitt uz=0, Biegeneigung frei' if section_support else 'FEM: Auflagerbänder, alle Knoten uz=0' if fixed else 'gelenkige vertikale Auflagen')
    if fixed:
        for p in supports:
            axs[1].axvspan(p-cfg['test']['support_width_m']/2,p+cfg['test']['support_width_m']/2,color='gray',alpha=.4)
        axs[1].legend(fontsize=8,loc='lower right')
    if section_support or contact_line:
        axs[1].legend(fontsize=8,loc='lower right')
    axs[1].annotate('F = m·g, bewegliche Wurzel',(0,0),(0,.14),ha='center',arrowprops={'arrowstyle':'->'})
    for p in supports:
        axs[1].text(p,-.08,f'x={p:.3f} m',ha='center')
    axs[1].set(title=f'Versuch: Vollflügel, Überhänge; p={a/L:.0%} der HALBSPANNWEITE',xlabel='x [m]',xlim=(-1.1*L,1.1*L))
    for ax in axs:
        ax.set_ylim(-.2,.25)
        ax.set_yticks([])
    save(fig,folder/'supports')
    files.append('supports')
    if not result['variants']:
        return files
    fig,axs = plt.subplots(2,2,figsize=(11,7))
    fig2,bs = plt.subplots(2,2,figsize=(11,7))
    fig3,cs = plt.subplots(2,1,figsize=(10,6))
    for variant,r in result['variants'].items():
        x = r['flight']['x']
        axs[0,0].plot(x,[s['EI'] for s in r['sections']],label=variant)
        axs[0,1].plot(x,[s['mu'] for s in r['sections']],label=variant)
        color={'A':'tab:blue','B':'tab:orange'}.get(variant)
        axs[1,0].plot(r['flight_beam_x'],r['flight_beam_w']*1000,color=color,label=variant+' numerischer Balken')
        axs[1,0].plot(x,r['flight']['w']*1000,'--',color=color,label=variant+' Integration')
        axs[1,1].plot(r['test_x'],r['test_w']*1000,color=color,label=variant+' numerischer Balken')
        record=(fem or {}).get('variants',{}).get(variant,{})
        rows=record.get('meshes',[])
        if rows and (out/'fem_sandwich_q20').exists():
            level=rows[-1]['level']
            for ax,case in [(axs[1,0],'flight'),(axs[1,1],'test')]:
                fem_folder=out/'fem_sandwich_q20'/variant/f'level_{level}'/case
                if not (fem_folder/'static.dat').exists():
                    continue
                fx,mean,lower,upper=fem_bending_line(fem_folder)
                ax.plot(fx,mean,':',color=color,lw=2,label=f'{variant} 3D-FEM linear, Netz {level}')
                ax.fill_between(fx,lower,upper,color=color,alpha=.12)
            result['fem_bending_overlay']=True
            result['fem_bending_converged']=all(v.get('convergence',{}).get('converged',False) for v in fem['variants'].values())
        for ax,k,title in zip(bs.flat,['q','V','M','curvature'],['q [N/m]','V [N]','M [Nm]','κ [1/m]']):
            ax.plot(x,r['flight'][k],color=color,label=variant+' Balken (M/EI)' if k=='curvature' else variant)
            ax.set(xlabel='x [m]',ylabel=title)
        if rows and cfg['geometry'].get('sandwich',{}).get('enabled'):
            fem_folder=out/'fem_sandwich_q20'/variant/f"level_{rows[-1]['level']}"/'flight'
            if (fem_folder/'static.dat').exists():
                from .curvature import flight_rear_curvature
                cx,ck=flight_rear_curvature(fem_folder,model,cfg,out/f'flight_rear_curvature_{variant}.csv')
                bs[1,1].plot(cx,ck,'--',color=color,label=variant+' FEM: hinterer Steg')
                result['fem_rear_curvature']=True
        for j,freq in enumerate(r['mode_frequencies']):
            cs[0 if variant=='A' else 1].plot(r['test_x'],r['mode_shapes'][:,j],label=f'{j+1}: {freq:.3g} Hz')
    excel_tip=model.get('reconstructed_excel',{}).get('excel_written_flight_root_EI_m')
    if excel_tip is None:
        p=model['parameters']
        excel_ei=p['E1']*p.get('excel_I_new',0)
        if excel_ei>0:
            excel_tip=(p['total_lift']/2*L/2)*L**2/(2*excel_ei)
    if excel_tip is not None:
        excel_x=np.linspace(0,L,201)
        axs[1,0].plot(excel_x,excel_tip*(excel_x/L)**2*1000,'-.',color='black',
                      label=f'Excel M0 x²/(2EI): Spitze {excel_tip*1000:.1f} mm')
    measurements=cfg['test'].get('measurements',{})
    measured_variant=measurements.get('variant')
    if measured_variant in result['variants']:
        p=model['parameters']
        for key,sign,xpos,marker,label,offset in [
            ('measured_root',measurements.get('root_sign',-1),0.,'o','ΔHöhe',(10,12)),
            ('measured_tip',measurements.get('tip_sign',1),-L if measurements.get('tip_side')=='left' else L,'D','ΔTip',(-10,-24))]:
            if p.get(key) is None:continue
            value=sign*abs(p[key])*1000
            axs[1,1].scatter([xpos],[value],color='black',marker=marker,s=45,zorder=8,label=f'{measured_variant} Messung {label}')
            axs[1,1].annotate(f'{label} = {value:+.3f} mm',(xpos,value),xytext=offset,textcoords='offset points',fontsize=8,ha='left' if key=='measured_root' else 'right')
        result['test_measurements_plotted']=True
    for ax,title in zip(axs.flat,['EI [Nm²]','μ [kg/m]','Flug: w [mm]','Versuch: w [mm]']):
        ax.set(xlabel='x [m]',ylabel=title)
        ax.legend(fontsize=8)
    for ax in bs.flat:
        ax.legend()
    for ax,var in zip(cs,['A','B']):
        ax.set(title=f'{var}: Vollmodell, normierte Eigenformen',xlabel='x [m]',ylabel='φ / max|φ|')
        ax.legend(ncol=3,fontsize=8)
    for fig,name in [(fig,'beam_comparison'),(fig2,'loads'),(fig3,'modes')]:
        save(fig,folder/name)
        files.append(name)
    # Root section sketch uses actual centroid positions and cap thickness.
    fig,axs = plt.subplots(1,len(result['variants']),figsize=(11,3.8),sharey=True,squeeze=False)
    for ax,(variant,r) in zip(axs[0],result['variants'].items()):
        for p in r['sections'][0]['parts']:
            b,t,z = p['width'],p['thickness'],p['z']
            y=p.get('y',0.)
            color='#f0dca2' if p['name'].endswith('core') else '#41647e' if p['name'] in ['top','bottom'] else '#444b50'
            ax.add_patch(plt.Rectangle(((y-b/2)*1000,(z-t/2)*1000),b*1000,t*1000,facecolor=color,edgecolor='#555',linewidth=.25))
        ax.autoscale()
        ax.set_aspect('equal')
        ax.set(xlabel='y [mm]',ylabel='z [mm]',title=variant+': tatsächlicher Wurzelquerschnitt')
    save(fig,folder/'sections')
    files.append('sections')
    return files


def fem_picture(path,nodes,faces,displacements,title,scale=1,mode=False):
    fig,ax = plt.subplots(figsize=(11,4))
    polygons,colors = [],[]
    for face in faces:
        ids = face[:3]
        if not all(i in displacements for i in ids):
            continue
        polygons.append([[nodes[i][0]+scale*displacements[i][0],nodes[i][2]+scale*displacements[i][2]] for i in ids])
        colors.append(np.mean([displacements[i][2] for i in ids]))
    if not polygons:
        raise ValueError('Keine Solververschiebungen zur FEM-Bildausgabe')
    colors=np.array(colors)
    if mode:
        colors/=max(max(abs(v[2]) for v in displacements.values()),1e-30)
    pc = PolyCollection(polygons,array=colors,cmap='coolwarm',linewidths=.1,edgecolors='gray')
    ax.add_collection(pc)
    xyz = np.array(list(nodes.values()))
    ax.scatter(xyz[:,0],xyz[:,2],s=.1,c='black',alpha=.2,label='unverformtes Netz')
    ax.autoscale()
    suffix=f'; Faktor {scale:g}'
    if mode:
        shown=scale*max(np.linalg.norm(v) for v in displacements.values())*1000
        suffix=f'; willkürliche Darstellungsamplitude {shown:.3g} mm'
    ax.set(title=title+suffix,xlabel='x [m]',ylabel='z [m]')
    ax.legend(fontsize=8,loc='upper left')
    fig.colorbar(pc,ax=ax,label='φz / max|φz| [1]' if mode else 'u_z [m]')
    save(fig,path)


def convergence_picture(path,rows):
    fig,axs = plt.subplots(1,3,figsize=(12,4))
    for ax,key,title in zip(axs,['flight_tip_m','test_root_m','frequency_Hz'],['Flugtip [m]','Testwurzel [m]','Biegemode [Hz]']):
        ax.plot([r['level'] for r in rows],[r[key] for r in rows],'o-')
        ax.set(xlabel='Netzverfeinerungsfaktor',ylabel=title)
    save(fig,path)
