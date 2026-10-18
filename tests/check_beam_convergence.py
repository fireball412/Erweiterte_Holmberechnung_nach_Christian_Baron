"""Refine the actual provisional beam model; preserve primary report results."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import yaml
from wingcheck.excel import Workbook,dump_json
from wingcheck.model import normalize
from wingcheck.analysis import compute

cfg = yaml.safe_load(Path('config.yaml').read_text(encoding='utf-8'))
baseline = json.loads(Path('results/summary.json').read_text(encoding='utf-8'))['beam']
cfg['analysis']['elements_per_interval'] *= 2
refined = compute(normalize(Workbook(cfg['excel']),cfg),cfg)
checks = {}
for row in baseline:
    v = row['variant']
    fine = refined['variants'][v]['summary']
    differences = {key:abs(row[key]-fine[key])/abs(fine[key]) for key in ['flight_tip_m','test_root_m']}
    differences['frequencies_Hz'] = [abs(a-b)/b for a,b in zip(row['frequencies_Hz'],fine['frequencies_Hz'])]
    checks[v] = {'relative_changes':differences,'refined_summary':fine}
    assert max(differences['frequencies_Hz']+[differences['flight_tip_m'],differences['test_root_m']])<.02
dump_json('results/beam_convergence.json',checks)
print('Balken-Netzverdopplung: Statik und alle sechs Eigenfrequenzen innerhalb 2 %.')
