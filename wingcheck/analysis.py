"""Identical variants and case definitions for static and dynamic beam checks."""
import numpy as np
from scipy.integrate import cumulative_trapezoid
from .sections import section
from .statics import assemble,static_solve,point_load,segmented_grid,segmented_cantilever
from .dynamics import modes,symmetry,rayleigh


def supports(model,cfg):
    L = model['half_span']
    a = model['parameters']['support_fraction']*L
    points = cfg['test']['supports_m'] or [-a,a]
    if len(points)!=2 or not -L < points[0] < points[1] < L:
        raise ValueError('Zwei geordnete Auflagen im Inneren des Vollflügels erforderlich')
    return points


def flight_load(model,cfg,x,sec):
    p = model['parameters']
    total = p['total_lift']/2
    kind = cfg['flight']['load_kind']
    if kind == 'ultimate':
        factor = cfg['flight']['safety_factor']
        if factor is None or factor <= 1:
            raise ValueError('Ultimate-Last verlangt einen expliziten Sicherheitsfaktor >1')
        total /= factor
    dist = cfg['flight']['distribution']
    if dist == 'chord_proportional':
        from .loads import chord_load
        q=chord_load(model,cfg,x)
        if cfg['flight']['mass_relief']:
            q-=p['load_factor']*cfg['test']['gravity']*np.array([s['mu'] for s in sec])
        return q
    if dist == 'uniform':
        weights = np.ones_like(x)
    elif dist == 'elliptic':
        weights = np.sqrt(np.maximum(0,1-(x/model['half_span'])**2))
    elif dist == 'stations':
        points = np.asarray(cfg['flight']['stations'],dtype=float)
        if points.ndim!=2 or points.shape[1]!=2 or len(points)<2 or np.any(np.diff(points[:,0])<=0) or points[0,0]!=0 or not np.isclose(points[-1,0],model['half_span']) or np.any(points[:,1]<0):
            raise ValueError('Stationslast muss 0..L eindeutig und nichtnegativ abdecken')
        weights = np.interp(x,points[:,0],points[:,1])
    else:
        raise ValueError('Unbekannte Auftriebsverteilung')
    norm = np.trapezoid(weights,x)
    if norm <= 0:
        raise ValueError('Leere Lastverteilung')
    q = weights*total/norm
    if cfg['flight']['mass_relief']:
        q -= p['load_factor']*cfg['test']['gravity']*np.array([s['mu'] for s in sec])
    return q


