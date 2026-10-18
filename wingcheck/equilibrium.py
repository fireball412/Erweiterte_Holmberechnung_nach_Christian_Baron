"""Auditable resultant reconstruction from the self-contained CalculiX input."""
from pathlib import Path
import numpy as np


def input_nodes_loads(path):
    nodes,loads={},{}
    block=None
    for line in Path(path).read_text(encoding='ascii').splitlines():
        line=line.strip()
        if line.startswith('*'):
            block=line.split(',')[0].upper()
            continue
        if not line:continue
        fields=[v.strip() for v in line.split(',') if v.strip()]
        if block=='*NODE' and len(fields)==4:
            nodes[int(fields[0])]=np.array([float(v) for v in fields[1:]])
        elif block=='*CLOAD' and len(fields)==3:
            node,dof=int(fields[0]),int(fields[1])-1
            loads.setdefault(node,np.zeros(3))[dof]+=float(fields[2])
    return nodes,loads


def averaged_support_reactions(path,real_node_count):
    nodes,loads=input_nodes_loads(path)
    refs=sorted(n for n in nodes if n>real_node_count)
    if len(refs)!=3:return None
    positions=np.array([nodes[n] for n in refs])
    matrix=np.array([np.ones(3),positions[:,0],positions[:,1]])
    rhs=-np.array([sum(f[2] for f in loads.values()),sum(nodes[n][0]*f[2] for n,f in loads.items()),sum(nodes[n][1]*f[2] for n,f in loads.items())])
    forces=np.linalg.solve(matrix,rhs)
    return dict(source='Aus Gleichgewicht der drei gemittelten Vertikalbedingungen rekonstruiert; keine direkten RF-Werte der virtuellen Referenzknoten.',
                labels=['links hinten','links vorne','rechts'],positions_m=positions.tolist(),reactions_N=forces.tolist(),
                tensile_reaction_required=bool(np.min(forces)<-1e-5),equilibrium_residual=(matrix@forces-rhs).tolist())
