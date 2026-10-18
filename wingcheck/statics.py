"""Segment quadrature and full-span Euler-Bernoulli finite elements, SI."""
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.linalg import solve


def cantilever(x,q,EI,tip_force=0,root_rotation_stiffness=None,GA=None):
    x,q,EI = [np.asarray(a,dtype=float) for a in [x,q,EI]]
    def tail(a):
        return -cumulative_trapezoid(a[::-1],x[::-1],initial=0)[::-1]
    V = tail(q)+tip_force
    M = tail(q*x)-x*tail(q)+tip_force*(x[-1]-x)
    kappa = M/EI
    theta = cumulative_trapezoid(kappa,x,initial=0)
    if root_rotation_stiffness is not None:
        if root_rotation_stiffness <= 0:
            raise ValueError('Drehfeder muss positiv sein')
        theta += M[0]/root_rotation_stiffness
    w = cumulative_trapezoid(theta,x,initial=0)
    shear = cumulative_trapezoid(V/np.asarray(GA),x,initial=0) if GA is not None else np.zeros_like(x)
    return dict(x=x,q=q,V=V,M=M,curvature=kappa,theta=theta,w=w+shear,shear_w=shear,
                root_force=float(V[0]),root_moment=float(M[0]))


def element_matrices(length,EI,mu):
    l = length
    K = EI/l**3*np.array([[12,6*l,-12,6*l],[6*l,4*l*l,-6*l,2*l*l],
                         [-12,-6*l,12,-6*l],[6*l,2*l*l,-6*l,4*l*l]])
    M = mu*l/420*np.array([[156,22*l,54,-13*l],[22*l,4*l*l,13*l,-3*l*l],
                          [54,13*l,156,-22*l],[-13*l,-3*l*l,-22*l,4*l*l]])
    return K,M


def segmented_cantilever(x,q,section_fn,root_rotation_stiffness=None,shear=False):
    """Integrate one-sided curvature inside every segment; no EI jump smoothing."""
    sec = [section_fn(xx) for xx in x]
    result = cantilever(x,q,[s['EI'] for s in sec],root_rotation_stiffness=root_rotation_stiffness)
    w,theta,sw = np.zeros_like(x),np.zeros_like(x),np.zeros_like(x)
    if root_rotation_stiffness is not None:
        theta[0] = result['M'][0]/root_rotation_stiffness
    gs,ws = np.polynomial.legendre.leggauss(5)
    for i,(a,b) in enumerate(zip(x[:-1],x[1:])):
        l = b-a
        dtheta,dw,ds = 0.,0.,0.
        slope = (q[i+1]-q[i])/l
        for gg,ww in zip(gs,ws):
            h = (gg+1)*l/2
            s = section_fn(a+h)
            moment = result['M'][i]-result['V'][i]*h+q[i]*h*h/2+slope*h**3/6
            curvature = moment/s['EI']
            dtheta += curvature*ww*l/2
            dw += (l-h)*curvature*ww*l/2
            if shear:
                if not s.get('shear_GA'):
                    raise ValueError('Bestätigte Schubsteifigkeit fehlt')
                V = result['V'][i]-q[i]*h-slope*h*h/2
                ds += V/s['shear_GA']*ww*l/2
        w[i+1] = w[i]+theta[i]*l+dw
        theta[i+1] = theta[i]+dtheta
        sw[i+1] = sw[i]+ds
    result.update(w=w+sw,theta=theta,shear_w=sw)
    return result


def shape(r,l):
    return np.array([1-3*r*r+2*r**3,l*(r-2*r*r+r**3),3*r*r-2*r**3,l*(-r*r+r**3)])


def assemble(x,section_fn,q_fn=lambda x:0.,central_mass=0.,central_inertia=0.):
    n = 2*len(x)
    K,M,f = np.zeros((n,n)),np.zeros((n,n)),np.zeros(n)
    gauss,weights = np.polynomial.legendre.leggauss(4)
    for i,(a,b) in enumerate(zip(x[:-1],x[1:])):
        l = b-a
        dofs = np.arange(2*i,2*i+4)
        # EI and consistent mass integrated at Gauss points; accommodates linear taper.
        ke,me,fe = np.zeros((4,4)),np.zeros((4,4)),np.zeros(4)
        for g,w in zip(gauss,weights):
            r = (g+1)/2
            sec = section_fn(a+r*l)
            B = np.array([-6+12*r, l*(-4+6*r),6-12*r,l*(-2+6*r)])/l**2
            N = shape(r,l)
            ke += sec['EI']*np.outer(B,B)*w*l/2
            me += sec['mu']*np.outer(N,N)*w*l/2
            fe += N*q_fn(a+r*l)*w*l/2
        K[np.ix_(dofs,dofs)] += ke
        M[np.ix_(dofs,dofs)] += me
        f[dofs] += fe
    if central_mass or central_inertia:
        hits = np.flatnonzero(np.isclose(x,0,atol=1e-12))
        if len(hits) != 1:
            raise ValueError('Für Zentralmasse muss x=0 ein Knoten sein')
        j = 2*hits[0]
        M[j,j] += central_mass
        M[j+1,j+1] += central_inertia
    return K,M,f


def point_load(f,x,position,force):
    if not x[0] <= position <= x[-1]:
        raise ValueError('Punktlast außerhalb des Balkens')
    i = min(np.searchsorted(x,position,side='right')-1,len(x)-2)
    l = x[i+1]-x[i]
    f[2*i:2*i+4] += shape((position-x[i])/l,l)*force


def static_solve(K,f,fixed):
    free = np.setdiff1d(np.arange(len(f)),fixed)
    u = np.zeros_like(f)
    u[free] = solve(K[np.ix_(free,free)],f[free],assume_a='pos')
    return u,K@u-f


def segmented_grid(breaks,subdivisions):
    breaks = sorted(set(float(x) for x in breaks))
    return np.concatenate([np.linspace(a,b,subdivisions+1)[:-1] for a,b in zip(breaks[:-1],breaks[1:])]+[np.array([breaks[-1]])])
