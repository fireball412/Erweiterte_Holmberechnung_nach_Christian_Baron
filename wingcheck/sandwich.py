"""Accepted wedge-cap / two sleeved Depron webs, explicit physical rectangles."""
import math
import numpy as np


def active(cfg):
    return cfg['geometry'].get('sandwich',{}).get('enabled',False)


def breaks(model,cfg):
    c = cfg['geometry']['sandwich']
    return sorted(set(round(x,12) for x in [s['x'] for s in model['stations']]+[c['pocket_length_m'],c['front_end_m'],c['rear_end_m']]))


def rectangles(model,cfg,x,variant,sample_x=None):
    from .sections import interpolate
    c = cfg['geometry']['sandwich']
    xx = abs(x)
    sx = xx if sample_x is None else abs(sample_x)
    ss = model['stations']
    i = min(max(np.searchsorted([s['x'] for s in ss],sx,side='right')-1,0),len(ss)-2)
    if variant=='B':
        i=0
    tu,tl = [ss[i][k]*cfg['geometry']['ply_thickness_m'] for k in ['plies_top','plies_bottom']]
    h,b = interpolate(model,xx,'height'),interpolate(model,xx,'width_top')
    if cfg['geometry']['height_definition']!='outer':
        raise ValueError('Schlauchmodell benötigt bestätigte Gurt-Außenhöhe')
    zu,zl = h/2-tu,-h/2+tl
    rs = [dict(name='top',mat='CAP',y0=0.,y1=b,z0=zu,z1=h/2),
          dict(name='bottom',mat='CAP',y0=0.,y1=b,z0=-h/2,z1=zl)]
    wall = interpolate(model,xx,'web_required')
    r0 = interpolate(model,0,'web_required')
    front0 = c['rear_center_y_m']+c['core_width_m']+2*r0+c['pocket_width_m']
    frontlast = interpolate(model,c['front_end_m'],'width_top')-.003
    f = np.clip((xx-c['pocket_length_m'])/(c['front_end_m']-c['pocket_length_m']),0,1)
    front = front0+(frontlast-front0)*f
    for name,yc,end in [('rear',c['rear_center_y_m'],c['rear_end_m']),('front',front,c['front_end_m'])]:
        if sx>=end-1e-11 and end<model['half_span']-1e-11:
            continue
        y0,y1 = yc-c['core_width_m']/2,yc+c['core_width_m']/2
        if y0-wall < -1e-8 or y1+wall > b+1e-8:
            raise ValueError(f'{name}: Schlauch außerhalb Gurt bei x={xx}')
        if zu-zl<=2*wall:
            raise ValueError('Schlauch überlappt sich in Dickenrichtung')
        rs.append(dict(name=name+'_core',mat='CORE',y0=y0,y1=y1,z0=zl+wall,z1=zu-wall))
        # Vertical walls occupy full outer height; top/bottom fill between cores.
        for side,aa,bb in [('left',y0-wall,y0),('right',y1,y1+wall)]:
            for j,(a,bv) in enumerate([(aa,(aa+bb)/2),((aa+bb)/2,bb)]):
                rs.append(dict(name=f'{name}_{side}_{j}',mat=f'V{j}',y0=a,y1=bv,z0=zl,z1=zu))
        for side,aa,bb in [('bottom',zl,zl+wall),('top',zu-wall,zu)]:
            for j,(a,bv) in enumerate([(aa,(aa+bb)/2),((aa+bb)/2,bb)]):
                rs.append(dict(name=f'{name}_{side}_{j}',mat=f'H{j}',y0=y0,y1=y1,z0=a,z1=bv))
    return rs


def effective_E(model,cfg,mat):
    if mat=='CORE':
        return cfg['geometry']['sandwich']['core_E']
    if mat=='CAP':
        return model['material']['E1']
    m=model['material']
    angle=math.radians(cfg['geometry']['sandwich']['sleeve_angles_deg'][int(mat[1])])
    c,s=math.cos(angle),math.sin(angle)
    return 1/(c**4/m['E1']+s**4/m['E2']+(1/m['G12']-2*m['nu12']/m['E1'])*s*s*c*c)


def section_parts(model,cfg,x,variant):
    parts=[]
    for r in rectangles(model,cfg,x,variant):
        b,t=r['y1']-r['y0'],r['z1']-r['z0']
        parts.append(dict(name=r['name'],area=b*t,I=b*t**3/12,z=(r['z1']+r['z0'])/2,
                          y=(r['y1']+r['y0'])/2,E=effective_E(model,cfg,r['mat']),
                          density=cfg['geometry']['sandwich']['core_density'] if r['mat']=='CORE' else model['material']['density'],
                          width=b,thickness=t))
    return parts
