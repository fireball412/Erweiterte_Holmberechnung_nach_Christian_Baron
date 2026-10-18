import numpy as np
from wingcheck.curvature import line_curvature


def test_nonuniform_line_curvature_cubic_and_rigid_motion():
    x=np.linspace(0,1.4,31)**1.2
    w=.7*x**3-.2*x**2+3*x+1
    kappa,width=line_curvature(x,w)
    np.testing.assert_allclose(kappa,4.2*x-.4,atol=1e-9)
    straight,_=line_curvature(x,3*x+1)
    np.testing.assert_allclose(straight,0,atol=1e-9)
    assert np.all(width>0)
