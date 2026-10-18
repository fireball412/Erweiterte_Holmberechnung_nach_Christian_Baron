"""Reproduce the z-axis ring-down fit and update the measurement report section."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results'
SOURCE = ROOT / 'Acceleration (without g) 2026-10-18 10-31-02.zip'


def model(p, t):
    c, b, amplitude, decay, frequency, phase = p
    return c + b*t + amplitude*np.exp(-decay*t)*np.cos(2*np.pi*frequency*t+phase)


def fit(data, start, end):
    selected = (data[:, 0] >= start) & (data[:, 0] <= end)
    t, y = data[selected, 0]-start, data[selected, 3]
    candidates = [least_squares(lambda p: model(p, t)-y,
                  [-.04, 0, 1, .15, f, 0],
                  bounds=([-1, -.1, 0, 0, 3, -20], [1, .1, 3, 2, 7, 20]),
                  max_nfev=3000) for f in np.arange(3.2, 6.9, .1)]
    result = min(candidates, key=lambda r: np.sum(r.fun**2))
    p = result.x
    p[5] = (p[5]+np.pi) % (2*np.pi)-np.pi
    return t, y, p, float(1-np.sum(result.fun**2)/np.sum((y-y.mean())**2)), float(np.sqrt(np.mean(result.fun**2)))


def main():
    OUT.mkdir(exist_ok=True)
    with zipfile.ZipFile(SOURCE) as archive:
        raw = archive.read('Raw Data.csv')
        data = np.loadtxt(io.BytesIO(raw), delimiter=',', skiprows=1)
    assert np.isfinite(data).all() and np.all(np.diff(data[:, 0]) > 0)
    start, end = 2.5, float(data[-1, 0])
    t, y, p, r2, rmse = fit(data, start, end)
    c, b, amplitude, decay, fd, phase = p
    f0 = np.sqrt(fd**2+(decay/(2*np.pi))**2)
    zeta = decay/(2*np.pi*f0)
    windows = []
    for lo, hi in [(3., end), (2.5, 8.), (8., end), (3., 12.)]:
        _, _, q, score, error = fit(data, lo, hi)
        windows.append(dict(start_s=lo, end_s=hi, frequency_Hz=float(q[4]), decay_per_s=float(q[3]), R2=score, RMSE_m_s2=error))
    result = dict(source=SOURCE.name, sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  samples=len(data), fit_samples=len(t), start_s=start, end_s=end,
                  sample_rate_Hz=float(1/np.median(np.diff(data[:, 0]))),
                  model='c+b*tau+A*exp(-delta*tau)*cos(2*pi*fd*tau+phi); tau=t-start_s',
                  parameters=dict(zip(['c_m_s2','b_m_s3','A_m_s2','delta_per_s','fd_Hz','phi_rad'], map(float,p))),
                  undamped_frequency_Hz=float(f0), damping_ratio=float(zeta),
                  R2=r2, RMSE_m_s2=rmse, sensitivity=windows)
    (OUT/'phyphox_fit.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), constrained_layout=True)
    axes[0].plot(data[:,0], data[:,3], color='#235789', lw=.9, label='Messung z')
    axes[0].axvspan(start, end, color='#65a765', alpha=.13, label='Fitfenster')
    dense = np.linspace(0, end-start, 12000)
    axes[0].plot(dense+start, model(p,dense), color='#d1495b', lw=.85, label='Fit')
    envelope = amplitude*np.exp(-decay*dense)
    for sign in [-1, 1]:
        axes[0].plot(dense+start,c+b*dense+sign*envelope,'--',color='#333333',lw=1,
                     label='Exponentielle Hüllkurve' if sign==1 else None)
    axes[0].set_title(f'phyphox: abklingende z-Schwingung | f_d = {fd:.4f} Hz | δ = {decay:.4f} s⁻¹')
    axes[0].legend(ncol=4, fontsize=9)
    axes[1].plot(data[:,0], data[:,3], '.-', ms=3, lw=.8, label='Messung')
    axes[1].plot(dense+start,model(p,dense),color='#d1495b',lw=1.2,label='Fit')
    axes[1].set_xlim(3, 5); axes[1].set_title('Detail: Messpunkte und Fit (ungefilterte Daten)')
    axes[2].plot(t+start,y-model(p,t),lw=.7,color='#76528b')
    axes[2].set_title(f'Residuen im Fitfenster | R² = {r2:.4f} | RMSE = {rmse:.4f} m/s²')
    for ax in axes:
        ax.set_xlabel('Messzeit t [s]'); ax.set_ylabel('a_z [m/s²]'); ax.grid(alpha=.25)
    axes[2].set_ylabel('Messung − Fit [m/s²]')
    fig.savefig(OUT/'phyphox_decay.png', dpi=180)
    fig.savefig(OUT/'phyphox_decay.pdf')
    plt.close(fig)
    rows = '\n'.join(f"| {w['start_s']:.1f}–{w['end_s']:.2f} | {w['frequency_Hz']:.5f} | {w['decay_per_s']:.5f} |" for w in windows)
    section = f'''## Schwingungsmessung mit phyphox: z-Achse

### Kurzanleitung: Messung und CSV-Export

1. **Aufbau vorbereiten:** Holm wie im gewuenschten Versuch lagern und belasten. Smartphone fest und ohne Spiel am Messort befestigen; seine z-Achse (senkrecht zum Display) muss in Schwingungsrichtung zeigen. Messort, Lagerung, Belastung sowie Telefonmasse und Befestigung notieren, da diese die Eigenfrequenz beeinflussen.
2. **phyphox einstellen:** Das Experiment **"Beschleunigung ohne g" / "Acceleration (without g)"** oeffnen. Fuer diese Auswertung wird die z-Beschleunigung benoetigt. Vor jeder Wiederholung alte Messdaten loeschen bzw. eine neue Aufnahme beginnen.
3. **Ausschwingen aufnehmen:** Mit der Starttaste starten, etwa 2 s Ruhe aufzeichnen, den Holm leicht auslenken und loslassen oder kurz anregen. Anschliessend frei ausschwingen lassen, ohne Holm oder Telefon zu beruehren. Nach etwa 15-20 s Ausschwingzeit die Aufnahme stoppen. Zwei bis drei getrennte Messungen erleichtern die Kontrolle der Wiederholbarkeit.
4. **Als CSV exportieren:** Im Experimentmenue **"Daten exportieren" / "Export Data"** waehlen und **CSV mit Komma als Spaltentrenner und Dezimalpunkt** auswaehlen (englisch "CSV (Comma, decimal point)"). Ueber den Speichern-/Teilen-Dialog die Exportdatei auf dem Geraet sichern oder auf den Rechner Uebertragen; Menuebezeichnungen koennen je nach Betriebssystem abweichen.
5. **Datei verwenden:** phyphox buendelt die CSV-Dateien in einem ZIP-Archiv. ZIP entpacken und **`Raw Data.csv`** verwenden. Fuer die vorliegende Auswertung sind **`Time (s)`** und **`Linear Acceleration z (m/s^2)`** massgeblich; die Originaldatei mit allen Achsen unveraendert aufbewahren. Beim Tabellenimport Komma als Trennzeichen und Dezimalpunkt einstellen. Fuer den Abklingfit nur den freien Ausschwingabschnitt nach der Anregung auswaehlen.

Hinweise zum [Beschleunigungssensor ohne g](https://phyphox.org/docs/file-format/input/) und zum [CSV-/ZIP-Exportformat](https://phyphox.org/docs/file-format/): offizielle phyphox-Dokumentation. Die Schritte beschreiben eine neue Messung; der genaue Aufbau der vorhandenen Aufnahme ist im Export nicht dokumentiert.

### Auswertung der vorhandenen Messung

Quelle: [{SOURCE.name}](../{SOURCE.name.replace(' ', '%20')}); CSV `Raw Data.csv`, Spalte `Linear Acceleration z (m/s^2)`. Laut ZIP-Metadaten wurde am 18.10.2026 von 10:30:22 bis 10:30:39 Uhr (UTC+02:00) gemessen; der Dateiname bezeichnet den Exportzeitpunkt. {len(data)} Messpunkte von {data[0,0]:.5f} bis {end:.5f} s, Abtastrate etwa {result['sample_rate_Hz']:.2f} Hz. Ausgewertet wird die von phyphox exportierte lineare Beschleunigung ohne g; keine zusätzliche Filterung oder Resampling.

Die stärkere Anregung liegt bei etwa 2,1 s. Für den freien Ausschwingvorgang wird das Fenster **{start:.2f} bis {end:.5f} s** verwendet ({len(t)} Punkte); die Anregung und der unmittelbar folgende Übergang bleiben außerhalb des Fits. Nichtlinearer Kleinste-Quadrate-Fit eines exponentiell gedämpften Sinus mit linearem Basislinienanteil; mehrere Frequenzstartwerte zwischen 3,2 und 6,8 Hz vermeiden eine ungünstige lokale Lösung.

Mit **τ = t − {start:.2f} s**, τ in Sekunden und a_z in m/s² lautet die Fitfunktion:

```text
a_z(t) = {c:.7f} {b:+.7f}·τ
         + {amplitude:.7f}·exp(−{decay:.7f}·τ)·cos(2π·{fd:.7f}·τ {phase:+.7f})
```

| Größe | Ergebnis |
|---|---:|
| Gemessene gedämpfte Eigenfrequenz f_d | {fd:.5f} Hz |
| Periodendauer 1/f_d | {1/fd:.5f} s |
| Abklingkonstante δ | {decay:.5f} s⁻¹ |
| Amplituden-Zeitkonstante 1/δ | {1/decay:.3f} s |
| Dämpfungsgrad ζ | {zeta:.5f} ({100*zeta:.3f} %) |
| Ungedämpfte Eigenfrequenz f_0 (Einmodenmodell) | {f0:.5f} Hz |
| Bestimmtheitsmaß R² | {r2:.5f} |
| Residuen-RMSE | {rmse:.5f} m/s² |

Dabei gelten f_0 = √(f_d² + (δ/2π)²) und ζ = δ/(2πf_0). Die Hüllkurven des Beschleunigungsfits sind c + bτ ± A·exp(−δτ). Die Amplitude A ist eine Beschleunigung, keine Auslenkung des Holms.

![Abklingende z-Schwingung mit Fit, Hüllkurve, Detail und Residuen](phyphox_decay.png)

**Fitstabilität:** Zusätzliche Zeitfenster liefern folgende Werte:

| Messzeitfenster [s] | f_d [Hz] | δ [s⁻¹] |
|---|---:|---:|
{rows}

Die Frequenz steigt im späteren Fenster leicht an; auch die Abklingrate hängt vom Fenster ab. Der konstante Einmodenfit ist daher eine Näherung. Als praktische Angabe ergibt sich **eine dominante Eigenfrequenz von rund {fd:.2f} Hz**; die zusätzlichen Fenster sind eine Sensitivitätsprüfung und kein statistisches Konfidenzintervall. Die vielen Nachkommastellen dokumentieren die numerische Anpassung, nicht die Messgenauigkeit. Systematische Residuen können unter anderem durch weitere Schwingungsanteile, amplitudenabhängiges Verhalten oder die Sensorverarbeitung entstehen; die einzelne Messung trennt diese Ursachen nicht.

**Einordnung zum Rechenmodell:** Dies ist die dominante z-Schwingung des gemessenen Aufbaus. Messort, Telefonbefestigung und Zusatzmasse, Lagerung sowie Belastungszustand sind im Export nicht dokumentiert. Die Zuordnung zu einer bestimmten berechneten Eigenform und ein direkter Modellabgleich bleiben deshalb offen; die Modellfrequenzen wurden nicht an diese Messung angepasst.

Reproduzierbar mit `.venv/Scripts/python.exe tests/analyze_phyphox.py`. [Fitparameter und Fenstervergleich](phyphox_fit.json), [Plot als PDF](phyphox_decay.pdf). SHA-256 des ZIP: `{result['sha256']}`.
'''
    (OUT/'phyphox_measurement.md').write_text(section, encoding='utf-8')
    report = OUT/'report.md'
    if report.exists():
        text = report.read_text(encoding='utf-8')
        heading = '## Schwingungsmessung mit phyphox: z-Achse'
        if heading in text:
            before, rest = text.split(heading, 1)
            next_heading = rest.find('\n## ')
            text = before + (rest[next_heading+1:] if next_heading >= 0 else '')
        marker = '## FEM-Anhänge'
        if marker not in text:
            text = text.replace('**Geänderte Spitzengeometrie:**', marker+'\n\n**Geänderte Spitzengeometrie:**', 1)
        text = text.replace(marker, section.strip()+'\n\n'+marker, 1) if marker in text else text.rstrip()+'\n\n'+section
        report.write_text(text, encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
