"""Full-model numerical beam eigenanalysis and documented Rayleigh estimate."""
import numpy as np
from scipy.linalg import eigh


def modes(K,M,fixed,count=6):
    free = np.setdiff1d(np.arange(len(K)),fixed)
    if count < 1:
        raise ValueError('Mindestens eine Eigenform erforderlich')
    # Solve the reciprocal problem Mφ=λKφ, λ=1/ω², selecting largest λ.
    # Thin/tapered caps plus short support intervals produce extreme high-mode
    # eigenvalues; direct smallest-eigenvalue extraction loses low-mode accuracy.
    count = min(count,len(free))
    reciprocal,vec = eigh(M[np.ix_(free,free)],K[np.ix_(free,free)],
                         subset_by_index=[len(free)-count,len(free)-1])
    reciprocal,vec = reciprocal[::-1],vec[:,::-1]
    vals = 1/reciprocal
    if np.any(vals <= 0):
        raise ValueError(f'Nichtpositive Eigenwerte: Lagerung/Material prüfen: {vals.tolist()}')
    shapes = np.zeros((len(K),len(vals)))
    shapes[free,:] = vec
    for j in range(len(vals)):
        shapes[:,j] /= max(abs(shapes[::2,j]))
    return np.sqrt(vals)/(2*np.pi),shapes


def symmetry(phi):
    symmetric = np.linalg.norm(phi-phi[::-1])
    antisymmetric = np.linalg.norm(phi+phi[::-1])
    return 'symmetrisch' if symmetric < antisymmetric else 'antisymmetrisch'


def rayleigh(K,M,trial,fixed):
    trial = np.array(trial,dtype=float)
    trial[fixed] = 0
    return np.sqrt(trial@K@trial/(trial@M@trial))/(2*np.pi)
