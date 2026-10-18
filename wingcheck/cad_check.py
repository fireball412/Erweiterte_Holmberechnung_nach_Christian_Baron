"""Reopen generated FCStd with FreeCAD and compare actual solid/mesh masses."""
import json
import sys
from pathlib import Path


def main(request_path):
    import FreeCAD as App
    request=json.loads(Path(request_path).read_text(encoding='utf-8'))
    results=[]
    for case in request['cases']:
        doc=App.openDocument(case['fcstd'])
        objects=[o for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
        assert objects and all(o.Shape.isValid() for o in objects)
        volume=sum(o.Shape.Volume for o in objects)*1e-9
        mass=sum(o.Shape.Volume*1e-9*(request['rho_core'] if o.Component.endswith('_core') else request['rho_cfk']) for o in objects)
        relative=abs(mass-case['mesh_mass_kg'])/case['mesh_mass_kg']
        assert relative<1e-6,(case,relative)
        results.append(dict(variant=case['variant'],case=case['case'],solids=len(objects),volume_m3=volume,
                            CAD_mass_kg=mass,mesh_mass_kg=case['mesh_mass_kg'],relative_difference=relative))
        App.closeDocument(doc.Name)
    Path(request['output']).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CAD erneut geöffnet, alle Körper gültig; CAD- und Netzmasse stimmen überein.')


if __name__=='__main__':
    main(sys.argv[1])
