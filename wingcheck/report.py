"""German report, explicit execution state and relative artifact paths."""
import csv
from pathlib import Path
import shutil
from .excel import dump_json
from .report_editorial import apply_report_wording
from .figure_notes import beam_notes,fem_notes,reference_notes,explanation


def fmt(v):
    return f'{v:.6g}' if isinstance(v,(int,float)) else str(v)


def write_report(out,model,cfg,analysis,fem,diagnostics,images,source):
    sandwich_mode = cfg['geometry'].get('sandwich',{}).get('enabled',False)
    if sandwich_mode:
        sketch=Path(__file__).resolve().parents[1]/'docs'/'stegannahmen.png'
        if sketch.exists():
            (out/'images').mkdir(exist_ok=True)
            shutil.copy2(sketch,out/'images'/'stegannahmen.png')
            shutil.copy2(sketch.with_suffix('.svg'),out/'images'/'stegannahmen.svg')
            if 'stegannahmen' not in images:images=list(images)+['stegannahmen']
    rows = []
    for variant,r in analysis['variants'].items():
        rows.append({'variant':variant,**r['summary']})
    dump_json(out/'summary.json',{'beam':rows,'fem':fem,'reconstructed_excel':model['reconstructed']})
    fem_rows=[dict(variant=variant,**row) for variant,v in fem.get('variants',{}).items() for row in v.get('meshes',[])]
    if fem_rows:
        keys=list(dict.fromkeys(k for row in fem_rows for k in row))
        with (out/'fem_summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(fem_rows)
    if rows:
        with (out/'summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w = csv.DictWriter(f,fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
    else:
        (out/'summary.csv').write_text('variant,status\nA,fehlende Pflichtdaten\nB,fehlende Pflichtdaten\n',encoding='utf-8-sig')
    p = model['parameters']
    lines = ['# Holmberechnung – Import, Nachrechnung und Ausführungsnachweis','',
             '## Aufgabenstellung und Modellumfang','',
             'Vergleich A (diskreter Excel-Lagenplan) gegen B (durchgehende jeweilige Wurzellagen). '+model['scope']+'.',
             'x=0 an der Wurzel, x=L an der Halbflügelspitze. Gesamtspannweite '+fmt(2*model['half_span'])+' m; Halbspannweite '+fmt(model['half_span'])+' m.',
             '', '## Tatsächlich ausgeführte Schritte','',
             '| Schritt | Status |','|---|---|',
             '| Excel-Inventur, Formeltokens, Cache-/Konsistenzprüfung | ausgeführt, schreibgeschützt |',
             '| Rekonstruktion einfacher Excel-Näherungen | ausgeführt; keine Neuberechnung der Arbeitsmappe |',
             f"| Varianten A/B: Statik, Masse, Eigenwertlösung | {analysis['status']} |",
             f"| Räumliche FreeCAD/CalculiX-FEM | {fem['status']} |",'',
             'Originaldatei: `'+str(source['path'])+'`  ', 'SHA-256: `'+source['sha256']+'`',
             '', 'Vollständige Daten: [Inventur](excel_inventory.json), [SI-Modell](normalized_input.json), [Konfiguration](used_config.yaml), [Diagnose](diagnostics.json), [Ergebnisse](summary.json).',
             '', '## Fehlende Daten und Annahmen','']
    lines += ['- '+s for s in model['missing']+model['warnings']]
    lines += ['- '+s for s in fem.get('reasons',[]) if s not in model['missing']]
    if cfg['flight']['distribution']=='chord_proportional':
        from .loads import chord_resultants
        load=chord_resultants(model,cfg)
        lines += ['', '## Aktive Fluglast: tiefenproportional', '',
            'q(x)=F_halb · c(x) / ∫₀ᴸc(s)ds. c(x) ist die Flächentiefe aus der Excel-Flächengeometrie, nicht die Gurtbreite. Angenommen wird ein örtlich konstanter Auftriebsbeiwert. Der Excel-Gesamtauftrieb bleibt erhalten; die früher verwendete Gleichlast ist jetzt nur noch eine Referenz.', '',
            'In der 3D-FEM wird diese Streckenlast durch einen äquivalenten vertikalen Gurtflächendruck proportional zu c(x)/b_Gurt(x) auf konsistente Knotenkräfte abgebildet. Die Gurtbreite dient nur der Lastübertragung auf das vorhandene Holmnetz. Das ist keine aerodynamische Druckverteilung auf einer mitmodellierten Flügelschale. Kraftsumme und erstes Lastmoment werden gegen die tiefenproportionale Sollverteilung geprüft.', '',
            'Lastschwerpunkt und Soll-Wurzelmoment unten beziehen sich auf die unverformte Referenzgeometrie. Im nichtlinearen Vergleich bleiben die daraus erzeugten vertikalen Knotenkräfte konstant; die Flächentiefe oder der Auftrieb werden während der Verformung nicht aerodynamisch neu berechnet. Veränderte Hebelarme sind deshalb von der initialen Lastmomentprüfung zu unterscheiden.', '',
            f"Halbflügelfläche {load['half_area_m2']:.6g} m²; Kraft je Halbflügel {load['force_N']:.6g} N; Lastschwerpunkt x={load['resultant_x_m']:.6g} m; Wurzelmoment {load['moment_Nm']:.6g} N·m. q(0)={load['root_q_N_m']:.6g} N/m; q(L)={load['tip_q_N_m']:.6g} N/m.", '',
            '| x [m] | Flächentiefe [mm] | q(x) [N/m] | Excel-Quelle |', '|---|---:|---:|---|']
        lines += [f"| {p['x']:.6g} | {p['chord']*1000:.6g} | {p['chord']*load['pressure_coefficient_N_m2']:.6g} | {p['source']} |" for p in model['planform']]
        lines += ['', 'Dies ist eine geometrisch gewichtete Lastannahme, keine Lösung der realen 3D-Auftriebsverteilung. Der zentrale Biegeversuch und die unbelastete Modalanalyse werden durch diese Änderung nicht verändert.']
    lines += ['', 'Fehlende Eingaben werden nicht automatisch ersetzt. Explizite Annahmen aus der verwendeten YAML sind als vorläufig markiert; Beispiele in `examples/material.example.yaml` werden niemals automatisch eingelesen.',
              'Die E1-Angabe stammt aus der ausgewählten Excel-Materialzeile. Ob sie den tatsächlich ausgehärteten Verbund beschreibt, muss bestätigt werden. Festigkeits-/Beulnachweise und Flugsicherheitsfreigabe sind nicht Gegenstand dieser Rechnung.',
              '', '## Excel-Inventur und Mapping','', '| Blatt | belegte Zeilen | Spalten |','|---|---:|---:|']
    lines += [f"| {s['name']} | {s['rows']} | {s['columns']} |" for s in source['sheets']]
    lines += ['', 'Alle belegten Werte, Kommentare, Formelergebnisse und verfügbare Formeltokens stehen in der Inventur. BIFF-Formeltexte sind diagnostisch: xlrd kann Klammern uneindeutig darstellen; Tokens bleiben als verlustfreie Referenz erhalten. Fehlende, Excel-fehlerhafte und durch unabhängige Beziehungen auffällige Caches werden gemeldet. Keine vollständige Excel-Formelauswertung; keine LibreOffice-Neuberechnung ausgeführt.',
              '', '| Parameter | SI-Wert | Originalwert/-einheit | interne Einheit | Blatt/Zelle | Herkunft / Überschreibung |', '|---|---:|---|---|---|---|']
    for item in model['provenance']:
        detail = item['origin']
        for o in item['overrides']:
            detail += f"; {o['origin']}: {o['previous']} → {o['new']} ({o['reason']})"
        lines.append(f"| {item['parameter']} | {fmt(item['value'])} | {fmt(item['original_value'])} {item['original_unit']} | {item['internal_unit']} | {item['source']} | {detail} |")
    lines += ['', '## Rekonstruierte Excel-Näherungen','',
              'Die Vorlage bestimmt Auftrieb aus ca, Geschwindigkeit und Fläche; G ist in N angegeben, keine Masse in kg. n=A/G wird geprüft. Die in Excel verwendete konstante Streckenlast integriert zu A/2. Eine explizite Unterscheidung Grenz-/Bruchlast ist nicht vorhanden und muss bestätigt werden.',
              'Die Höhen H (Profil), h (unter Beplankung), h1 (lichte Steghöhe) und t (theoretische Gurtdicke) sind zu unterscheiden. Das Standardmapping verwendet h als Holm-Außenhöhe. Fertigungslagen verschieben Gurtschwerpunkte gegenüber der theoretischen Excel-Geometrie.',
              '', 'Für konstantes EI an der Wurzel gelten:',
              '- Gleichlast-Kragträger: δ=qL⁴/(8EI), M₀=qL²/2. Die ausgeschriebene Excel-Näherung M₀L²/(2EI) überschätzt diesen Referenzfall um Faktor 2.',
              '- Gelenkiger Auflagenversuch, zentrale Kraft: δ₀=F(2pL)³/(48EI). Freie Überhänge ohne Eigengewicht sind krümmungsfrei, aber wegen der Auflagerneigung nicht verschiebungsfrei.',
              '- Zentraler Feder-Masse-Ersatz: k=6EI/(pL)³ und f=√(k/m)/(2π). Strukturmasse fehlt in dieser einfachen Excel-Näherung.',
              '', '| Größe | neu rekonstruierter Wert | Bedeutung |','|---|---:|---|']
    meanings = {'uniform_q_N_m':'konstante Halbflügel-Streckenlast N/m','root_moment_Nm':'Wurzelmoment Nm',
        'flight_uniform_root_EI_m':'korrekte Gleichlastformel, m; konstantes korrigiertes Excel-Wurzel-EI',
        'excel_written_flight_root_EI_m':'ausgeschriebene Excel-Näherung, m',
        'test_root_constant_EI_m':'Wurzelabsenkung, m; konstantes korrigiertes Excel-Wurzel-EI',
        'test_tip_constant_EI_m':'Spitzenhebung relativ Auflagen, m',
        'spring_frequency_excel_mass_Hz':'Feder-Masse-Näherung mit C170, Hz'}
    lines += [f'| {k} | {fmt(v)} | {meanings[k]} |' for k,v in model['reconstructed'].items()]
    if cfg['flight']['distribution']=='chord_proportional':
        lines += ['', '**Die vorstehenden Flugwerte rekonstruieren ausschließlich die frühere Excel-Gleichlastnäherung. Sie sind nicht die aktive tiefenproportionale Last oder deren Wurzelmoment.**','']
    lines += ['', 'Diese Werte verwenden das theoretische Excel-Wurzel-EI und ersetzen keine Rechnung der Fertigungsvarianten. C144 ist die statische Laständerungsmasse; C170 wird separat als gesamte mitbewegte Zentralmasse interpretiert. Ihre physische Bedeutung muss am Aufbau bestätigt werden.',
              '', '| gespeicherte Excel-/Messgröße | Wert in SI |','|---|---:|']
    lines += [f'| {k} | {fmt(v)} |' for k,v in p.items() if k.startswith('excel_') or k.startswith('measured_')]
    lines += ['', '## Berechnungsverfahren und Randbedingungen','',
        'A verwendet abschnittsweise konstante ganze Lagenzahlen [xᵢ,xᵢ₊₁); der Spitzenwert 0 beschreibt das Ende, kein endliches gurtloses Intervall. Breiten und Höhen werden linear interpoliert. B übernimmt nur die oberen/unteren Wurzellagen; restliche Geometrie bleibt gleich.',
        '1D-Balkenquerschnitt: zₙ=Σ(EAz)/Σ(EA), EI=ΣE[Iₑ+A(z−zₙ)²]. Orthotrope Nachgiebigkeitsmatrix ist symmetrisch (νji=νij Ej/Ei) und muss positiv definit sein. Der Balken setzt ebene vertikale Biegung voraus und erfasst keine Biege-Torsionskopplung; diese Einschränkung gilt nicht als Vorgabe für die räumliche FEM. Ein Verbinder wird ohne bestätigten Schub-/Momentenübertragungsmechanismus nicht addiert.',
        'Flug: M(x)=∫ₓᴸq(s)(s−x)ds, κ=M/EI, θ=∫κdx und w=∫θdx. Krümmung wird innerhalb jedes diskreten Lagenintervalls einseitig mit Gaußquadratur integriert; kein Glätten der Steifigkeitssprünge. Zusätzlich eine an allen Geometrie- und Lagensprüngen segmentierte numerische Balkenlösung mit Gaußintegration. Positive Fluglast bedeutet positive Durchbiegung.',
        'Versuch: vollständiger Flügel, freie Überhänge und zentrale Last; die Wurzel bleibt beweglich. Der 1D-Balken verwendet zwei vertikale Punktauflager bei ±pL (oder expliziten Koordinaten). Die räumliche Lagerung wird separat durch test.fem_support_model festgelegt und im FEM-Abschnitt beschrieben. Bei bottom_contact_line werden nur die Unterseitenknoten auf einer Linie je Auflager vertikal fixiert; die konfigurierte 20-mm-Breite dient dann ausschließlich der Netzunterteilung.',
        'Dynamik: Euler-Bernoulli-Hermite-Elemente, konsistente verteilte Masse und separate Zentralmasse am beweglichen Wurzelknoten; optional Rotationsträgheit. Vollmodell erfasst symmetrische und antisymmetrische Biegemoden. Zentralmasse ist fest mitbewegend; lose aufgelegte Massen können Kontakt verlieren. Statische Versuchsmasse und dynamische Gesamtmasse werden nicht addiert.',
        'Rayleigh: statische Einheitslast-Biegelinie als zulässige Ansatzfunktion; ω²=φᵀKφ/(φᵀMφ). Effektive Masse m_eff=φᵀMφ/φ(0)². Der mit derselben Ansatzfunktion gebildete Feder-Masse-Wert ist mathematisch identisch und kein unabhängiger Genauigkeitsnachweis. Numerische Eigenwerte sind keine geschlossene Formel.',
        'Schub: optionaler Fluganteil ∫V/(κGA)dx wird separat ausgegeben. Versuch und Eigenwerte bleiben Euler-Bernoulli; keine behauptete Timoshenko-Validierung.',
        '', '## Variantenvergleich','']
    if rows:
        lines += ['| Größe | A | B | (B−A)/A |','|---|---:|---:|---:|']
        aa,bb = [r['summary'] for r in analysis['variants'].values()]
        for key in ['half_spar_mass_kg','flight_tip_m','flight_integral_tip_m','test_root_m','test_right_tip_m','rayleigh_Hz']:
            av,bv = aa[key],bb[key]
            lines.append(f'| {key} | {fmt(av)} | {fmt(bv)} | {100*(bv-av)/av:.3g} % |')
        lines += ['', '| Eigenform | A [Hz] / Symmetrie | B [Hz] / Symmetrie |','|---|---|---|']
        for j,(fa,fb) in enumerate(zip(aa['frequencies_Hz'],bb['frequencies_Hz'])):
            lines.append(f"| {j+1} | {fa:.5g} / {aa['mode_symmetry'][j]} | {fb:.5g} / {bb['mode_symmetry'][j]} |")
        lines += ['', '**Kontrolle der Kräfte und Ergebnisse der linearen Balkenrechnung**', '',
                  'Die Auflagerkräfte im Laborversuch und die Reaktionen an der Wurzel im Fluglastfall werden gegen die aufgebrachte Last geprüft. Der Reaktionsrest ist die verbleibende numerische Abweichung vom Kräftegleichgewicht.', '',
                  '| Fall | Reaktionsrest Labor [N] | Gegenkraft Flug [N] | Gegenmoment Flug [N·m] | Flug-Spitzenweg [mm] |',
                  '|---|---:|---:|---:|---:|']
        for variant,r in analysis['variants'].items():
            result = r['summary']
            lines += [f"| {variant} | {result['test_reaction_residual_N']:.4g} | {abs(result['flight_reaction_N']):.5g} | {abs(result['flight_reaction_Nm']):.5g} | {result['flight_tip_m']*1000:.4g} |"]
        lines += ['', 'Fall B biegt sich weniger, weil die UD-Lagenzahl an der Wurzel bis zur Flügelspitze beibehalten wird.']
        if any(r['summary']['large_deflection'] for r in analysis['variants'].values()):
            lines += ['', '**Einordnung:** Die Flugverformungen sind im Verhältnis zur Halbspannweite groß. Die lineare Rechnung berücksichtigt nicht, wie die veränderte Form das Tragverhalten beeinflusst. Die Werte sind deshalb zusammen mit der geometrisch nichtlinearen FEM und deren Abschlussstatus zu beurteilen.']
        lines += ['', '**Materialmengen je Halbflügel**', '',
                  'Die Volumina bilden zusammen mit den Materialdichten die Grundlage der Massenberechnung. Die CFK-Wandbereiche um jeden Depronkern sind zusammengefasst.', '',
                  '| Holmteil | Fall A [cm³] | Fall B [cm³] |', '|---|---:|---:|']
        groups = [('Oberer UD-Gurt', 'top'), ('Unterer UD-Gurt', 'bottom'),
                  ('Hinterer Depronkern', 'rear_core'), ('CFK-Wände um den hinteren Kern', 'rear_'),
                  ('Vorderer Depronkern', 'front_core'), ('CFK-Wände um den vorderen Kern', 'front_')]
        for label, key in groups:
            values = []
            for variant in ('A','B'):
                volumes = analysis['variants'][variant]['summary']['material_volume_half_m3']
                volume = sum(v for k,v in volumes.items() if k.startswith(key) and not k.endswith('_core')) if key.endswith('_') else volumes.get(key,0)
                values.append(volume*1e6)
            lines += [f'| {label} | {values[0]:.2f} | {values[1]:.2f} |']
    else:
        lines += ['Keine Variantenwerte: Pflichtdaten fehlen. Damit sind Massen, Eigenformen und Durchbiegungen der Fertigungsvarianten nicht belastbar berechenbar.']
    lines += ['', '## Räumliche FEM und Netzkonvergenz','',
        ('Aktives Biest-Schlauchmodell: keilförmige UD-Gurte mit gerader hinterer Kante, hinterer 5-mm-Depronkern bis x=1,40 m; Gurtbreite max(Excel-Keil, 6 mm) mit Knick bei x≈1,28618 m, vorderer bis x=0,70 m. Hintere Kernmitte y=3 mm; Verbindertasche 35 mm breit. Taschenlänge 0,14 m als Excel-basierte Annahme; vorderer Steg danach linear zur Keilkontur geführt. Idealer Verbund. Der Verbinder und seine Tasche werden als Lage-/Freiraumvorgabe dokumentiert, ohne unbelegten Steifigkeitsbeitrag. Jeder CFK-Schlauch besitzt zwei senkrechte Wände und obere/untere Abschnitte, jeweils max(R(x), 0,10 mm) als vorläufige Mindestwanddicke, in zwei halbe ±45°-Teilschichten zerlegt. Orientierungen beziehen sich auf die globale Spannweitenrichtung; die kleine lokale Schräglage des vorderen Stegs wird in der Faserorientierung vernachlässigt. Depron isotrop mit E=20 MPa, ν=0,30, ρ=40 kg/m³; CFK-Werte vorläufig. Der eigene strukturierte 3D-Netzgenerator erzeugt quadratische C3D20R-Hexaeder statt Gmsh-Tetraeder. Alle Materialgrenzen innerhalb eines Intervalls teilen Knoten. Nichtpassende Knoten an Lagensprüngen werden über quadratische Flächen-Verschiebungsinterpolation verbunden, ohne starre Lastspider; zusätzliche lokale Diskretisierungssteifigkeit ist durch Netzverfeinerung zu prüfen. Vorläufe mit linearen C3D8I-Elementen wurden wegen auffälliger lokaler Niedrigfrequenzformen verworfen und werden nicht als validierte Ergebnisse gezeigt.' if sandwich_mode else
        'FreeCAD baut pro Lagenintervall massive, linear veränderliche Gurte und einen zentralen rechteckigen Steg. Gmsh erzeugt quadratische Tetraeder; CalculiX nutzt C3D10 mit orthotropem UD in globaler x-Faserrichtung.'),
        ('CAD in mm; der strukturierte Netzgenerator arbeitet direkt in m. Solver: m, N, kg, s, Pa; Dichte kg/m³. E-Modul N/mm² aus Excel wird mit 10⁶ in Pa umgerechnet. UD-Gurtfaser entlang x; Schlauchfasern ±45° zur Spannweitenrichtung in der jeweiligen Wandebene. Ausgegebene σxx sind globale Längsspannungen, in der linearen Rechnung im UD-Gurt zugleich Fasernormalspannungen; bei großen nichtlinearen Rotationen ist diese Gleichsetzung nicht allgemein zulässig.' if sandwich_mode else 'CAD in mm; Gmsh-Knoten werden vor Solverexport mit 0,001 in m umgerechnet. Solver: m, N, kg, s, Pa; Dichte kg/m³. E-Modul N/mm² aus Excel wird mit 10⁶ in Pa umgerechnet.'),
        'Lasten werden über die Elementflächen in konsistente Knotenkräfte umgerechnet; kein starrer Lastspider. Die Auflagerbedingungen entsprechen dem konfigurierten Lagermodell; beim aktuellen Modell werden nur die unteren Kontaktlinien vertikal festgehalten. Drei weitere skalare Bedingungen verhindern Starrkörperbewegungen in der Ebene. Die zusätzliche Zentralmasse verteilt sich über das Lastband.',
        'Mindestens drei Netzfaktoren; relative Änderung zwischen den letzten zwei Stufen bezogen auf feinste Stufe. Räumliche Modalsuche liefert auch Quer-/Torsionsmoden; deren erste Frequenz darf erst nach Prüfung der Form einer vertikalen Balkenmode zugeordnet werden. Nichtlineare Statik wird separat gerechnet; Modalanalyse ist unbelastet linear, keine vorgespannte Analyse.',
        '', f"Status: **{fem['status']}**."]
    for variant,v in fem.get('variants',{}).items():
        lines += ['',f'### FEM {variant}', '', '| Netzfaktor | Flugtip [m] | Testwurzel [m] | f₁ [Hz] |','|---|---:|---:|---:|']
        lines += [f"| {r['level']} | {r['flight_tip_m']:.6g} | {r['test_root_m']:.6g} | {r['frequency_Hz']:.6g} |" for r in v['meshes']]
        conv=v['convergence'];changes=conv.get('relative_changes',{})
        lines += ['', '**Netzkonvergenz:** '+conv.get('reason','nicht ausgewertet')+'.']
        if changes:
            lines += ['Änderung der letzten beiden Stufen, bezogen auf die feinste: '+', '.join(f'{key}: {100*changes[key]:.3g} %' for key in ['flight_tip_m','test_root_m','frequency_Hz'] if key in changes)+'.']
            if changes.get('modes_by_index'):
                lines += ['Eigenfrequenzen 1–6 nach Index: '+', '.join(f'{100*x:.3g} %' for x in changes['modes_by_index'])+'. Ein Modenwechsel wird damit nicht ausgeschlossen.']
        for row in v['meshes']:
            for error in row.get('errors',[]):
                lines += ['',f"**Netz {row['level']}: nicht erfolgreich abgeschlossen:** {error}"]
        last = v['meshes'][-1]
        if 'flight_mesh_mass_kg' in last:
            lines += ['',f"FEM-Strukturmasse: Halbflügel {last['flight_mesh_mass_kg']:.6g} kg; Vollflügel {last.get('test_mesh_mass_kg',0):.6g} kg. Enthält Gurte, CFK-Schläuche und Depron, keine Flügelschale und keine zentrale Zusatzmasse."]
        if 'test_averaged_support_reactions' in last:
            supports=last['test_averaged_support_reactions']
            lines += ['', 'Reaktionen der drei gemittelten Vertikalbedingungen (aus dem globalen Gleichgewicht rekonstruiert): '+', '.join(f'{name}: {value:.5g} N' for name,value in zip(supports['labels'],supports['reactions_N']))+'.']
            if supports['tensile_reaction_required']:
                lines += ['**Kontaktgrenze:** Das bilaterale Lagerungsmodell erfordert eine Zug-/Niederhaltereaktion. Lose Unterlagen können diese nicht aufbringen. Für eine physische Nachbildung des Auflagenversuchs müssen Kontaktlage bzw. Lastübertragung über die reale Flügelschale ergänzt werden. Die vorliegenden Werte gelten für die ausdrücklich idealisierten Gelenk-/Mittelungsbedingungen, nicht für einen nachgewiesenen einseitigen Kontaktversuch.']
        if 'frequencies_Hz' in last:
            lines += ['', '| 3D-Eigenform | Frequenz [Hz] | Symmetrie | Anteil vertikaler Verschiebung |','|---|---:|---|---:|']
            for j,f in enumerate(last['frequencies_Hz']):
                sym=last.get('mode_symmetry',[])
                fractions=last.get('vertical_fractions',[])
                lines += [f"| {j+1} | {f:.6g} | {sym[j] if j<len(sym) else 'nicht klassifiziert'} | {fractions[j]*100 if j<len(fractions) else 0:.3g} % |"]
            lines += ['Die Zuordnung erfolgt aus den räumlichen Eigenformen; Tabellenindizes sind kein Beweis einer Übereinstimmung mit den reinen 1D-Biegemoden.']
        nonlinear_rows=[r for r in v['meshes'] if 'flight_nonlinear_m' in r]
        if nonlinear_rows:
            nl=nonlinear_rows[-1]
            lines += ['',f"Nichtlinearer Flugvergleich auf Netzstufe {nl['level']}: zusätzlicher qualitativer Vergleich, **kein netzkonvergierter nichtlinearer Nachweis**."]
            lines += ['', '| Statik | linear [m] | geometrisch nichtlinear [m] | Abweichung relativ linear |', '|---|---:|---:|---:|']
            for case,linear in [('flight','flight_tip_m')]:
                av,bv = nl[linear],nl[case+'_nonlinear_m']
                lines += [f'| {case} | {av:.6g} | {bv:.6g} | {100*(bv-av)/av:.4g} % |']
        if variant in analysis['variants']:
            beam = analysis['variants'][variant]['summary']
            finest = v['meshes'][-1]
            lines += ['', '| Größe | Balken | räumliche FEM (feinstes Netz) | (FEM−Balken)/Balken |', '|---|---:|---:|---:|']
            for key in ['flight_tip_m','test_root_m']:
                av,bv = beam[key],finest[key]
                lines += [f'| {key} | {av:.6g} | {bv:.6g} | {100*(bv-av)/av:.4g} % |']
            lines += ['Frequenzvergleich erfordert Eigenformzuordnung. Die ausgewählte 3D-Form hat überwiegend vertikale Verschiebungen; Biege-Torsions-Mischformen sind möglich und müssen anhand der Bilder geprüft werden. Die räumlichen Auflagerbedingungen unterscheiden sich vom Punktauflager des Balkens.']
    lines += ['', '## Bilder','']
    for name in images:
        notes=beam_notes(name,model,cfg,analysis)
        lines += ['### '+notes[0], '']
        lines += [f'![{name}](images/{name}.png)','']
        lines += explanation(notes)
        if name=='loads' and analysis.get('fem_rear_curvature'):
            lines += ['[Krümmungsdaten A als CSV](flight_rear_curvature_A.csv) · [Krümmungsdaten B als CSV](flight_rear_curvature_B.csv).','']
        if name=='stegannahmen':
            lines += ['[Skizze als verlustfrei vergrößerbare SVG öffnen](images/stegannahmen.svg).','']
    if fem.get('complete') and fem.get('variants'):
        lines += ['', '## Messwerte und aktuelle FEM-Ergebnisse im Laborversuch', '']
        p=model['parameters']
        lines += ['', f"**Messpunkte im Biegelinienplot (B-Modell):** Excel D146, ΔHöhe={p['measured_root']*1000:.6g} mm als Absenkung an x=0; Excel D147, ΔTip={p['measured_tip']*1000:.6g} mm als Hebung am Tip. Die Darstellungsseite +L ist eine YAML-Annahme, keine in Excel dokumentierte Messseite. Die genaue Messposition über der Flächentiefe ist nicht dokumentiert; der FEM-Querschnittsmittelwert und die Wurzelauswertung im Taschenband sind nicht automatisch identisch mit dem Messpunkt. Die Werte sind kein automatischer Nachweis identischer Material-, Geometrie- und Lagerannahmen.", '']
        lines += ['| Variante | FEM Wurzel, Taschenmittel [mm] | FEM Tip links, oberer Gurt [mm] | FEM Tip rechts, oberer Gurt [mm] |', '|---|---:|---:|---:|']
        for variant,record in fem['variants'].items():
            last=record['meshes'][-1]
            lines += [f"| {variant} | {last['test_root_m']*1000:.6g} | {last['test_left_tip_m']*1000:.6g} | {last['test_right_tip_m']*1000:.6g} |"]
    lines += ['', '## FEM-Anhänge', '', 'Die wesentlichen Ergebnisse und Vergleiche stehen im Hauptteil oben. Der folgende Anhang dokumentiert die einzelnen FEM-Netzstufen, Verformungen, Spannungen und Schwingungsformen sowie die technischen Prüfungen und die Reproduzierbarkeit der Berechnung.', '']
    fem_folder = out/(('fem_sandwich_q20' if cfg['fem'].get('sandwich_element')=='C3D20R' else 'fem_sandwich') if sandwich_mode else 'fem')
    if sandwich_mode:
        lines += ['', '**Geänderte Spitzengeometrie:** Hinterer Steg bis 1,40 m; Gurt mindestens 6 mm. Die CFK-Mindestwanddicke 0,10 mm bleibt eine Annahme. Die reale Flügelschale ist nicht enthalten. Frühere Messwerte dienen nur bei identischem tatsächlichem Bauzustand zur Validierung dieser neuen Variante.','']
        lines += ['Flug-Spitzenverschiebung bezeichnet den belasteten oberen Gurt; der untere Gurt wird in der JSON/CSV getrennt ausgewiesen. Die Versuchswurzel wird als Auswertegröße weiterhin über die obere Gurtfläche im 35-mm-Taschenbereich bei x=0 gemittelt; dies ist kein festgelegter Messpunkt. Versuchskraft und Schwingungsmasse werden bei load_region=rear_web auf der oberen Gurtfläche unmittelbar über dem hinteren Steg verteilt: x=-25 bis +25 mm, quer dazu über den 5-mm-Depronkern einschließlich beider CFK-Schlauchwände, Mittelpunkt y=3 mm zur hinteren Gurtkante. Die statische Gesamtkraft bleibt 37,278 N; die gesonderte Schwingungsmasse bleibt 5,58 kg und erzeugt keine zusätzliche statische Gewichtslast. Nichtlineare Statik wird für den großen Fluglastfall versucht; beim kleinen Auflagenversuch bleibt die Statik linear. [FEM-Ergebnistabelle als CSV](fem_summary.csv).','']
        if cfg['test'].get('fem_support_model')=='bottom_contact_line':
            lines += ['**Versuchslagerung auf unteren Kontaktlinien:** Bei x=±0,896 m gilt u_z=0 ausschließlich für die Knoten auf der unteren Holmoberfläche, über deren Breite. Oberseite und innere Knoten werden nicht vertikal festgehalten. Benachbarte Querschnitte bleiben vertikal frei; die Biegeneigung und das horizontale Gleiten werden bis auf drei skalare Bedingungen zur Starrkörperstabilisierung zugelassen. Die Außenflügel setzen die Auflagerneigung fort. Die 20-mm-Unterteilung um die Auflage ist nur eine Netzunterteilung, keine fixierte Kontaktfläche. Diese bilaterale Kontaktlinie verhindert Abheben und kann Niederhaltekräfte übertragen; sie ist kein einseitiger Kontakt mit Abrollen und kein Nachweis realer Kontaktpressungen. Die reale Flügelschale fehlt weiterhin.','']
        elif cfg['test'].get('fem_support_model')=='fixed_vertical_section':
            lines += ['**Versuchslagerung mit freier Biegeneigung:** Nur in den beiden Querschnittsebenen bei x=±0,896 m gilt für sämtliche Strukturknoten u_z=0. Die Nachbarquerschnitte sind vertikal frei; die Biegeneigung kann sich einstellen und der Außenflügel setzt die Neigung fort. Die Verschiebung in Spannweitenrichtung bleibt bis auf die Starrkörperstabilisierung frei. Querschnittstorsion an der Auflage ist unterdrückt. Drei zusätzliche skalare Bedingungen verhindern Starrkörperbewegungen in der Flügelebene. Dies ist ein bilaterales ideales Querschnittslager mit möglichen Niederhaltekräften, kein einseitiger Kontakt und keine flächige Einspannung. Die 20-mm-Unterteilung um die Auflage bleibt nur im Netz erhalten. Die reale Flügelschale ist nicht enthalten.','']
        elif cfg['test'].get('fem_support_model')=='fixed_vertical_band':
            lines += ['**Versuchslagerung nach Nutzerfestlegung:** In beiden 20-mm-Auflagerbändern bei x=±0,896 m gilt für sämtliche Strukturknoten u_z=0, über die gesamte Holmbreite und -höhe. Drei zusätzliche skalare Bedingungen in der Flügelebene verhindern Starrkörperbewegungen. Die Bänder verhindern Abheben und Absinken und schränken Querschnittstorsion sowie die Biegerotation innerhalb ihrer endlichen Breite ein. Dies ist eine bilaterale vertikale Führung mit möglichen Niederhaltekräften, kein einseitiger Kontakt. Die Flügelschale wird dadurch nicht ausdrücklich modelliert. Der 1D-Balken behält seine idealen Punktauflager; Unterschiede zum 3D-Versuch sind deshalb auch durch die Lageridealisation bedingt.','']
        else:
            lines += ['Die drei gemittelten Vertikalbedingungen der Auflagenbänder unterdrücken Starrkörperbewegungen, lassen aber die Rotation in Spannweitenrichtung frei. Reaktionskräfte werden aus den ursprünglichen Flächenknoten zurückgewonnen.','']
    last_parent=None
    for path in sorted(fem_folder.rglob('*.png')) if fem_folder.exists() and fem.get('variants') else []:
        relative=path.relative_to(fem_folder)
        variant_record=fem['variants'].get(relative.parts[0])
        if not variant_record:continue
        if len(relative.parts)>2 and relative.parts[1].startswith('level_'):
            level=int(relative.parts[1].split('_')[-1])
            row=next((r for r in variant_record['meshes'] if r['level']==level),None)
            if row is None or not all(k in row for k in ['flight_tip_m','test_root_m','frequency_Hz']):continue
        if path.parent!=last_parent:
            lines += ['', '### '+path.parent.relative_to(out).as_posix(),'']
            last_parent=path.parent
        notes=fem_notes(path,out,fem) if sandwich_mode else (
            path.stem+' – '+path.parent.relative_to(out).as_posix(),
            'Vorhandenes Bild des separaten C3D10-Adapters; Achsen und Farbskala stehen im Bild. Modell, Netz, Verformung, Spannung und normierte Eigenformen stellen unterschiedliche Größen dar.',
            'Dies ist nicht das aktuelle Depron-/CFK-Schlauchmodell. Ergebnisse gelten nur für die oben genannten Geometrien, Materialien und Lagerbedingungen; örtliche Spitzen benötigen eine eigene Netzprüfung.')
        lines += ['**'+notes[0]+'**', '', f'![{notes[0]}]({path.relative_to(out).as_posix()})','']
        lines += explanation(notes)
    if not fem.get('variants'):
        lines += ['Es liegen keine vollständig abgeschlossenen räumlichen Variantenläufe vor; Status/Fehler stehen oben. Vorhandene Zwischenbilder stammen nur aus tatsächlich ausgeführten Schritten. Keine Balkenbilder werden als FEM ausgegeben.']
    galleries = sorted((out/'fem_reference').glob('*/gallery.json'))
    if galleries:
        lines += ['', '## FEM-Bilder des synthetischen Prüffalls – keine Biest-Ergebnisse','',
            '**Diese Modelle, Netze und Solverergebnisse gehören ausschließlich zum synthetischen Software-Prüffall. Sie sind kein FEM-Nachweis der Excel-Holmauslegung und kein A/B-Vergleich des Biest-Holms.**',
            'Gezeigt wird der vorhandene homogene I-Holm-Prüffall (L=0,15 m je Halbflügel, E=70 GPa, ν=0,3, ρ=2700 kg/m³) auf seiner feinsten vorhandenen Netzstufe. Die Statik wurde für die Spannungsanforderung erneut mit CalculiX gerechnet. Das 2-%-Konvergenzziel des Auflagenversuchs war noch nicht erreicht; insbesondere Spannungen an Last- und Lagerstellen sind netzabhängig.',
            'Modellbilder zeigen die parametrischen Körper aus den tatsächlichen CAD-Eingaben; Netzbilder zeigen die zugehörigen quadratischen Tetraeder. Verformungsbilder überlagern das unverformte Netz; Farbskala und Vergrößerungsfaktor sind getrennt angegeben.',
            'Spannungsbilder zeigen globale Längsspannung σxx in MPa, positiv bei Zug und negativ bei Druck. x entspricht der UD-Gurtfaserrichtung; im ±45°-Schlauch ist σxx keine lokale Faserspannung. Dargestellt werden Mittelwerte der echten Integrationspunktspannungen innerhalb jedes Elements, ohne Glättung über Materialgrenzen. Die Farbskala enthält daher nicht zwingend die Integrationspunktspitze. Eine Spannungsdarstellung ist kein CFK-Festigkeitsnachweis.']
        for manifest_path in galleries:
            manifest = __import__('json').loads(manifest_path.read_text(encoding='utf-8'))
            lines += ['', '### '+manifest['label'],'',
                f"{manifest['nodes']} Knoten, {manifest['elements']} C3D10-Elemente; max. reale Verschiebung {manifest['max_displacement_m']*1000:.5g} mm. Max. |σxx| an Integrationspunkten: {manifest['max_abs_sigma_xx_integration_point_Pa']/1e6:.5g} MPa.",
                f"[Solverdaten und Herkunft]({manifest_path.relative_to(out).as_posix()}); [CalculiX-Ergebnisdatei]({(manifest_path.parent/manifest['solver_dat']).relative_to(out).as_posix()})."]
            for item in manifest['images']:
                relative = (manifest_path.parent/item['file']).relative_to(out).as_posix()
                lines += ['', '**'+item['caption']+'**','',f"![Synthetischer FEM-Prüffall: {item['caption']}]({relative})"]
                lines += explanation(reference_notes(item['file'],manifest))
    lines += ['', '## Anhang', '', '## Versionen und Reproduzierbarkeit','', '```json', __import__('json').dumps(diagnostics,ensure_ascii=False,indent=2),'```',
        '', '## Offizielle technische Quellen','',
        '- [CalculiX 2.22 Handbuch](https://www.dhondt.de/ccx_2.22.pdf): C3D10, C3D20R, *ELASTIC / ENGINEERING CONSTANTS, *ORIENTATION, *SOLID SECTION, *EQUATION, *FREQUENCY, *MASS, *NODE PRINT und *EL PRINT.',
        '- [FreeCAD Part-Scripting](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Topological_data_scripting.md): Part-Geometrie und Export.',
        '- [Gmsh-Handbuch](https://gmsh.info/doc/texinfo/gmsh.html): STEP-Import, MSH2, quadratische Tetraeder und Knotenreihenfolge.',
        '', 'Quelle der Excel-Auslegung: Christian Baron, 11/2013; Bearbeitungen und Kommentare der gelieferten Arbeitsmappe bleiben unverändert.']
    if (out/'validation.md').exists():
        lines += ['', '## Separater Software-Prüfnachweis','', '[Referenztests und tatsächlich ausgeführte synthetische Solverläufe](validation.md). Diese Ergebnisse gehören nicht zur gelieferten Excel-Holmauslegung.']
    if (out/'beam_convergence.json').exists():
        lines += ['', '## Numerische Balkenkonvergenz','', '[Verdopplung der Balkenelemente](beam_convergence.json): relative Änderungen der statischen Durchbiegungen und der ersten sechs Eigenfrequenzen bezogen auf das verfeinerte Modell dokumentiert. Dies prüft die Diskretisierung, nicht die Richtigkeit der Material-/Fertigungsannahmen.']
    if (out/'c3d20r_reference'/'validation.json').exists():
        reference=__import__('json').loads((out/'c3d20r_reference'/'validation.json').read_text(encoding='utf-8'))
        lines += ['', '## Unabhängiger einfacher C3D20R-Referenzfall','',
            'Ein separater homogener 3D-Kragträger wurde tatsächlich mit CalculiX gerechnet und mit geschlossenen Balkenformeln verglichen. Dieser synthetische Referenzfall prüft Elementexport, Einheiten, Statik und Dynamik; er bestätigt keine Genauigkeit des komplexen Biest-Modells.',
            f"Abweichung der Spitzendurchbiegung: {reference['relative_deviation']*100:.3g} %; Abweichung der ersten Eigenfrequenz: {reference.get('frequency_relative_deviation',0)*100:.3g} %.",
            '[Eingaben und tatsächliche Referenzergebnisse](c3d20r_reference/validation.json).']
    if (out/'cad_validation.json').exists():
        lines += ['', '## CAD-/Netz-Konsistenz','', '[Erneut geöffnete CAD-Dateien, gültige Volumenkörper und Vergleich der CAD-/Netzmassen](cad_validation.json).']
    if (out/'original_fem_validation.json').exists():
        lines += ['', '[Prüfung der tatsächlichen Original-FEM-Dateien und Reaktionsgleichgewichte](original_fem_validation.json).']
    measurement = out/'phyphox_measurement.md'
    if measurement.exists():
        appendix_index = lines.index('## FEM-Anhänge')
        lines[appendix_index:appendix_index] = [measurement.read_text(encoding='utf-8').strip(), '']
    (out/'report.md').write_text(apply_report_wording('\n'.join(lines)+'\n'),encoding='utf-8')
