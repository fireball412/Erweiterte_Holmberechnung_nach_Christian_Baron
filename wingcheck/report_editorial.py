"""Editorial wording recovered from the project conversation of 18 October 2026.

Apply to generated Markdown so every report entry point uses the same wording.
Numerical results are still generated from the current model, never from chat logs.
"""
import json
import re
from pathlib import Path

def apply_report_wording(text):
    rules = json.loads(Path(__file__).with_name('report_wording.json').read_text(encoding='utf-8'))
    text = text.replace('Versuch und Eigenwerte bleiben', 'Laborversuch und Eigenwerte bleiben')
    for kind, old, new in rules:
        text = text.replace(old, new) if kind == 'literal' else re.sub(old, lambda match: new, text)
    text = text.replace('Auflagenversuch', 'Laborversuch').replace('Kontaktversuch', 'Laborversuch mit Kontakt')
    text = re.sub(r'(?<!Labor-)Biegeversuch', 'Labor-Biegeversuch', text)
    text = re.sub(r'(?<!Labor)Versuch', 'Laborversuch', text)
    text = re.sub(r'(?m)^- Altes Excel-I[^\n]*\n', '', text)
    text = re.sub(r'(?m)^### fem_sandwich_q20/([AB])/level_(\d+)/(flight|test)$',
                  lambda m: f"### Fall {m[1]} \u2013 Netzstufe {m[2]} \u2013 "+('Fluglastfall' if m[3]=='flight' else 'Laborversuch'), text)
    text = re.sub(r'(?m)^### fem_sandwich_q20/([AB])$', lambda m: '## FEM-Detailbilder \u2013 Fall '+m[1], text)
    notice = '**Hinweis zu den Berechnungen:** Die Berechnungen dokumentieren das beschriebene Modell und seine Annahmen. Sie ersetzen keinen gepr\u00fcften Festigkeits- oder Luftt\u00fcchtigkeitsnachweis.'
    if notice not in text:
        title, body = text.split('\n', 1)
        text = title+'\n\n'+notice+'\n'+body
    return text
