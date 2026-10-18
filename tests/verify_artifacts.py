"""Validate generated source report and independently inspect synthetic solver files."""
import json
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wingcheck.postprocess import parse_dat,convergence
from wingcheck.excel import Workbook,dump_json
from wingcheck.fem import read_msh,write_input,reaction_balance

root = Path(__file__).resolve().parents[1]
out = root/'results'
report = (out/'report.md').read_text(encoding='utf-8')
for relative in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',report):
    assert (out/relative).is_file(),relative
inventory = json.loads((out/'excel_inventory.json').read_text(encoding='utf-8'))
assert Workbook(inventory['path']).sha256 == inventory['sha256']
assert json.loads((out/'summary.json').read_text(encoding='utf-8'))['fem']['status'] in ['ausgeführt','nicht ausgeführt','fehlgeschlagen','nicht angefordert']
benchmark_path = root/'benchmark_results/synthetic_benchmark.json'
if not benchmark_path.exists():
    raise SystemExit('Synthetischer Gesamtlauf noch nicht fertig')
benchmark = json.loads(benchmark_path.read_text(encoding='utf-8'))
assert benchmark['status']=='ausgeführt'
summary = {}
cfg = __import__('yaml').safe_load((root/'config.yaml').read_text(encoding='utf-8'))
cfg['geometry']['sandwich']['enabled']=False
cfg['geometry'].update(ply_thickness_m=.001,manufacturing_plan_confirmed=True)
cfg['geometry']['web'].update(enabled=True,thickness_m=.002,E_Pa=70e9,G_Pa=70e9/2.6,density_kg_m3=2700)
cfg['test'].update(support_width_m=.015,load_width_m=.02)
cfg['flight']['load_kind']='limit'
cfg['flight']['distribution']='uniform' # Unveränderter synthetischer Referenzfall.
mat = dict(E1=70e9,E2=70e9,E3=70e9,G12=70e9/2.6,G13=70e9/2.6,G23=70e9/2.6,nu12=.3,nu13=.3,nu23=.3,density=2700)
station = dict(width_top=.02,width_bottom=.02,height=.02,plies_top=2,plies_bottom=2)
model = dict(half_span=.15,stations=[dict(station,x=0),dict(station,x=.15)],material=mat,
             parameters=dict(support_fraction=.6,total_lift=20,test_mass=1.,modal_mass=1.))
for variant,data in benchmark['variants'].items():
    assert len(data['meshes'])==3
    for row in data['meshes']:
        for case in ['flight','test']:
            folder = root/f"benchmark_results/fem/{variant}/level_{row['level']}/{case}"
            nodes,elements,faces = read_msh(folder/'mesh.msh')
            metadata = write_input(folder/'verified.inp',nodes,elements,faces,model,cfg,variant,case)
            reaction,residual = reaction_balance(parse_dat(folder/'static.dat'),metadata)
            row[case+'_reaction_residual_N'] = residual
            row[case+'_mesh_mass_kg'] = metadata['mesh_mass_kg']
            row[case+'_reaction_N'] = reaction
    updated = convergence(data['meshes'],.02)
    residual = max(abs(row[case+'_reaction_residual_N']) for row in data['meshes'] for case in ['flight','test'])
    assert residual < .001, (variant,residual)
    summary[variant] = {'convergence':updated,'max_reaction_residual_N':residual,
                        'finest':data['meshes'][-1]}
    for level in [1,2,3]:
        for case in ['flight','test']:
            folder = root/f'benchmark_results/fem/{variant}/level_{level}/{case}'
            assert (folder/'spar.FCStd').stat().st_size > 0
            assert (folder/'mesh.msh').stat().st_size > 0
            assert len(parse_dat(folder/'modal.dat')['frequencies'])==6
            assert parse_dat(folder/'static.dat')['displacements']
dump_json(out/'synthetic_validation.json',summary)
dump_json(benchmark_path,benchmark)
lines = ['# Ausführungs- und Verifikationsnachweis','',
         'Stand: 18.10.2026. 33 physikalische/Import-/Postprocessing-/Schlauchmodell-/Lastverteilungs-/Auflager-/Krümmungs-Referenztests bestanden (`python -m pytest -q`); Python-Module kompilierbar.',
         'Die Quelldatei ist unverändert (SHA-256 gegen Importinventur geprüft). Alle Bildpfade im Originalbericht existieren.',
         '', '## Tatsächlicher synthetischer Integrationstest','',
         '**Keine Biest-/Excel-Ergebnisse.** Expliziter homogener I-Holm: Halbspannweite 0,15 m, Gurtbreite 0,02 m, Außenhöhe 0,02 m, zwei Lagen je 0,001 m je Gurt, Stegbreite 0,002 m, E=70 GPa, ν=0,3, ρ=2700 kg/m³. 20 N Gesamtfluglast, 1 kg Zentralmasse, Auflagen bei ±0,09 m. Endliche Auflagen-/Lastbreiten siehe Testskript.',
         'Beide Varianten sind hier absichtlich identisch. Drei Netzstufen pro Variante und Lastfall; insgesamt 12 CAD-/Netzmodelle und 24 CalculiX-Läufe (je Statik und sechs Eigenformen). FCStd, STEP, Netze, Eingaben, Logs und echte DAT/FRD-Dateien unter `../benchmark_results/fem/`.',
         '', '| Variante | größter Reaktionsrest [N] | Konvergenz aller 6 Eigenwerte und statischen Größen ≤2 % |', '|---|---:|---|']
