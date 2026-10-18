import argparse
import copy
import sys
from pathlib import Path
import yaml
from .excel import Workbook,dump_json
from .model import normalize
from .analysis import compute
from .fem import diagnose,execute
from .visualization import plots
from .report import write_report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Excel-Holmprüfung: schreibgeschützter Import, Balken und 3D-FEM')
    parser.add_argument('command',nargs='?',default='report',choices=['inspect','analytical','fem','report','diagnose'])
    parser.add_argument('--excel')
    parser.add_argument('--config',default='config.yaml')
    parser.add_argument('--output')
    parser.add_argument('--set',action='append',default=[],metavar='PARAMETER=WERT',help='Mapping-Parameter in seiner Originaleinheit überschreiben')
    parser.add_argument('--with-fem',action='store_true',help='Räumliche FEM im Report wirklich ausführen')
    args = parser.parse_args(argv)
    try:
        cfgpath = Path(args.config).resolve()
        cfg = yaml.safe_load(cfgpath.read_text(encoding='utf-8'))
        # Config-relative paths are deterministic even when invoked from elsewhere.
        for key in ['excel','output']:
            value = getattr(args,key) or cfg[key]
            path = Path(value)
            cfg[key] = str((path if path.is_absolute() else (Path.cwd() if getattr(args,key) else cfgpath.parent)/path).resolve())
        out = Path(cfg['output'])
        out.mkdir(parents=True,exist_ok=True)
        diagnostics = diagnose(cfg)
        dump_json(out/'diagnostics.json',diagnostics)
        if args.command=='diagnose':
            print(__import__('json').dumps(diagnostics,ensure_ascii=False,indent=2))
            return 0
        overrides = {}
        for item in args.set:
            key,value = item.split('=',1)
            overrides[key] = float(value)
        book = Workbook(cfg['excel'])
        source = book.inventory()
        dump_json(out/'excel_inventory.json',source)
        model = normalize(book,cfg,overrides)
        dump_json(out/'normalized_input.json',model)
        effective = copy.deepcopy(cfg)
        effective['cli_overrides'] = overrides
        (out/'used_config.yaml').write_text(yaml.safe_dump(effective,allow_unicode=True,sort_keys=False),encoding='utf-8')
        analysis = compute(model,cfg) if args.command!='inspect' else {'status':'nicht angefordert','variants':{}}
        fem = {'status':'nicht angefordert','variants':{}}
        if args.command=='fem' or args.with_fem:
            try:
                fem = execute(model,cfg,out,diagnostics)
            except Exception as exc:
                fem = {'status':'fehlgeschlagen','reasons':[str(exc)],'variants':{}}
        images = plots(model,cfg,analysis,out,fem)
        write_report(out,model,cfg,analysis,fem,diagnostics,images,source)
        print(f"Report: {out/'report.md'}")
        print(f"Balken: {analysis['status']}; FEM: {fem['status']}")
        for problem in model['missing']:
            print('OFFEN: '+problem)
        return 2 if model['missing'] or fem['status']=='fehlgeschlagen' else 0
    except (ValueError,KeyError,FileNotFoundError) as exc:
        print('Eingabefehler: '+str(exc),file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
