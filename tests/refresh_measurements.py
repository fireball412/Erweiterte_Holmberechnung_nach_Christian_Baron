"""Refresh Excel measurements and comparisons while retaining compatible FEM results."""
import copy
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wingcheck.analysis import compute
from wingcheck.excel import Workbook, dump_json
from wingcheck.model import normalize
from wingcheck.report import write_report
from wingcheck.visualization import plots


def main():
    out = ROOT / 'results'
    cfg = yaml.safe_load((out / 'used_config.yaml').read_text(encoding='utf-8'))
    active_cfg = yaml.safe_load((ROOT / 'config.yaml').read_text(encoding='utf-8'))
    for key in active_cfg:
        if key not in ('excel', 'output') and active_cfg[key] != cfg[key]:
            raise ValueError(f'Configuration changed: {key}; full analysis required.')
    old = json.loads((out / 'normalized_input.json').read_text(encoding='utf-8'))
    book = Workbook(cfg['excel'])
    model = normalize(book, cfg, cfg.get('cli_overrides'))
    def calculation_inputs(value):
        value = copy.deepcopy(value)
        value.pop('provenance', None)
        value['parameters'] = {k: v for k, v in value['parameters'].items()
                               if not k.startswith('measured_')}
        return value
    if calculation_inputs(old) != calculation_inputs(model):
        raise ValueError('Non-measurement model inputs changed; full analysis required.')
    fem = json.loads((out / 'summary.json').read_text(encoding='utf-8'))['fem']
    analysis = compute(model, cfg)
    images = plots(model, cfg, analysis, out, fem)
    source = book.inventory()
    dump_json(out / 'excel_inventory.json', source)
    dump_json(out / 'normalized_input.json', model)
    diagnostics = json.loads((out / 'diagnostics.json').read_text(encoding='utf-8'))
    write_report(out, model, cfg, analysis, fem, diagnostics, images, source)
    for key, value in model['parameters'].items():
        if key.startswith('measured_'):
            print(f'{key}: {old["parameters"][key]:.9g} -> {value:.9g} (SI)')
    assert analysis['test_measurements_plotted']
    print('Updated report, input audit, summaries and plots; retained compatible FEM results.')


if __name__ == '__main__':
    main()
