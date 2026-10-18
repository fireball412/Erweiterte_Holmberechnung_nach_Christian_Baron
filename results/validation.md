# Ausführungs- und Verifikationsnachweis

Stand: 18.10.2026. 33 physikalische/Import-/Postprocessing-/Schlauchmodell-/Lastverteilungs-/Auflager-/Krümmungs-Referenztests bestanden (`python -m pytest -q`); Python-Module kompilierbar.
Die Quelldatei ist unverändert (SHA-256 gegen Importinventur geprüft). Alle Bildpfade im Originalbericht existieren.

## Tatsächlicher synthetischer Integrationstest

**Keine Biest-/Excel-Ergebnisse.** Expliziter homogener I-Holm: Halbspannweite 0,15 m, Gurtbreite 0,02 m, Außenhöhe 0,02 m, zwei Lagen je 0,001 m je Gurt, Stegbreite 0,002 m, E=70 GPa, ν=0,3, ρ=2700 kg/m³. 20 N Gesamtfluglast, 1 kg Zentralmasse, Auflagen bei ±0,09 m. Endliche Auflagen-/Lastbreiten siehe Testskript.
Beide Varianten sind hier absichtlich identisch. Drei Netzstufen pro Variante und Lastfall; insgesamt 12 CAD-/Netzmodelle und 24 CalculiX-Läufe (je Statik und sechs Eigenformen). FCStd, STEP, Netze, Eingaben, Logs und echte DAT/FRD-Dateien unter `../benchmark_results/fem/`.

| Variante | größter Reaktionsrest [N] | Konvergenz aller 6 Eigenwerte und statischen Größen ≤2 % |
|---|---:|---|
| A | 7e-06 | False |
| B | 7e-06 | False |

Details: [synthetic_validation.json](synthetic_validation.json). Ein eventuell nicht erreichtes Konvergenzziel ist ein ausgewiesenes Testergebnis, kein ersetzter Solverwert.

## Originalmappe

Import, Zuordnung, Cache-Konsistenzprüfung und Rekonstruktion der Excel-Näherungen ausgeführt. Siehe [Report](report.md) und `../config.yaml`.
Die Balkenvarianten wurden mit dem ausdrücklich vorläufigen YAML-Annahmensatz gerechnet (angenommener Fertigungsplan, Excel-Auftrieb als Vergleichslast). Räumlicher Original-FEM-Status: ausgeführt. Bestätigte Stegannahmen sind im aktiven Schlauchmodell hinterlegt; Materialwerte und Taschenlänge bleiben Annahmen.

## Geometrisch nichtlineare Zusatzprüfung

Ein weiterer tatsächlicher CalculiX-NLGEOM-Lauf auf dem synthetischen feinsten Flugnetz ist abgeschlossen. Insgesamt damit 25 Solverläufe. Ergebnisdateien und Log unter `../benchmark_results/fem/A/level_3/flight/nonlinear.*`. Keine vorgespannte Modalanalyse.

## FEM-Bildgalerien mit echten Spannungsdaten

Zwei zusätzliche statische CalculiX-Läufe für Flug-Halbmodell und Auflagen-Vollmodell des synthetischen Prüffalls fordern Integrationspunktspannungen an. Insgesamt damit 27 Solverläufe. Modell-, Netz-, Verformungs- und σxx-Bilder sowie DAT/FRD und Herkunftsmanifest unter `fem_reference/`; im Hauptreport ausdrücklich getrennt von Biest-Ergebnissen dargestellt.

## Räumliches Originalmodell mit bestätigtem Stegaufbau

12 räumliche C3D20R-Netze und 18 abgeschlossene lineare CalculiX-Läufe (12 statisch, sechs modal) anhand der tatsächlichen Eingaben, DAT-Dateien und Logs geprüft. Jede Modalanalyse enthält sechs Eigenformen. Kräftebilanz und Flug-Wurzelmoment geprüft. Die aktive Versuchslagerung bottom_contact_line fixiert ausschließlich Unterseitenknoten auf je einer Linie bei x=±0,896 m vertikal. Oberseite und innere Knoten bleiben vertikal frei; Biegeneigung und horizontales Gleiten sind bis auf die Starrkörperstabilisierung frei. Die bilaterale Fixierung kann Niederhaltekräfte übertragen und ist kein einseitiger Kontakt.
Das 2-%-Konvergenzziel für Flugtip, Versuchswurzel und sechs Eigenfrequenzen: A: erreicht; B: erreicht. Dies belegt keine lokale Spannungs- oder Krümmungskonvergenz. Nichtlineare Versuche und ihr tatsächlicher Abschlussstatus stehen im [Report](report.md); Zwischeninkremente sind keine Volllastergebnisse.
Versuchskraft 37,278 N und separate Schwingungsmasse 5,58 kg greifen über dem hinteren Steg bei x=-25 bis +25 mm an. Im Biegelinienplot sind die B-Messwerte ΔHöhe=7,02 mm abwärts und ΔTip=5,985 mm aufwärts ergänzt; die rechte Tip-Seite ist eine Darstellungsannahme. Die Flug-FEM-Krümmung entlang des hinteren Stegs wird aus Knotenverschiebungen mit lokalen kubischen Fünf-Punkte-Fits abgeleitet und zusammen mit M/EI dargestellt; Randstationen sind im Plot ausgespart. Einzelheiten und CSV-Daten stehen im [Report](report.md).
Prüfdaten: [Original-FEM](original_fem_validation.json), [geöffnete CAD-Modelle und Massenvergleich](cad_validation.json), [separater C3D20R-Referenzbalken](c3d20r_reference/validation.json). Der einfache Referenzbalken liegt bei Durchbiegung und erster Eigenfrequenz innerhalb 2 % der Euler-Bernoulli-Lösung; das ersetzt keinen Konvergenznachweis des komplexen Originalmodells.
