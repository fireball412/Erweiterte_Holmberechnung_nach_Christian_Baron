"""Shared planform-proportional flight load, independent of spar cap width."""
import numpy as np


def chord(model,x):
    points=model.get('planform',[])
    if len(points)<2:raise ValueError('Tiefenproportionale Last benötigt Flächentiefenstationen aus Excel')
    return np.interp(np.abs(x),[p['x'] for p in points],[p['chord'] for p in points])


def chord_resultants(model,cfg):
    points=model.get('planform',[])
    if len(points)<2:raise ValueError('Flächentiefenstationen fehlen')
    area,first=0.,0.
    for a,b in zip(points[:-1],points[1:]):
        dx=b['x']-a['x'];ca,cb=a['chord'],b['chord']
        area+=dx*(ca+cb)/2
        first+=a['x']*dx*(ca+cb)/2+dx**2*(ca/2+(cb-ca)/3)
    force=model['parameters']['total_lift']/2
    if cfg['flight']['load_kind']=='ultimate':force/=cfg['flight']['safety_factor']
    return dict(half_area_m2=area,force_N=force,moment_Nm=force*first/area,
                resultant_x_m=first/area,pressure_coefficient_N_m2=force/area,
                root_q_N_m=force/area*points[0]['chord'],tip_q_N_m=force/area*points[-1]['chord'])


def chord_load(model,cfg,x):
    return chord(model,x)*chord_resultants(model,cfg)['pressure_coefficient_N_m2']
