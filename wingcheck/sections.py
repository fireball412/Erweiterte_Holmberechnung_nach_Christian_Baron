"""Component-based elastic centroid, self inertia and parallel-axis terms."""
import numpy as np


def component_section(parts):
    EA = sum(p['E']*p['area'] for p in parts)
    if EA <= 0:
        raise ValueError('Querschnitt ohne axiale Steifigkeit')
    z = sum(p['E']*p['area']*p['z'] for p in parts)/EA
    EI = sum(p['E']*(p['I']+p['area']*(p['z']-z)**2) for p in parts)
    mu = sum(p['density']*p['area'] for p in parts)
    return {'neutral_axis':z,'EI':EI,'mu':mu,'parts':parts}


def interpolate(model, x, name):
    ss = model['stations']
    return np.interp(abs(x),[s['x'] for s in ss],[s[name] for s in ss])


def section(model,cfg,x,variant='A'):
    ss = model['stations']
    i = min(max(np.searchsorted([s['x'] for s in ss],abs(x),side='right')-1,0),len(ss)-2)
    if variant == 'B':
        i = 0
    nup, nlo = ss[i]['plies_top'],ss[i]['plies_bottom']
    t = cfg['geometry']['ply_thickness_m']
    tu,tl = nup*t,nlo*t
    h = interpolate(model,x,'height')
    bu,bl = [interpolate(model,x,k) for k in ['width_top','width_bottom']]
    kind = cfg['geometry']['height_definition']
    if kind == 'outer':
        zu,zl = (h-tu)/2,(-h+tl)/2
        clear = h-tu-tl
    elif kind == 'clear':
        zu,zl = (h+tu)/2,-(h+tl)/2
        clear = h
    elif kind == 'centroid':
        zu,zl = h/2,-h/2
        clear = h-(tu+tl)/2
    else:
        raise ValueError('height_definition muss outer, clear oder centroid sein')
    if min(clear,tu,tl,bu,bl) <= 0:
        raise ValueError('Überlappende oder leere Gurtgeometrie')
    m = model['material']
    parts = [{'name':name,'area':b*th,'I':b*th**3/12,'z':z,'E':m['E1'],
              'density':m['density'],'width':b,'thickness':th}
             for name,b,th,z in [('top',bu,tu,zu),('bottom',bl,tl,zl)]]
    web = cfg['geometry']['web']
    from .sandwich import active,section_parts
    if active(cfg):
        parts = section_parts(model,cfg,x,variant)
    elif web['enabled']:
        tw = web['thickness_m']
        if tw > min(bu,bl):
            raise ValueError('Steg breiter als Gurt; dieses Querschnittsmodell unterstützt das nicht')
        parts.append({'name':'web','area':tw*clear,'I':tw*clear**3/12,
                      'z':(zu-tu/2+zl+tl/2)/2,'E':web['E_Pa'],
                      'density':web['density_kg_m3'],'width':tw,'thickness':clear})
    out = component_section(parts)
    out.update(plies_top=nup,plies_bottom=nlo,height=h,clear=clear,
               cap_volume_per_length=bu*tu+bl*tl,
               shear_GA=web['G_Pa']*web['thickness_m']*clear*5/6 if web['enabled'] else None)
    out['EI'] += cfg['geometry']['shell_EI_Nm2']
    out['mu'] += cfg['geometry']['shell_mass_kg_m']+cfg['geometry']['nonstructural_mass_kg_m']
    return out
