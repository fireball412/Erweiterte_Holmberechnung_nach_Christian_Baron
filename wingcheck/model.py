"""Validated SI input model; no cell addresses in the calculation core."""
from dataclasses import dataclass, asdict
import numpy as np
from .excel import convert, UNITS


@dataclass
class Station:
    x: float
    width_top: float
    width_bottom: float
    height: float
    clear_height: float
    theoretical_thickness: float
    plies_top: int
    plies_bottom: int
    web_required: float
    source: str


def material_compliance(m):
    required = ['E1','E2','E3','G12','G13','G23','nu12','nu13','nu23','density']
    missing = [k for k in required if m.get(k) is None]
    if missing:
        raise ValueError('Fehlende Materialwerte: '+', '.join(missing))
    if any(not np.isfinite(float(m[k])) for k in required):
        raise ValueError('Nichtendliche Materialwerte')
    if any(m[k] <= 0 for k in ['E1','E2','E3','G12','G13','G23','density']):
        raise ValueError('E, G und Dichte müssen positiv sein')
    e1,e2,e3 = [m[k] for k in ['E1','E2','E3']]
    # Reciprocal minor Poisson ratios are defined by symmetric compliance.
    S = np.diag([1/e1,1/e2,1/e3,1/m['G23'],1/m['G13'],1/m['G12']])
    S[0,1] = S[1,0] = -m['nu12']/e1
    S[0,2] = S[2,0] = -m['nu13']/e1
    S[1,2] = S[2,1] = -m['nu23']/e2
    np.linalg.cholesky(S)
    return S