def compute(model,cfg):
    if model['missing']:
        return {'status':'nicht ausgeführt','reasons':model['missing'],'variants':{}}
    result = {'status':'ausgeführt','variants':{}}
    L = model['half_span']
    subdivisions = int(cfg['analysis']['elements_per_interval'])
    if subdivisions < 1:
        raise ValueError('elements_per_interval muss positiv sein')
    positions = [s['x'] for s in model['stations']]
    from .sandwich import active,breaks as sandwich_breaks
    if active(cfg):
        positions = sandwich_breaks(model,cfg)
    sp = supports(model,cfg)
    flight_positions=sorted(set(round(v,12) for v in positions+[p['x'] for p in model.get('planform',[])]))
    x = segmented_grid(flight_positions,subdivisions*8)
    # Integrate intervals with one-sided sections; duplicate interfaces are avoided
    # in solver nodes, but integration sums each interval separately in assemble.
    for variant in ['A','B']:
        sec_fn = lambda xx:section(model,cfg,xx,variant)
        sec = [sec_fn(xx) for xx in x]
        q = flight_load(model,cfg,x,sec)
        ga = None
        if cfg['analysis']['timoshenko']:
            if any(s['shear_GA'] is None for s in sec):
                raise ValueError('Schubverformung benötigt bestätigte Steg-Schubsteifigkeit')
            ga = [s['shear_GA'] for s in sec]
        flight = segmented_cantilever(x,q,sec_fn,root_rotation_stiffness=cfg['flight']['root_rotation_stiffness_Nm'],shear=ga is not None)
        # Independent numerical beam solution provides jump-segmented integration
        # using Gauss integration; report integral curve with convergence caveat.
        xf = segmented_grid(flight_positions,subdivisions)
        Kf,Mf,ff = assemble(xf,sec_fn,lambda xx:np.interp(xx,x,q))
        fixed = [0,1]
        if cfg['flight']['root_rotation_stiffness_Nm'] is not None:
            Kf[1,1] += cfg['flight']['root_rotation_stiffness_Nm']
            fixed = [0]
        uf,rf = static_solve(Kf,ff,fixed)
        bending_w = uf[::2].copy()
        total_w = bending_w+np.interp(xf,x,flight['shear_w'])
        # Full-model experiment: two vertical supports, no root clamp.
        breaks = [-p for p in positions[::-1]]+positions+sp+[0]
        xt = segmented_grid(breaks,subdivisions)
        extra = model['parameters']['modal_mass']
        g = cfg['test']['gravity']
        gravity = (lambda xx:-sec_fn(xx)['mu']*g) if cfg['test']['self_weight'] else (lambda xx:0.)
        K,M,f = assemble(xt,sec_fn,gravity,extra,cfg['test']['central_inertia_kg_m2'])
        force = cfg['test']['force_N']
        if force is None:
            force = model['parameters']['test_mass']*g
        width = cfg['test']['load_width_m']
        if width > 0:
            # Consistent distributed central force, with edges inserted into mesh.
            if width/2 >= L:
                raise ValueError('Zentrale Lastbreite muss kleiner als Gesamtspannweite sein')
            xt = segmented_grid(breaks+[-width/2,width/2],subdivisions)
            qtest = lambda xx:gravity(xx)+(-force/width if abs(xx)<width/2 else 0.)
            K,M,f = assemble(xt,sec_fn,qtest,extra,cfg['test']['central_inertia_kg_m2'])
        else:
            point_load(f,xt,0.,-force)
        fixed = [2*int(np.argmin(abs(xt-a))) for a in sp]
        u,r = static_solve(K,f,fixed)
        freqs,forms = modes(K,M,fixed,cfg['analysis']['modes'])
        root_index = int(np.argmin(abs(xt)))
        # Static unit-load influence vector is a kinematically admissible Rayleigh trial.
        unit_f = np.zeros_like(f)
        point_load(unit_f,xt,0.,-1.)
        trial,_ = static_solve(K,unit_f,fixed)
        compliance = -trial[2*root_index]
        effective_mass = float(trial@M@trial/trial[2*root_index]**2)
        # Integrate component volume/mass with Gauss quadrature, never smooth ply count.
        volume,mass,structural_mass = {},0.,0.
        gs,ws = np.polynomial.legendre.leggauss(5)
        for a,b in zip(positions[:-1],positions[1:]):
            for gg,ww in zip(gs,ws):
                s = sec_fn((a+b)/2+gg*(b-a)/2)
                mass += s['mu']*ww*(b-a)/2
                for part in s['parts']:
                    volume[part['name']] = volume.get(part['name'],0)+part['area']*ww*(b-a)/2
                    structural_mass += part['area']*part['density']*ww*(b-a)/2
        half_mass = mass
        maxidx = int(np.argmax(abs(total_w)))
        root_EI = sec_fn(0)['EI']
        a = model['parameters']['support_fraction']*L
        summary = {'half_spar_mass_kg':structural_mass,'half_model_mass_kg':half_mass,
                   'half_shell_mass_kg':cfg['geometry']['shell_mass_kg_m']*L,
                   'half_nonstructural_mass_kg':cfg['geometry']['nonstructural_mass_kg_m']*L,
                   'flight_tip_m':float(total_w[-1]),'flight_integral_tip_m':float(flight['w'][-1]),
                   'flight_bending_tip_m':float(bending_w[-1]),'flight_shear_tip_m':float(flight['shear_w'][-1]),
                   'flight_max_m':float(total_w[maxidx]),'flight_max_x_m':float(xf[maxidx]),
                   'flight_reaction_N':float(rf[0]),'flight_reaction_Nm':float(rf[1]),
                   'test_root_m':float(u[2*root_index]),'test_left_tip_m':float(u[0]),'test_right_tip_m':float(u[-2]),
                   'test_reactions_N':[float(r[i]) for i in fixed],
                   'test_reaction_residual_N':float(sum(r[fixed])+sum(f[::2])),
                   'frequencies_Hz':freqs.tolist(), 'mode_symmetry':[symmetry(forms[::2,j]) if np.allclose(xt,-xt[::-1]) else 'unsymmetrischer Aufbau' for j in range(len(freqs))],
                   'rayleigh_Hz':float(rayleigh(K,M,trial,fixed)),
                   'effective_mass_kg':effective_mass,'spring_Hz':float(np.sqrt(1/compliance/effective_mass)/(2*np.pi)),
                   'material_volume_half_m3':volume,
                   'constant_EI_flight_m':float(model['parameters']['total_lift']/2/L*L**4/(8*root_EI)),
                   'large_deflection':bool(max(abs(total_w))/L>cfg['analysis']['large_deflection_ratio']),
                   'test_central_mass_kg':extra,'static_test_force_N':float(force)}
        if cfg['flight']['load_kind']=='ultimate':
            summary['constant_EI_flight_m'] /= cfg['flight']['safety_factor']
        if cfg['flight']['distribution']=='chord_proportional':
            # Unit-load influence at the cantilever tip, using the active q(s).
            # Five-point Gauss quadrature is exact for piecewise-linear q here.
            from .loads import chord_load
            constant=0.
            for aa,bb in zip(flight_positions[:-1],flight_positions[1:]):
                for gg,ww in zip(gs,ws):
                    ss=(aa+bb)/2+gg*(bb-aa)/2
                    constant+=chord_load(model,cfg,ss)*ss**2*(3*L-ss)/(6*root_EI)*ww*(bb-aa)/2
            summary['constant_EI_flight_m']=float(constant)
        result['variants'][variant] = {'summary':summary,'flight':flight,
            'flight_beam_x':xf,'flight_beam_w':total_w,'sections':sec,
            'test_x':xt,'test_w':u[::2],'test_theta':u[1::2],
            'mode_shapes':forms[::2,:],'mode_frequencies':freqs}
    return result
