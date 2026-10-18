"""Standalone script executed with the installed FreeCAD Python interpreter.

Coordinates enter in SI; Part operates in millimetres. STEP and FCStd are mm.
Lofts interpolate widths/heights, while every ply-drop interval is a separate solid.
"""
import json
import sys
import os
import uuid
import zipfile
from pathlib import Path


def create(request_path):
    import FreeCAD as App
    import Part
    request = json.loads(Path(request_path).read_text(encoding='utf-8'))
    doc = App.newDocument('Wingcheck')
    solids = []
    for i,block in enumerate(request['blocks']):
        wires = []
        for end in block['ends']:
            x,b,z0,z1 = end[:4]
            yc = end[4] if len(end)>4 else 0.
            pts = [App.Vector(x*1000,y*1000,z*1000) for y,z in
                   [(yc-b/2,z0),(yc+b/2,z0),(yc+b/2,z1),(yc-b/2,z1),(yc-b/2,z0)]]
            wires.append(Part.Wire(Part.makePolygon(pts).Edges))
        solid = Part.makeLoft(wires,True,True)
        obj = doc.addObject('Part::Feature',f'Interval_{i:04d}')
        obj.addProperty('App::PropertyString','Component').Component = block['component']
        obj.addProperty('App::PropertyString','InputSI').InputSI = json.dumps(block)
        obj.Shape = solid
        solids.append(solid)
    fused = Part.makeCompound(solids) if request.get('partitioned_only') else solids[0].multiFuse(solids[1:]).removeSplitter()
    if not fused.isValid():
        raise RuntimeError('FreeCAD erzeugte ungültige Verbundgeometrie')
    obj = doc.addObject('Part::Feature','BondedSpar')
    obj.addProperty('App::PropertyString','ModelDefinition').ModelDefinition = 'SI input; CAD mm; ideal bonded central web'
    obj.Shape = fused
    if request.get('partitioned_only'):
        # Each physical partition is already a document object. Saving a second
        # compound referencing the same shapes triggers FreeCAD 1.1's save bug.
        doc.removeObject(obj.Name)
    doc.recompute()
    # Export unfused components; Gmsh BooleanFragments preserves material interfaces
    # and creates a conforming shared mesh. A fused solid alone loses these faces.
    # Save documented source bodies/fused solid before constructing a transient
    # shared-shape export compound (FreeCAD 1.1 serialization rejects that graph).
    # Atomic replacement also keeps any prior artifact intact on save failure.
    temporary = str(Path(request['fcstd']).with_name('new_'+uuid.uuid4().hex+'.FCStd'))
    try:
        doc.saveAs(temporary)
        saved=Path(temporary)
    except OSError:
        # Qt on this Windows installation sometimes writes a complete FCStd ZIP
        # but fails its final rename. Recover only a CRC-verified complete archive.
        candidates=list(Path(temporary).parent.glob(Path(temporary).name+'.*'))
        valid=[]
        for candidate in candidates:
            try:
                with zipfile.ZipFile(candidate) as archive:
                    if 'Document.xml' in archive.namelist() and archive.testzip() is None and sum(n.endswith('.brp') for n in archive.namelist())>=len(solids):
                        valid.append(candidate)
            except (OSError,zipfile.BadZipFile):
                pass
        if len(valid)!=1:
            raise
        saved=valid[0]
    os.replace(saved,request['fcstd'])
    mesh_obj = doc.addObject('Part::Feature','MeshPartitions')
    mesh_obj.Shape = Part.makeCompound(solids)
    doc.recompute()
    Part.export([mesh_obj],request['step'])
    Path(request['version_file']).write_text(json.dumps(App.Version()),encoding='utf-8')


if __name__ == '__main__':
    create(sys.argv[1])