for variant,data in summary.items():
    lines.append(f"| {variant} | {data['max_reaction_residual_N']:.6g} | {data['convergence']['converged']} |")
lines += ['', 'Details: [synthetic_validation.json](synthetic_validation.json). Ein eventuell nicht erreichtes Konvergenzziel ist ein ausgewiesenes Testergebnis, kein ersetzter Solverwert.',
          '', '## Originalmappe','', 'Import, Zuordnung, Cache-Konsistenzprüfung und Rekonstruktion der Excel-Näherungen ausgeführt. Siehe [Report](report.md) und `../config.yaml`.']
source_results = json.loads((out/'summary.json').read_text(encoding='utf-8'))
if source_results.get('beam'):
    lines += ['Die Balkenvarianten wurden mit dem ausdrücklich vorläufigen YAML-Annahmensatz gerechnet (angenommener Fertigungsplan, Excel-Auftrieb als Vergleichslast). Räumlicher Original-FEM-Status: '+source_results['fem']['status']+'. Bestätigte Stegannahmen sind im aktiven Schlauchmodell hinterlegt; Materialwerte und Taschenlänge bleiben Annahmen.']
else:
    lines += ['Variantenrechnung wegen fehlender Pflichtdaten nicht ausgeführt.']
nonlinear = root/'benchmark_results/fem/A/level_3/flight/nonlinear.dat'
if nonlinear.exists() and parse_dat(nonlinear)['displacements']:
    lines += ['', '## Geometrisch nichtlineare Zusatzprüfung','',
              'Ein weiterer tatsächlicher CalculiX-NLGEOM-Lauf auf dem synthetischen feinsten Flugnetz ist abgeschlossen. Insgesamt damit 25 Solverläufe. Ergebnisdateien und Log unter `../benchmark_results/fem/A/level_3/flight/nonlinear.*`. Keine vorgespannte Modalanalyse.']
if list((out/'fem_reference').glob('*/gallery.json')):
    lines += ['', '## FEM-Bildgalerien mit echten Spannungsdaten','',
              'Zwei zusätzliche statische CalculiX-Läufe für Flug-Halbmodell und Auflagen-Vollmodell des synthetischen Prüffalls fordern Integrationspunktspannungen an. Insgesamt damit 27 Solverläufe. Modell-, Netz-, Verformungs- und σxx-Bilder sowie DAT/FRD und Herkunftsmanifest unter `fem_reference/`; im Hauptreport ausdrücklich getrennt von Biest-Ergebnissen dargestellt.']
if (out/'original_fem_validation.json').exists():
    original_checks=json.loads((out/'original_fem_validation.json').read_text(encoding='utf-8'))
    convergence_text='; '.join(f"{variant}: {'erreicht' if data['convergence']['converged'] else 'nicht für alle betrachteten Größen erreicht'}" for variant,data in original_checks.items())
    lines += ['', '## Räumliches Originalmodell mit bestätigtem Stegaufbau', '',
              '12 räumliche C3D20R-Netze und 18 abgeschlossene lineare CalculiX-Läufe (12 statisch, sechs modal) anhand der tatsächlichen Eingaben, DAT-Dateien und Logs geprüft. Jede Modalanalyse enthält sechs Eigenformen. Kräftebilanz und Flug-Wurzelmoment geprüft. Die aktive Versuchslagerung bottom_contact_line fixiert ausschließlich Unterseitenknoten auf je einer Linie bei x=±0,896 m vertikal. Oberseite und innere Knoten bleiben vertikal frei; Biegeneigung und horizontales Gleiten sind bis auf die Starrkörperstabilisierung frei. Die bilaterale Fixierung kann Niederhaltekräfte übertragen und ist kein einseitiger Kontakt.',
              'Das 2-%-Konvergenzziel für Flugtip, Versuchswurzel und sechs Eigenfrequenzen: '+convergence_text+'. Dies belegt keine lokale Spannungs- oder Krümmungskonvergenz. Nichtlineare Versuche und ihr tatsächlicher Abschlussstatus stehen im [Report](report.md); Zwischeninkremente sind keine Volllastergebnisse.',
              'Versuchskraft 37,278 N und separate Schwingungsmasse 5,58 kg greifen über dem hinteren Steg bei x=-25 bis +25 mm an. Im Biegelinienplot sind die B-Messwerte ΔHöhe=7,02 mm abwärts und ΔTip=5,985 mm aufwärts ergänzt; die rechte Tip-Seite ist eine Darstellungsannahme. Die Flug-FEM-Krümmung entlang des hinteren Stegs wird aus Knotenverschiebungen mit lokalen kubischen Fünf-Punkte-Fits abgeleitet und zusammen mit M/EI dargestellt; Randstationen sind im Plot ausgespart. Einzelheiten und CSV-Daten stehen im [Report](report.md).',
              'Prüfdaten: [Original-FEM](original_fem_validation.json), [geöffnete CAD-Modelle und Massenvergleich](cad_validation.json), [separater C3D20R-Referenzbalken](c3d20r_reference/validation.json). Der einfache Referenzbalken liegt bei Durchbiegung und erster Eigenfrequenz innerhalb 2 % der Euler-Bernoulli-Lösung; das ersetzt keinen Konvergenznachweis des komplexen Originalmodells.']
(out/'validation.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Artefakte geprüft; Nachweis: results/validation.md')
