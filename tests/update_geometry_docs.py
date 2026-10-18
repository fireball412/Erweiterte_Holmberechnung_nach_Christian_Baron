"""Synchronize the accepted full-length-web drawing and model description."""
from pathlib import Path
import yaml

root=Path(__file__).resolve().parents[1]
p=root/'docs/stegannahmen.svg'
t=p.read_text(encoding='utf-8')
t=t.replace('1070,377 1070,380','994.8,365 1070,365 1070,380')
t=t.replace('L997.3,370.4','L1070,370.4')
t=t.replace('M997.3,357 L997.3,402','M994.8,350 L994.8,402')
t=t.replace('Stegende vorgeschlagen: x = 1,29 m','Gurt ab x ≈ 1,286 m konstant 6 mm')
t=t.replace('Hier b ≈ 5,83 mm; Kern + CFK passen.','Hinterer Steg durchgehend bis 1,40 m.')
t=t.replace('M995,316 L997.3,355','M995,316 L994.8,350')
t=t.replace('Gurt läuft ohne Steg bis x = 1,40 m weiter.','Gurt + hinterer Steg bis zur Flügelspitze.')
t=t.replace('Schlauch: ±45° zur lokalen Steglängsachse; ideal verklebt mit Kern und UD-Gurten.','Schlauch: ±45° zur Spannweite; ideal verklebt mit Kern und UD-Gurten.')
t=t.replace('Hinterer Steg endet bei 1,29 m; Gurtbreiten bleiben unverändert. Keine Mindestbreite von 6 mm.','Gurt: max(Excel-Keil, 6 mm); 5-mm-Depronkern unverändert bis zur Spitze.')
t=t.replace('Reine 5-mm-Breitengrenze bei x ≈ 1,309 m; Schlauch und gerade Steglage benötigen mehr Platz.','ANNAHME: CFK je Wand max(Excel R, 0,10 mm); keine Wanddicke null an der Spitze.')
p.write_text(t,encoding='utf-8')
p=root/'docs/stegannahmen.md'
p.write_text('''# Bestätigte Geometrie: durchgehender hinterer Steg

![Aktueller Stegaufbau](stegannahmen.svg)

Der Nutzer hat die Variante mit **mindestens 6 mm Gurtbreite und unverändert 5 mm breitem Depronkern** gewählt. Ober- und Untergurt folgen der ursprünglichen linearen Excel-Keilkontur bis zur 6-mm-Grenze bei x≈1,28618 m; danach bleibt ihre Breite bis x=1,40 m konstant 6 mm. Die hintere Gurtkante bleibt gerade. Die Excel-Datei bleibt unverändert; die Mindestbreite wird im SI-Modell angewendet und der Knick als zusätzliche Station eingefügt. Dabei werden die ursprünglichen diskreten Lagenintervalle erhalten.

Der hintere Steg verläuft durchgehend bis zur Flügelspitze. Seine Kernmitte bleibt y=3 mm, parallel zur hinteren Gurtkante. Kernbreite 5 mm; CFK-Schlauch geschlossen mit jeweils zwei senkrechten Wänden und oberem/unterem Abschnitt. Der vordere Steg endet weiter bei x=0,70 m, die Verbindertasche ist 35 mm breit. Ihre Länge von 0,14 m bleibt eine Annahme. Der Verbinder erhält keinen unbelegten zusätzlichen Steifigkeitsbeitrag.

**Zusätzliche Wanddickenannahme:** Weil Excel R an der Spitze auf null fällt, gilt nun je Schlauchwand max(Excel R(x), 0,10 mm). Das ist eine vorläufige Mindestdicke für die durchgehende Geometrie, keine gemessene Schlauchdicke. Der jeweilige Knick der Dickenfunktion wird ebenfalls als Station eingefügt. Die Schlauchaußenflächen passen mit Kernmitte y=3 mm unter den 6-mm-Gurt; kein seitlicher Überstand wird verwendet.

Gurtdicke: Variante A verwendet die diskreten Excel-Lagenzahlen; B die durchgehenden Wurzellagen. Die Schlauchaußenhöhe entspricht jeweils dem tatsächlichen lichten Abstand der Gurte. Der Kern ist um die oberen/unteren Schlauchdicken niedriger. Idealer Verbund; keine Kleberadien, Schälspannungs- oder Delaminationsnachweise.

Materialannahmen bleiben: Depron E=20 MPa, ν=0,30, ρ=40 kg/m³; vorläufige CFK-Lamina gemäß config.yaml; Schlauch in zwei ausgeglichenen ±45°-Teilschichten. Der kleine lokale Winkel des vorderen Stegs wird in der Faserorientierung vernachlässigt.

Flugstatik, Auflagenversuch und Eigenformen verwenden wieder die vollständigen 1,40 m Halbspannweite. Es gibt keinen Schnitt bei 1,29 m und keine Schnitt-Ersatzlast. Eine Flügelschale ist weiterhin nicht modelliert. Die neue Gurt-/Steggeometrie ist eine geänderte Variante gegenüber den archivierten Rechnungen; die bisherigen Messwerte dürfen nur bei tatsächlich übereinstimmendem Bauzustand als Validierung dienen.

Aktive Werte: [config.yaml](../config.yaml). Maschinenlesbare Dokumentation: [stegannahmen.yaml](stegannahmen.yaml). Modell-, Netz-, Verformungs- und Spannungsbilder entstehen aus den neuen Solverläufen; ältere Bilder befinden sich im archivierten Ergebnisordner.
''',encoding='utf-8')
p=root/'docs/stegannahmen.yaml';d=yaml.safe_load(p.read_text(encoding='utf-8'))
d['confirmed_by_user']['rear_web_end_rule']='Durchgehend bis zur Flügelspitze x=1.40 m'
d['confirmed_by_user']['minimum_cap_width_m']=.006
d['derived_geometry'].pop('width_5mm_crossing_x_m',None)
d['derived_geometry'].update(rear_web_extent_m=[0.,1.4],cap_width_at_rear_web_end_m=.006,wall_thickness_at_rear_web_end_m=.0001,width_6mm_crossing_x_m=1.2861788617886178)
d['unresolved_geometry'].update(cap_width_change='max(Excel-Keil, 6 mm), Nutzerentscheidung',rear_end_check='5-mm-Kern plus CFK innerhalb 6-mm-Gurt',rear_end_after_x_1_29='Hinterer Steg läuft bis 1.40 m durch',tip_wall_issue='ANNAHME: max(Excel R, 0.10 mm) je Schlauchwand')
d['proposed_assumptions']['minimum_sleeve_wall_m']=.0001
p.write_text(yaml.safe_dump(d,allow_unicode=True,sort_keys=False),encoding='utf-8')
for name in ['README.md','wingcheck/report.py']:
    p=root/name;t=p.read_text(encoding='utf-8')
    t=t.replace('Hinterer Steg bis 1,29 m','Hinterer Steg bis zur Spitze bei 1,40 m, Gurtbreite mindestens 6 mm')
    t=t.replace('hinterer 5-mm-Depronkern bis x=1,29 m','hinterer 5-mm-Depronkern bis x=1,40 m; Gurtbreite max(Excel-Keil, 6 mm) mit Knick bei x≈1,28618 m')
    t=t.replace('jeweils R(x), in zwei halbe','jeweils max(R(x), 0,10 mm) als vorläufige Mindestwanddicke, in zwei halbe')
    if name=='README.md' and '**Stegfreie Spitze:**' in t:
        start=t.index('**Stegfreie Spitze:**');end=t.index('\n\n',start)
        t=t[:start]+'**Durchgehender hinterer Steg:** Mindestens 6 mm Gurtbreite bei unverändertem Keilverlauf davor; 5-mm-Depronkern bis zur Spitze. Je CFK-Schlauchwand wird max(Excel R, 0,10 mm) als Annahme verwendet. Die Flügelschale fehlt weiterhin. Neue Rechnungen beziehen sich auf diesen geänderten Aufbau; frühere Messwerte bestätigen ihn nur bei identischer tatsächlicher Geometrie.'+t[end:]
    else:
        t=t.replace('**Stegfreier Spitzenbereich:** Nach x=1,29 m bestehen nur die beiden Gurte. Die reale Flügelschale ist nicht enthalten. Dort ist der ideale Gurtverbund der Balkenrechnung nicht gegeben; insbesondere Flug-Spitzenverschiebungen und lokale Moden dürfen nicht als vollständige Flügelantwort interpretiert werden.','**Geänderte Spitzengeometrie:** Hinterer Steg bis 1,40 m; Gurt mindestens 6 mm. Die CFK-Mindestwanddicke 0,10 mm bleibt eine Annahme. Die reale Flügelschale ist nicht enthalten. Frühere Messwerte dienen nur bei identischem tatsächlichem Bauzustand zur Validierung dieser neuen Variante.')
    p.write_text(t,encoding='utf-8')
print('Skizze und Geometriebeschreibungen aktualisiert.')
