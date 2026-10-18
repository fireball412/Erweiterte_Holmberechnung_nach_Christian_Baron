"""Publish only completed checkpoint rows as an explicitly running report."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import yaml
from wingcheck.excel import Workbook
from wingcheck.model import normalize
from wingcheck.analysis import compute
from wingcheck.visualization import plots
from wingcheck.report import write_report

out=Path('results')
cfg=yaml.safe_load((out/'used_config.yaml').read_text(encoding='utf-8'))
fem=json.loads((out/'fem_progress.json').read_text(encoding='utf-8'))
for record in fem['variants'].values():
    record['meshes']=[r for r in record['meshes'] if all(k in r for k in ['flight_tip_m','test_root_m','frequency_Hz'])]
fem['variants']={v:r for v,r in fem['variants'].items() if r['meshes']}
fem['status']='läuft – Zwischenstand'
fem['reasons']=['Zwischenbericht: nur vollständig abgeschlossene Netzstufen aufgeführt; weitere Solverläufe laufen.']
book=Workbook(cfg['excel']);model=normalize(book,cfg,cfg.get('cli_overrides'))
analysis=compute(model,cfg)
images=plots(model,cfg,analysis,out,fem)
write_report(out,model,cfg,analysis,fem,json.loads((out/'diagnostics.json').read_text(encoding='utf-8')),images,book.inventory())
print('Zwischenbericht aktualisiert; Solverprozess unverändert aktiv.')