def normalize(book, cfg, cli_overrides=None):
    values, provenance, warnings = {}, [], list(book.inventory()['warnings'])
    for name, spec in cfg['mapping']['parameters'].items():
        raw,sheet,cell = book.resolve(spec)
        unit = spec['unit']
        v = convert(raw,unit)
        item = {'parameter':name,'value':v,'original_value':raw,'original_unit':unit,
                'internal_unit':UNITS[unit][1], 'source':f'{sheet}!{cell}',
                'origin':'Excel-Cache' if book.cells[(sheet,cell)].get('cached') else 'Excel-Eingabe',
                'overrides':[]}
        for origin, overrides in [('Konfiguration',cfg.get('overrides',{})), ('CLI',cli_overrides or {})]:
            if name in overrides:
                override = overrides[name]
                if not isinstance(override,dict):
                    override = {'value':override,'unit':unit}
                v = convert(override['value'],override.get('unit',unit))
                if UNITS[override.get('unit',unit)][1] != UNITS[unit][1]:
                    raise ValueError(f'Unverträgliche Override-Einheit für {name}')
                item['overrides'].append({'origin':origin,'previous':item['value'],'new':v,
                                          'reason':override.get('reason','explizite Überschreibung')})
                item.update(value=v,origin=origin)
        values[name] = v
        provenance.append(item)
    unknown = (set(cfg.get('overrides',{})) | set(cli_overrides or {}))-set(values)
    if unknown:
        raise ValueError(f'Unbekannte Overrides: {sorted(unknown)}')
    spec, stations = cfg['mapping']['stations'], []
    sheet = cfg['mapping']['sheet']
    for row in range(spec['first_row'],spec['last_row']+1):
        v = {name:book.get(sheet,f'{col}{row}') for name,col in spec.items() if name not in ['first_row','last_row']}
        for name,raw in v.items():
            unit = '1' if name.startswith('plies') else 'mm'
            provenance.append({'parameter':f'stations[{row}].{name}', 'value':convert(raw,unit),
                'original_value':raw,'original_unit':unit,'internal_unit':UNITS[unit][1],
                'source':f'{sheet}!{spec[name]}{row}','origin':'Excel-Auslegung/Cache','overrides':[]})
        for k in ['plies_top','plies_bottom']:
            if v[k] < 0 or int(v[k]) != v[k]:
                raise ValueError(f'Keine ganzzahlige Fertigungslagenzahl: {sheet}!{spec[k]}{row}')
        s = Station(**{k:(int(z) if k.startswith('plies') else z*.001) for k,z in v.items()},
                    source=f'{sheet}!Zeile {row}')
        if stations and s.x <= stations[-1].x:
            raise ValueError('Stationspositionen müssen eindeutig und streng steigend sein')
        if min(s.width_top,s.width_bottom,s.height) <= 0:
            raise ValueError('Ungültige Geometrie')
        if cfg['geometry']['height_definition']=='outer' and not np.isclose(s.height,s.clear_height+2*s.theoretical_thickness,rtol=1e-5):
            warnings.append(f'Inkonsistente Außen-/Licht-/Gurthöhen: {s.source}')
        stations.append(s)
    L = values['span']/2
    if L <= 0 or not np.isclose(stations[0].x,0) or not np.isclose(stations[-1].x,L):
        raise ValueError('Stationen müssen von 0 bis zur halben Gesamtspannweite reichen')
    minimum=cfg['geometry'].get('minimum_cap_width_m')
    if minimum is not None:
        if minimum<=0:raise ValueError('Mindestgurtbreite muss positiv sein')
        # Preserve the exact original linear taper by inserting each crossing
        # before clipping station widths. The Excel source/provenance stays raw.
        raw=stations[:];crossings=set()
        minima={'width_top':minimum,'width_bottom':minimum}
        wall_min=cfg['geometry'].get('minimum_sleeve_wall_m')
        if wall_min is not None:
            if wall_min<=0:raise ValueError('Mindestwanddicke muss positiv sein')
            minima['web_required']=wall_min
        for a,b in zip(raw[:-1],raw[1:]):
            for key,floor in minima.items():
                av,bv=getattr(a,key),getattr(b,key)
                if (av-floor)*(bv-floor)<0:
                    crossings.add(a.x+(floor-av)*(b.x-a.x)/(bv-av))
        for x in sorted(crossings):
            a,b=next((a,b) for a,b in zip(raw[:-1],raw[1:]) if a.x<x<b.x)
            fraction=(x-a.x)/(b.x-a.x)
            vals={key:(getattr(a,key)+(getattr(b,key)-getattr(a,key))*fraction) for key in ['width_top','width_bottom','height','clear_height','theoretical_thickness','web_required']}
            stations.append(Station(x=x,plies_top=a.plies_top,plies_bottom=a.plies_bottom,source='YAML-Mindestbreite: eingefügter Keilknick',**vals))
        stations.sort(key=lambda s:s.x)
        for s in stations:
            for key,floor in minima.items():setattr(s,key,max(getattr(s,key),floor))
        warnings.append(f'Nutzergeometrie: Gurtbreiten max(Excel-Keil, {minimum*1000:g} mm); Excel-Datei unverändert. Eingefügte Knickstationen übernehmen die Lagen des ursprünglichen Intervalls.')
        if wall_min is not None:warnings.append(f'ANNAHME: CFK-Schlauchwand max(Excel R, {wall_min*1000:g} mm), damit der durchgehende Steg an der Spitze nicht auf null Wanddicke ausläuft.')
    if not 0 < values['support_fraction'] < 1:
        raise ValueError('Auflagenanteil muss zwischen 0 und 1 liegen')
    if not np.isclose(values['total_lift']/values['weight'],values['load_factor'],rtol=1e-5):
        warnings.append('Inkonsistenter Cache: Auftrieb/Gewicht != Lastvielfaches')
    # Independent reconstruction, not formula evaluation.
    EI = values['E1']*values.get('excel_I_new',0)
    recon = {}
    if EI > 0:
        q = values['total_lift']/2/L
        a = values['support_fraction']*L
        F = values['test_mass']*cfg['test']['gravity']
        recon = {'uniform_q_N_m':q,'root_moment_Nm':q*L**2/2,
                 'flight_uniform_root_EI_m':q*L**4/(8*EI),
                 'excel_written_flight_root_EI_m':q*L**4/(4*EI),
                 'test_root_constant_EI_m':F*(2*a)**3/(48*EI),
                 'test_tip_constant_EI_m':F*a*a*(L-a)/(4*EI),
                 'spring_frequency_excel_mass_Hz':np.sqrt(6*EI/a**3/values['modal_mass'])/(2*np.pi)}
        if 'excel_test_root' in values and not np.isclose(recon['test_root_constant_EI_m'],values['excel_test_root'],rtol=.01):
            warnings.append('Excel-Versuchscache weicht von F*S³/(48EI) ab')
        warnings.append('Excel-Flugnäherung M0*L²/(2EI) ist doppelt so groß wie die korrekte Gleichlast-Kragträgerformel q*L⁴/(8EI).')
        if values.get('excel_I_old',0) > 10*values['excel_I_new']:
            warnings.append('Altes Excel-I ist größenordnungsmäßig größer als korrigiertes I; alter Formelzweig nicht als Referenz verwenden.')
    missing = []
    geo = cfg['geometry']
    if geo['step_rule']!='right':
        raise ValueError('Nur explizite rechtsseitige Lagenintervalle werden unterstützt')
    if not geo.get('ply_thickness_m'):
        missing.append('geometry.ply_thickness_m: ausgehärtete Lagendicke fehlt')
    if not geo.get('manufacturing_plan_confirmed'):
        if cfg['analysis'].get('allow_provisional',False) and cfg['material'].get('provisional'):
            warnings.append('VORLÄUFIG: Excel-Auslegungsplan als Fertigungsplan angenommen; tatsächliche Fertigung NICHT bestätigt.')
        else:
            missing.append('geometry.manufacturing_plan_confirmed: diskreten Excel-Auslegungsplan als tatsächlichen Fertigungsplan bestätigen')
    if cfg['flight']['load_kind']=='comparison' and cfg['analysis'].get('allow_provisional',False) and cfg['material'].get('provisional'):
        warnings.append('VORLÄUFIG: unveränderter Excel-Auftrieb ist eine Vergleichslast, keine bestätigte Grenz-/Bruchlast; kein Sicherheitsfaktor angewendet.')
    elif cfg['flight']['load_kind'] not in ['limit','ultimate']:
        missing.append('flight.load_kind: maximalen Excel-Auftrieb als Grenz- oder Bruchlast einordnen')
    mat = {**cfg['material'],'E1':values['E1']}
    try:
        material_compliance(mat)
    except (ValueError,np.linalg.LinAlgError) as exc:
        missing.append(str(exc))
    if geo['web']['enabled']:
        for k in ['thickness_m','E_Pa','G_Pa','density_kg_m3']:
            if not geo['web'].get(k) or geo['web'][k] <= 0:
                missing.append('geometry.web.'+k)
    elif not cfg['geometry'].get('sandwich',{}).get('enabled'):
        warnings.append('Steg nicht bestätigt: Gurt-EI setzt idealen Schubverbund voraus; räumliche FEM gesperrt.')
    else:
        warnings.append('Bestätigtes Schlauchmodell: zwei Depronkerne, ±45°-CFK-Wände; Materialwerte bleiben Annahmen. Hinteres Stegende gemäß YAML; Flügelschale nicht enthalten.')
    if mat.get('provisional'):
        warnings.append('VORLÄUFIG: Materialkennwerte enthalten ausdrücklich bestätigte Beispielannahmen.')
    if cfg['geometry'].get('ply_thickness_m') is not None and cfg['geometry']['ply_thickness_m']<=0:
        raise ValueError('Ausgehärtete Lagendicke muss positiv sein')
    if any(values.get(k,0)<=0 for k in ['E1','total_lift','weight','modal_mass']):
        raise ValueError('E1, Auftrieb, Gewicht und dynamische Masse müssen positiv sein')
    if values['test_mass']<0 or cfg['test']['central_inertia_kg_m2']<0:
        raise ValueError('Negative Masse/Trägheit unzulässig')
    if any(cfg['geometry'][k]<0 for k in ['shell_EI_Nm2','shell_mass_kg_m','nonstructural_mass_kg_m']):
        raise ValueError('Zusätzliche Steifigkeit/Masse darf nicht negativ sein')
    if cfg['flight']['mass_relief'] and cfg['flight']['net_load']:
        raise ValueError('Nettolast darf nicht nochmals um Massenentlastung reduziert werden')
    if cfg['flight']['mass_relief'] and not np.isclose(values['total_lift']/values['weight'],values['load_factor'],rtol=1e-5):
        raise ValueError('Massenentlastung verlangt ein mit Auftrieb/Gewicht konsistentes Lastvielfaches')
    if not cfg['test']['modal_mass_is_total']:
        raise ValueError('modal_mass muss die gesamte bewegte Zentralmasse sein; Massenanteile vorher explizit summieren')
    planform=[]
    if cfg['flight']['distribution']=='chord_proportional':
        table=cfg['mapping'].get('planform')
        if not table:raise ValueError('mapping.planform fehlt für tiefenproportionale Last')
        distance=0.
        for row in range(table['first_row'],table['last_row']+1):
            depth=convert(book.get(sheet,f"{table['chord']}{row}"),table['unit'])
            segment=convert(book.get(sheet,f"{table['segment']}{row}"),table['unit'])
            if depth==0 and segment==0:continue
            if depth<=0 or segment<0:raise ValueError('Ungültige Flächentiefe/Abschnittslänge')
            if not planform:
                planform.append(dict(x=0.,chord=depth,source=f'{sheet}!{table["chord"]}{row}'))
            elif segment<=0:raise ValueError('Weitere Flächentiefenstation ohne positive Abschnittslänge')
            distance+=segment
            if distance>0:planform.append(dict(x=distance,chord=depth,source=f'{sheet}!{table["chord"]}{row}'))
        if len(planform)<2 or not np.isclose(planform[-1]['x'],L,rtol=0,atol=1e-10):
            raise ValueError('Flächentiefen müssen die gesamte Halbspannweite abdecken')
        warnings.append('Fluglast tiefenproportional aus separater Excel-Flächengeometrie; örtlich konstanter Auftriebsbeiwert als Annahme, keine berechnete 3D-Auftriebsverteilung.')
    return {'parameters':values,'stations':[asdict(s) for s in stations], 'half_span':L,'planform':planform,
            'material':mat,'provenance':provenance,'warnings':warnings,'missing':missing,
            'reconstructed':recon, 'scope':'Holm, keine vollständige Flügelsteifigkeit'}
