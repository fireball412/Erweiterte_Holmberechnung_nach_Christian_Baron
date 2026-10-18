# wingcheck

## Lizenz und Herkunft

Der Programmcode steht unter der [MIT-Lizenz](https://opensource.org/license/mit). Der Bericht und die eigenen Abbildungen stehen unter [Creative Commons Namensnennung 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.de). Bei deren Weiterverwendung sind die Urheber zu nennen, die Lizenz zu verlinken und Änderungen kenntlich zu machen.

Die Excel-Datei `Holmberechnung_deutsch_korrigiert3_Biest.xls` stammt ursprünglich von Christian Baron und wird mit seiner Genehmigung veröffentlicht. Sie ist von den oben genannten Lizenzen ausgenommen; die Rechte an den ursprünglichen Inhalten verbleiben bei Christian Baron. Die Genehmigung zur Veröffentlichung beinhaltet keine darüber hinausgehende freie Lizenzierung der Excel-Datei.

Die Lizenzen externer Bibliotheken und Programme gelten unabhängig davon weiter.

**Hinweis zu den Berechnungen:** Die Berechnungen dokumentieren das beschriebene Modell und seine Annahmen. Sie ersetzen keinen geprüften Festigkeits- oder Lufttüchtigkeitsnachweis.

## Projektübersicht

Aktueller Rechenstand: `config.yaml` enthält den vom Nutzer bestätigten Depron-/CFK-Schlauchaufbau unter `geometry.sandwich`. Hinterer Steg bis zur Spitze bei 1,40 m, Gurtbreite mindestens 6 mm, vorderer bis 0,70 m, 5-mm-Kerne, 35-mm-Verbindertasche. `analysis.allow_provisional: true` erlaubt die Rechnung mit angenommenem Excel-Fertigungsplan und `flight.load_kind: comparison`, ohne eine Fertigungsbestätigung oder Grenzlastklassifikation zu behaupten. `material.provisional: true` kennzeichnet die angenommenen Materialwerte. Die räumliche Original-FEM ist aktiviert.

Ausführbares Python-Projekt zur schreibgeschützten Nachrechnung einer Excel-Holmauslegung. Quellmappe: Christian Baron (11/2013), gelieferte bearbeitete Fassung. Die Originaldatei wird nie geändert; Excel/VBA wird nicht gestartet.

## Installation (Windows / PowerShell)

```powershell
py -3 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Python >=3.9. FreeCAD mit Python-Modul, CalculiX und Gmsh sind für analytische Schritte optional. Die lokal gefundenen Programme sind bereits in `config.yaml` eingetragen. Bei anderer Installation deren absolute Pfade ändern. Offizielle Downloads: [FreeCAD](https://www.freecad.org/downloads.php), [CalculiX](https://www.dhondt.de/), [Gmsh](https://gmsh.info/).

## Befehle

```powershell
# Programme und Versionen prüfen
.venv/Scripts/python.exe -m wingcheck diagnose --config config.yaml

# Excel inventarisieren, Mapping und Cache prüfen
.venv/Scripts/python.exe -m wingcheck inspect --config config.yaml --output results

# Analytische und numerische Balkenrechnung, Bilder und Bericht
.venv/Scripts/python.exe -m wingcheck analytical --config config.yaml --output results

# Räumliche FEM mit mindestens drei Netzen (reale Pflichtdaten vorher ergänzen)
.venv/Scripts/python.exe -m wingcheck fem --config config.yaml --output results

# Gesamtreport einschließlich tatsächlicher FEM-Ausführung
.venv/Scripts/python.exe -m wingcheck --excel './Holmberechnung_deutsch_korrigiert3_Biest.xls' --config config.yaml --output results --with-fem

# Beispiel einer nachvollziehbaren CLI-Überschreibung (Originaleinheit des Mappings)
.venv/Scripts/python.exe -m wingcheck analytical --set total_lift=2000 --output results_override

# Physikalische Referenztests
.venv/Scripts/python.exe -m pytest -q
```

Exitcodes: 0 erfolgreich, 1 fehlerhafte Eingabe, 2 fehlende Pflichtdaten oder fehlgeschlagene FEM. Ein Bericht mit Status und Fehlstellen wird auch bei fehlenden Pflichtdaten erzeugt. `inspect` rechnet keine Varianten. Ohne `--with-fem` startet `report` keine externen Solver.

## Vor einer Variantenrechnung ergänzen

`config.yaml` enthält alle Parameter mit Einheiten und Erläuterungen. `null` bedeutet fehlend, **nicht Null**. Insbesondere ausgehärtete UD-Lagendicke, Verbunddichte und orthotrope Quer-/Schubwerte fehlen in der gelieferten Vorlage. Der Excel-Auslegungsplan muss als tatsächlicher Fertigungsplan bestätigt werden. Ein ausgewähltes Gelege-Flächengewicht ist keine ausgehärtete Lagendicke. Die Beispiele unter `examples/` sind explizit erfundene Demonstrationskennwerte und werden nicht automatisch übernommen; bei Einsatz `material.provisional: true` setzen.

Der maximale Excel-Auftrieb ist nicht ausdrücklich als Grenz- oder Bruchlast bezeichnet. `flight.load_kind` bestätigen; nur bei `ultimate` wird durch `safety_factor` dividiert. Nettolast und zusätzliche Massenentlastung gleichzeitig sind unzulässig. Die Vorlage verwendet G=30 N, nicht 30 kg; n≈72,36, Gesamtspannweite 2,8 m, Halbspannweite 1,4 m.

1D-Standardversuch: zwei Gelenkauflagen bei ±p·L, zentrale Kraft auf dem **beweglichen** Wurzelquerschnitt, freie Überhänge. Excel liefert p=0,64, statische Laständerung 3,8 kg und eine gesonderte Schwingungsmasse 5,58 kg. Letztere wird als gesamte mitbewegte Zentralmasse behandelt, nicht zusätzlich zur 3,8-kg-Last. `test.force_N` ändert nur die statische Kraft. Rotationsträgheit separat in kg·m². Modell einer fest mitbewegten Masse; lose Auflage/Kontakt ist kein automatisches Äquivalent.

Das aktive Schlauchmodell nutzt getrennte Depronkerne und jeweils zwei senkrechte sowie obere/untere CFK-Schlauchabschnitte. R aus Excel gilt nach Nutzerbestätigung je Wand; für die oberen/unteren Abschnitte wird ebenfalls R angenommen. Die ±45°-CFK-Anteile werden als zwei halbe orientierte Teilschichten abgebildet. Die hintere Kernmitte liegt bei y=3 mm zur geraden Gurtkante. Vor der 35-mm-Tasche liegt der vordere Steg; nach der mit 0,14 m angenommenen Taschenlänge wird er zur Keilkontur geführt. Versuchskraft (37,278 N) und separate Schwingungsmasse (5,58 kg) werden oben unmittelbar über dem hinteren Steg verteilt (`test.load_region: rear_web`): x=-25 bis +25 mm, quer über 5-mm-Kern samt Schlauchwänden, Mittelpunkt y=3 mm. Die Schwingungsmasse ist keine zusätzliche statische Last. Ideale Verklebung, kein zusätzlicher Verbinder-EI-Beitrag. Materialwerte bleiben Annahmen. Schub-, Klebe- und CFK-Versagen werden nicht nachgewiesen.

**Durchgehender hinterer Steg:** Mindestens 6 mm Gurtbreite bei unverändertem Keilverlauf davor; 5-mm-Depronkern bis zur Spitze. Je CFK-Schlauchwand wird max(Excel R, 0,10 mm) als Annahme verwendet. Die Flügelschale fehlt weiterhin. Neue Rechnungen beziehen sich auf diesen geänderten Aufbau; frühere Messwerte bestätigen ihn nur bei identischer tatsächlicher Geometrie.

Die aktuelle Versuchslagerung (`test.fem_support_model: bottom_contact_line`) hält nur die Unterseitenknoten auf je einer Kontaktlinie bei x=±0,896 m vertikal fest (u_z=0). Oberseite, innere Knoten und Nachbarquerschnitte bleiben vertikal frei. Biegeneigung und horizontales Gleiten sind bis auf drei skalare Bedingungen zur Starrkörperstabilisierung frei. Dies ist eine bilaterale ideale Kontaktlinie; sie kann Niederhaltekräfte übertragen und bildet weder einseitiges Abrollen noch Kontaktpressungen ab. `support_width_m: 0.020` dient nur der Netzunterteilung. Die Flügelschale fehlt weiterhin. Der 1D-Balken behält ideale Punktauflager. Der letzte vollständige Stand mit fixierten 20-mm-Bändern ist nur lokal archiviert und wird nicht mitveröffentlicht; die unterbrochene Querschnittslager-Rechnung im lokalen Archiv ist kein abgeschlossener Vergleichsfall.

Die Messpunkte im Biegelinienplot gehören zum B-Modell: Excel D146 (delta_Höhe=6,70 mm) wird als Wurzelabsenkung, D147 (delta_Tip=6,83 mm) als Spitzenhebung dargestellt. `test.measurements` dokumentiert Vorzeichen und die nur für die Darstellung angenommene rechte Tip-Seite. Excel enthält keine Seitenangabe oder genaue Messposition über der Flächentiefe. Die Messwerte werden nicht auf beide Tips gespiegelt oder zur Materialanpassung verwendet.

Im Flug-Krümmungsdiagramm (`results/images/loads.svg`, unten rechts) stehen Balkenkrümmung M/EI und die aus der linearen FEM abgeleiteten A/B-Kurven zusammen. FEM-Pfad: Mitte des hinteren Depronkerns bei y=3 mm, z=0; tatsächliche Knotenverschiebungen, kein Querschnittsmittel. Lokale kubische Ausgleichspolynome über fünf Stationen liefern w'' in 1/m. Die ersten/letzten zwei Stationen werden im Plot ausgelassen; CSV-Dateien `flight_rear_curvature_A.csv` und `flight_rear_curvature_B.csv` enthalten auch die gekennzeichneten Randschätzungen sowie die örtliche Fitbreite. Die Auswertung glättet Übergänge und ist kein Nachweis lokaler Krümmungskonvergenz oder exakter geometrischer Krümmung bei großer Verformung. Keine Änderung oder Neuberechnung der Solverlastfälle erforderlich.

## Import und Nachvollziehbarkeit

**Aktive Fluglast:** `flight.distribution: chord_proportional`. Die Flächentiefen C22:C27 und Abschnittslängen D22:D27 werden separat von den Gurtmaßen importiert (`mapping.planform`). q(x) ist proportional zur linearen Tiefenkontur und auf den unveränderten Gesamtauftrieb aus D37 normiert. Annahme: örtlich konstanter Auftriebsbeiwert; keine berechnete Randwirbel-/Verwindungsverteilung. Die Flächenintegration ergibt 0,521 m²; q reicht von 958,33 bis 395,83 N/m, das Wurzelmoment beträgt 670,83 Nm. Beim Auflagenversuch und den unbelasteten Eigenformen ändert sich die Lastdefinition nicht. Das Gleichlastmodell ist nur lokal archiviert und wird nicht mitveröffentlicht. Die frühere Gleichlast-Rekonstruktion bleibt im Bericht als ausdrücklich separater Excel-Referenzfall erhalten.

Die Ergebnisse des früheren Aufbaus mit Stegende bei 1,29 m sind nur lokal archiviert und werden nicht mitveröffentlicht. `results/` gehört zur neuen Geometrie mit mindestens 6 mm Gurtbreite und durchgehendem hinterem Steg. Die ursprüngliche Excel-Datei wurde dafür nicht geändert; die Mindestbreite und CFK-Mindestwanddicke werden beim Import über die YAML angewendet.

Die vertikalen Auflagerbedingungen können Druck- und Niederhaltekräfte übertragen. Die Versuchswerte gelten für diese idealisierte Führung. Die räumliche Lastübertragung durch die reale Flügelschale wird damit nicht ausdrücklich modelliert.

Echte BIFF-`.xls`: xlrd + OLE-Formeltokens; `.xlsx`: openpyxl, Formel- und Cacheansicht. Reader rechnen keine Formeln neu. Fehlende Fehlercaches blockieren die betroffenen Inputs; externe Links und Makros werden nicht ausgeführt. Die optionale Neuberechnung durch LibreOffice ist nicht implementiert. Ein Formeltext aus xlrd dient nur zur Diagnose (Klammerdarstellung eingeschränkt); originale BIFF-Token werden gesichert. Formelcache-Konsistenz wird zusätzlich über A/G=n und physikalische Referenzformeln geprüft, aber nicht für jede beliebige Excel-Formel bewiesen.

Priorität: `--set` > `overrides` in YAML > Excel. Überschreibungen erscheinen mit Vorwert im Bericht. Ein anderer Dateiname ist frei möglich; bei anderer Tabellenstruktur das Mapping anpassen. Ein Mapping kann statt `cell` eine eindeutige `label` mit `offset: [Zeilen, Spalten]` verwenden. Mehrdeutige Beschriftungen sind Fehler. Keine Zelladressen im Rechenkern.

## Artefakte

Der Report enthält Modell-, Netz-, Verformungs-, Spannungs- und Eigenformbilder der tatsächlich ausgeführten Biest-FEM sowie eine getrennte, ausdrücklich als **synthetischer Prüffall** gekennzeichnete Referenzgalerie. Spannungen werden an Integrationspunkten aus CalculiX-DAT gelesen und innerhalb eines Elements gemittelt; keine Glättung über Materialgrenzen und kein CFK-Versagenskriterium.

Galerie reproduzieren (für den Auflagenversuch `flight` durch `test` ersetzen):

```powershell
.venv/Scripts/python.exe -m wingcheck.gallery --source benchmark_results/fem/A/level_3/flight --output results/fem_reference/flight --solver "C:/Program Files/FreeCAD 1.1/bin/ccx.exe" --label "Synthetischer Prueffall: Flug-Halbmodell"
```

Mit `--reuse-results` werden ausschließlich vorhandene Ergebnisse bei exakt identischem Solverinput erneut gerendert. Anschließend `python -m wingcheck --config config.yaml --output results --with-fem` zum Aktualisieren des Berichts. Künftige ausgeführte Original-FEM-Läufe erzeugen die vier Bildarten automatisch.

`results/report.md` mit relativen PNG-Pfaden; zusätzlich SVG, `excel_inventory.json`, `normalized_input.json`, `summary.csv/json`, `used_config.yaml`, `diagnostics.json`. Bei tatsächlich ausgeführter FEM unter `fem/A|B/level_*/flight|test`: FCStd, STEP, Gmsh-Geometrie/Netz, SI-Netz-JSON, CalculiX `.inp/.dat/.frd`, Logs und geparste Ergebnisse. Keine FEM-Bilder ohne tatsächliche Solverdateien.

Die aktive FEM nutzt FreeCAD-Loft-Volumengeometrie und einen eigenen strukturierten Netzgenerator mit quadratischen C3D20R-Hexaederelementen. Dadurch sind die dünnen CFK-Schichten mit stark unterschiedlichen Abmessungen gezielt vernetzbar. Innerhalb eines Intervalls teilen die Materialien Knoten; an Lagensprüngen werden nichtpassende Flächennetze quadratisch interpolierend verbunden, mit der dickeren/inbordseitigen Fläche als Master. Es werden keine starren Spinnen verwendet. C3D8I-Vorläufe wurden nach der Modenkontrolle verworfen. Der frühere Gmsh-/C3D10-Adapter bleibt für homogene Referenzstege vorhanden.

Aktuelle Originalartefakte liegen unter `results/fem_sandwich_q20/A|B/level_*/flight|test`: FCStd, STEP, SI-Netz-JSON und VTK, CalculiX-Eingaben, DAT/FRD, Logs und Bilder. Zwischenstand: `results/fem_progress.json`. Identische Solverinputs mit erfolgreichem Log und gleicher CalculiX-Version können bei Wiederholung wiederverwendet werden; geänderte Inputs werden neu gerechnet. CAD in mm, Solver in m–N–kg–s–Pa. Netzkonvergenz und Reaktionsreste prüfen; 3D-Eigenformen vor Vergleich auf vertikale Biegung prüfen.

## Struktur

- `excel.py`, `model.py`: Inventur, Mapping, Einheiten, Herkunft, Validierung.
- `sections.py`: Komponenten, Neutralachse, Eigen-/Steiner-Anteile, diskrete Gurte.
- `statics.py`, `dynamics.py`, `analysis.py`: Integration, Hermite-Balken, Vollmodell und Eigenwerte.
- `freecad_geometry.py`, `fem.py`: parametrische CAD-Dokumentation, 3D-Netz und Solver.
- `sandwich.py`, `sandwich_fem.py`: bestätigte Keilgeometrie, Depron-/CFK-Partitionen, strukturiertes quadratisches Netz und Interfacegleichungen.
- `postprocess.py`, `visualization.py`, `report.py`: echte Solverauswertung, Diagramme und Report.

Die Referenztests verwenden synthetische, explizit definierte Benchmarkwerte. Diese sind keine Eingaben oder FEM-Ergebnisse der gelieferten Excel-Datei. Die Rechnung ist ein Steifigkeitsvergleich, kein Festigkeits-, Delaminations-, Stabilitäts- oder Flugfreigabenachweis.

Der tatsächlich ausgeführte synthetische Integrationslauf ist in [results/validation.md](results/validation.md) dokumentiert. Reproduzieren mit `python tests/run_fem_benchmark.py`, danach `python tests/verify_artifacts.py`. Optional `python -m tests.run_nonlinear_smoke` für einen echten geometrisch nichtlinearen Solverlauf auf dem Referenznetz. Die drei groben Referenznetze erreichen das konfigurierte 2-%-Ziel noch nicht; die Warnung ist beabsichtigt sichtbar. Für belastbare FEM-Auswertung müssen Netzgröße und reale Last-/Auflagenbanddiskretisierung weiter verfeinert werden.
