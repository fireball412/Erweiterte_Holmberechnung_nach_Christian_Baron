"""One actual NLGEOM static test on the explicit synthetic reference mesh."""
import runpy
from pathlib import Path
from wingcheck.fem import read_msh,write_input,run_command
from wingcheck.postprocess import parse_dat
from wingcheck.excel import dump_json

if __name__=='__main__':
    inputs = runpy.run_path(str(Path(__file__).with_name('verify_artifacts.py')))
    cfg,model = inputs['cfg'],inputs['model']
    folder = Path('benchmark_results/fem/A/level_3/flight')
    nodes,elements,faces = read_msh(folder/'mesh.msh')
    write_input(folder/'nonlinear.inp',nodes,elements,faces,model,cfg,'A','flight',nonlinear=True)
    run_command([cfg['paths']['calculix'],'-i','nonlinear'],folder,folder/'nonlinear.log')
    data = parse_dat(folder/'nonlinear.dat')
    assert data['displacements']
    dump_json(folder/'nonlinear.parsed.json',data)
    print('Synthetische geometrisch nichtlineare Statik tatsächlich ausgeführt')
