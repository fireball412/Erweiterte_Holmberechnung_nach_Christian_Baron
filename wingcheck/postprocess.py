"""Parse actual CalculiX DAT tables. Missing output is an error, never a zero."""
import re
from pathlib import Path


def number(s):
    return float(s.replace('D','E').replace('d','e'))


def parse_dat(path):
    text = Path(path).read_text(errors='replace')
    data = {'frequencies':[],'displacements':{},'forces':{},'mode_shapes':[],'stresses':{}}
    current,table = None,None
    for line in text.splitlines():
        low = line.lower()
        if 'eigenvalue' in low and 'frequency' in low:
            table = 'frequencies'
            continue
        if table == 'frequencies' and ('real part' in low or 'rad/time' in low):
            continue
        if 'displacements (' in low:
            table = 'displacements'
            current = {}
            data[table] = current
            data['mode_shapes'].append(current)
            continue
        if 'forces (' in low:
            table = 'forces'
            current = {}
            data[table] = current
            continue
        if 'stresses (' in low:
            table = 'stresses'
            current = {}
            data[table] = current
            continue
        fields = line.split()
        if not fields or not fields[0].isdigit():
            if line.strip() and any(ch.isalpha() for ch in line) and not re.match(r'^\s*[0-9]',line):
                table = None
            continue
        try:
            if table == 'frequencies' and len(fields) >= 4:
                data['frequencies'].append(number(fields[3]))
            elif table in ['displacements','forces'] and len(fields) == 4:
                current[int(fields[0])] = [number(v) for v in fields[1:]]
            elif table == 'stresses' and len(fields) == 8:
                current.setdefault(int(fields[0]),[]).append([number(v) for v in fields[2:]])
        except ValueError:
            continue
    return data


def convergence(rows,tolerance):
    if len(rows) < 3:
        return {'converged':False,'reason':'Weniger als drei berechnete Netzstufen'}
    out = {}
    for key in ['flight_tip_m','test_root_m','frequency_Hz']:
        a,b = rows[-2][key],rows[-1][key]
        out[key] = abs(b-a)/abs(b) if b else None
    ok = all(v is not None and v <= tolerance for v in out.values())
    if 'frequencies_Hz' in rows[-1] and 'frequencies_Hz' in rows[-2]:
        out['modes_by_index'] = [abs(b-a)/abs(b) for a,b in zip(rows[-2]['frequencies_Hz'],rows[-1]['frequencies_Hz'])]
        ok = ok and all(v<=tolerance for v in out['modes_by_index'])
    return {'converged':ok,'relative_changes':out,'reference':'jeweils feinste Netzstufe',
            'tolerance':tolerance,'reason':'erreicht' if ok else 'Konvergenzziel NICHT erreicht'}
