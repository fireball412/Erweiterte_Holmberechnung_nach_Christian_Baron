import numpy as np
from wingcheck.postprocess import parse_dat
from wingcheck.gallery import exterior_faces,triangles


def test_stress_parser_keeps_last_increment_and_component_order(tmp_path):
    path = tmp_path/'static.dat'
    path.write_text(' stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set SOLIDS and time 1\n\n'
                    ' 1 1 1.0E+6 2.0E+6 3.0E+6 4.0E+6 5.0E+6 6.0E+6\n'
                    ' 1 2 -1.0E+6 0 0 0 0 0\n'
                    ' stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set SOLIDS and time 2\n\n'
                    ' 1 1 7.0D+6 0 0 0 0 0\n',encoding='ascii')
    assert parse_dat(path)['stresses']=={1:[[7e6,0,0,0,0,0]]}


def test_internal_material_faces_are_not_rendered():
    elements = [[1,2,3,4],[1,3,2,5]]
    faces = [[1,2,3],[1,2,4],[1,3,4],[2,3,4],[1,3,5],[1,2,5],[2,3,5]]
    ext = exterior_faces(elements,faces)
    assert len(ext)==6
    assert all(set(face)!={1,2,3} for face,_ in ext)
    assert triangles([1,2,3,4,5,6])==[(1,4,6),(4,2,5),(6,5,3),(4,5,6)]
