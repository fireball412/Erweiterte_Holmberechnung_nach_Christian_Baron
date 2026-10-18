"""Recover linear vertical line curvature from actual FEM displacements."""
import csv
import json
from pathlib import Path
import numpy as np
from .postprocess import parse_dat


def line_curvature(x,w,points=5):
    """Local cubic least-squares recovery; x/w in metres, w'' in 1/metre."""
    x=np.asarray(x,dtype=float);w=np.asarray(w,dtype=float)
    if len(x)<points or len(x)!=len(w) or np.any(np.diff(x)<=0):
        raise ValueError('Krümmung benötigt mindestens fünf verschiedene, sortierte Stationen')
    kappa=[];width=[]
    for i,position in enumerate(x):
        start=int(np.clip(i-points//2,0,len(x)-points))
        ids=np.arange(start,start+points)
        scale=np.max(abs(x[ids]-position))
        coef=np.polynomial.polynomial.polyfit((x[ids]-position)/scale,w[ids],3)
        kappa.append(2*coef[2]/scale**2)
        width.append(x[ids[-1]]-x[ids[0]])
    return np.array(kappa),np.array(width)


def flight_rear_curvature(folder,model,cfg,csv_path):
    """Use existing nodes on the rear core centreline, not a section average."""
    if any(s['plies_top']!=s['plies_bottom'] for s in model['stations']):
        raise ValueError('Mittellinie z=0 setzt symmetrische Gurtdicken voraus')
    folder=Path(folder)
    mesh=json.loads((folder/'mesh_si.json').read_text(encoding='utf-8'))
    displacement=parse_dat(folder/'static.dat')['displacements']
    yc=cfg['geometry']['sandwich']['rear_center_y_m']
    samples={}
    for key,p in mesh['nodes'].items():
        n=int(key)
        if abs(p[1]-yc)<1e-9 and abs(p[2])<1e-9:
            if n not in displacement:raise ValueError('Fehlende FEM-Mittellinienverschiebung')
            samples.setdefault(round(p[0],10),[]).append(displacement[n][2])
    x=np.array(sorted(samples));w=np.array([np.mean(samples[t]) for t in x])
    if len(x)<5 or abs(x[0])>1e-9 or abs(x[-1]-model['half_span'])>1e-9:
        raise ValueError('FEM-Knoten decken hintere Mittellinie nicht vollständig ab')
    kappa,width=line_curvature(x,w)
    with Path(csv_path).open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f)
        interior=np.arange(len(x))
        reliable_stencil=(interior>=2)&(interior<len(x)-2)
        writer.writerow(['x_m','y_m','z_m','uz_m','kappa_linear_1_m','fit_span_m','interior_stencil'])
        writer.writerows(zip(x,np.full(len(x),yc),np.zeros(len(x)),w,kappa,width,reliable_stencil))
    # Do not present one-sided endpoint recovery as a reliable tip/root value.
    return x[2:-2],kappa[2:-2]
