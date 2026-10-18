# Holmberechnung – Import, Nachrechnung und Ausführungsnachweis

## Aufgabenstellung und Modellumfang

Vergleich A (diskreter Excel-Lagenplan) gegen B (durchgehende jeweilige Wurzellagen). Holm, keine vollständige Flügelsteifigkeit.
x=0 an der Wurzel, x=L an der Halbflügelspitze. Gesamtspannweite 2.8 m; Halbspannweite 1.4 m.

## Tatsächlich ausgeführte Schritte

| Schritt | Status |
|---|---|
| Excel-Inventur, Formeltokens, Cache-/Konsistenzprüfung | ausgeführt, schreibgeschützt |
| Rekonstruktion einfacher Excel-Näherungen | ausgeführt; keine Neuberechnung der Arbeitsmappe |
| Varianten A/B: Statik, Masse, Eigenwertlösung | ausgeführt |
| Räumliche FreeCAD/CalculiX-FEM | ausgeführt |

Originaldatei: `C:\Users\USER\Documents\ChatGPT\Erweiterte_Holmberechnung_nach_Christian_Baron\Holmberechnung_deutsch_korrigiert3_Biest.xls`  
SHA-256: `310f7fe670c74eb42d6dfe5a9c250a67c4957ffa026299d3ba60b1b76c17d7b0`

Vollständige Daten: [Inventur](excel_inventory.json), [SI-Modell](normalized_input.json), [Konfiguration](used_config.yaml), [Diagnose](diagnostics.json), [Ergebnisse](summary.json).

## Fehlende Daten und Annahmen

- Excel-Flugnäherung M0*L²/(2EI) ist doppelt so groß wie die korrekte Gleichlast-Kragträgerformel q*L⁴/(8EI).
- Altes Excel-I ist größenordnungsmäßig größer als korrigiertes I; alter Formelzweig nicht als Referenz verwenden.
- VORLÄUFIG: Excel-Auslegungsplan als Fertigungsplan angenommen; tatsächliche Fertigung NICHT bestätigt.
- VORLÄUFIG: unveränderter Excel-Auftrieb ist eine Vergleichslast, keine bestätigte Grenz-/Bruchlast; kein Sicherheitsfaktor angewendet.
- Bestätigtes Schlauchmodell: zwei Depronkerne, ±45°-CFK-Wände; Materialwerte bleiben Annahmen. Stegfreier Spitzenbereich ohne Schale: Balkenrechnung dort nur idealisierte Vergleichsgrenze.
- VORLÄUFIG: Materialkennwerte enthalten ausdrücklich bestätigte Beispielannahmen.

Fehlende Eingaben werden nicht automatisch ersetzt. Explizite Annahmen aus der verwendeten YAML sind als vorläufig markiert; Beispiele in `examples/material.example.yaml` werden niemals automatisch eingelesen.
Die E1-Angabe stammt aus der ausgewählten Excel-Materialzeile. Ob sie den tatsächlich ausgehärteten Verbund beschreibt, muss bestätigt werden. Festigkeits-/Beulnachweise und Flugsicherheitsfreigabe sind nicht Gegenstand dieser Rechnung.

## Excel-Inventur und Mapping

| Blatt | belegte Zeilen | Spalten |
|---|---:|---:|
| Berechnung der Werte | 173 | 34 |
| Materialdaten | 84 | 16 |
| Flächensteckung | 69 | 18 |
| Roving-Gelege Umrechnung | 30 | 5 |

Alle belegten Werte, Kommentare, Formelergebnisse und verfügbare Formeltokens stehen in der Inventur. BIFF-Formeltexte sind diagnostisch: xlrd kann Klammern uneindeutig darstellen; Tokens bleiben als verlustfreie Referenz erhalten. Fehlende, Excel-fehlerhafte und durch unabhängige Beziehungen auffällige Caches werden gemeldet. Keine vollständige Excel-Formelauswertung; keine LibreOffice-Neuberechnung ausgeführt.

| Parameter | SI-Wert | Originalwert/-einheit | interne Einheit | Blatt/Zelle | Herkunft / Überschreibung |
|---|---:|---|---|---|---|
| span | 2.8 | 2800 mm | m | Berechnung der Werte!D45 | Excel-Cache |
| total_lift | 2170.83 | 2170.83 N | N | Berechnung der Werte!D37 | Excel-Cache |
| weight | 30 | 30 N | N | Berechnung der Werte!D39 | Excel-Eingabe |
| load_factor | 72.3611 | 72.3611 1 | 1 | Berechnung der Werte!D41 | Excel-Cache |
| E1 | 1.35e+11 | 135000 MPa | Pa | Berechnung der Werte!U68 | Excel-Cache |
| support_fraction | 0.64 | 64 % | 1 | Berechnung der Werte!C145 | Excel-Eingabe |
| test_mass | 3.8 | 3.8 kg | kg | Berechnung der Werte!C144 | Excel-Eingabe |
| modal_mass | 5.58 | 5.58 kg | kg | Berechnung der Werte!C170 | Excel-Eingabe |
| excel_I_old | 4.4903e-07 | 449030 mm4 | m⁴ | Berechnung der Werte!W68 | Excel-Cache |
| excel_I_new | 8.69642e-09 | 8696.42 mm4 | m⁴ | Berechnung der Werte!W78 | Excel-Cache |
| excel_flight_old | 0.0122832 | 12.2832 mm | m | Berechnung der Werte!C126 | Excel-Cache |
| excel_flight_new | 0.634229 | 634.229 mm | m | Berechnung der Werte!G126 | Excel-Cache |
| measured_root | 0.00702 | 7.02 mm | m | Berechnung der Werte!D146 | Excel-Cache |
| measured_tip | 0.005985 | 5.985 mm | m | Berechnung der Werte!D147 | Excel-Cache |
| measured_frequency | 4.5 | 4.5 Hz | Hz | Berechnung der Werte!C173 | Excel-Eingabe |
| measured_stiffness | 5310.26 | 5.31026 N/mm | N/m | Berechnung der Werte!D149 | Excel-Cache |
| excel_test_root | 0.00380672 | 3.80672 mm | m | Berechnung der Werte!C146 | Excel-Cache |
| excel_frequency | 6.66736 | 6.66736 Hz | Hz | Berechnung der Werte!C171 | Excel-Cache |
| stations[111].x | 0 | 0 mm | m | Berechnung der Werte!C111 | Excel-Auslegung/Cache |
| stations[111].width_top | 0.0625 | 62.5 mm | m | Berechnung der Werte!D111 | Excel-Auslegung/Cache |
| stations[111].width_bottom | 0.0625 | 62.5 mm | m | Berechnung der Werte!D111 | Excel-Auslegung/Cache |
| stations[111].height | 0.01778 | 17.78 mm | m | Berechnung der Werte!H111 | Excel-Auslegung/Cache |
| stations[111].clear_height | 0.0158736 | 15.8736 mm | m | Berechnung der Werte!J111 | Excel-Auslegung/Cache |
| stations[111].theoretical_thickness | 0.000953212 | 0.953212 mm | m | Berechnung der Werte!K111 | Excel-Auslegung/Cache |
| stations[111].plies_top | 10 | 10 1 | 1 | Berechnung der Werte!M111 | Excel-Auslegung/Cache |
| stations[111].plies_bottom | 10 | 10 1 | 1 | Berechnung der Werte!M111 | Excel-Auslegung/Cache |
| stations[111].web_required | 0.000379882 | 0.379882 mm | m | Berechnung der Werte!R111 | Excel-Auslegung/Cache |
| stations[112].x | 0.2 | 200 mm | m | Berechnung der Werte!C112 | Excel-Auslegung/Cache |
| stations[112].width_top | 0.0537143 | 53.7143 mm | m | Berechnung der Werte!D112 | Excel-Auslegung/Cache |
| stations[112].width_bottom | 0.0537143 | 53.7143 mm | m | Berechnung der Werte!D112 | Excel-Auslegung/Cache |
| stations[112].height | 0.01735 | 17.35 mm | m | Berechnung der Werte!H112 | Excel-Auslegung/Cache |
| stations[112].clear_height | 0.0157007 | 15.7007 mm | m | Berechnung der Werte!J112 | Excel-Auslegung/Cache |
| stations[112].theoretical_thickness | 0.000824627 | 0.824627 mm | m | Berechnung der Werte!K112 | Excel-Auslegung/Cache |
| stations[112].plies_top | 9 | 9 1 | 1 | Berechnung der Werte!M112 | Excel-Auslegung/Cache |
| stations[112].plies_bottom | 9 | 9 1 | 1 | Berechnung der Werte!M112 | Excel-Auslegung/Cache |
| stations[112].web_required | 0.000329198 | 0.329198 mm | m | Berechnung der Werte!R112 | Excel-Auslegung/Cache |
| stations[113].x | 0.4 | 400 mm | m | Berechnung der Werte!C113 | Excel-Auslegung/Cache |
| stations[113].width_top | 0.0449286 | 44.9286 mm | m | Berechnung der Werte!D113 | Excel-Auslegung/Cache |
| stations[113].width_bottom | 0.0449286 | 44.9286 mm | m | Berechnung der Werte!D113 | Excel-Auslegung/Cache |
| stations[113].height | 0.01692 | 16.92 mm | m | Berechnung der Werte!H113 | Excel-Auslegung/Cache |
| stations[113].clear_height | 0.0155349 | 15.5349 mm | m | Berechnung der Werte!J113 | Excel-Auslegung/Cache |
| stations[113].theoretical_thickness | 0.000692569 | 0.692569 mm | m | Berechnung der Werte!K113 | Excel-Auslegung/Cache |
| stations[113].plies_top | 7 | 7 1 | 1 | Berechnung der Werte!M113 | Excel-Auslegung/Cache |
| stations[113].plies_bottom | 7 | 7 1 | 1 | Berechnung der Werte!M113 | Excel-Auslegung/Cache |
| stations[113].web_required | 0.000277261 | 0.277261 mm | m | Berechnung der Werte!R113 | Excel-Auslegung/Cache |
| stations[114].x | 0.6 | 600 mm | m | Berechnung der Werte!C114 | Excel-Auslegung/Cache |
| stations[114].width_top | 0.0361429 | 36.1429 mm | m | Berechnung der Werte!D114 | Excel-Auslegung/Cache |
| stations[114].width_bottom | 0.0361429 | 36.1429 mm | m | Berechnung der Werte!D114 | Excel-Auslegung/Cache |
| stations[114].height | 0.01563 | 15.63 mm | m | Berechnung der Werte!H114 | Excel-Auslegung/Cache |
| stations[114].clear_height | 0.0144444 | 14.4444 mm | m | Berechnung der Werte!J114 | Excel-Auslegung/Cache |
| stations[114].theoretical_thickness | 0.000592797 | 0.592797 mm | m | Berechnung der Werte!K114 | Excel-Auslegung/Cache |
| stations[114].plies_top | 6 | 6 1 | 1 | Berechnung der Werte!M114 | Excel-Auslegung/Cache |
| stations[114].plies_bottom | 6 | 6 1 | 1 | Berechnung der Werte!M114 | Excel-Auslegung/Cache |
| stations[114].web_required | 0.000238554 | 0.238554 mm | m | Berechnung der Werte!R114 | Excel-Auslegung/Cache |
| stations[115].x | 0.8 | 800 mm | m | Berechnung der Werte!C115 | Excel-Auslegung/Cache |
| stations[115].width_top | 0.0273571 | 27.3571 mm | m | Berechnung der Werte!D115 | Excel-Auslegung/Cache |
| stations[115].width_bottom | 0.0273571 | 27.3571 mm | m | Berechnung der Werte!D115 | Excel-Auslegung/Cache |
| stations[115].height | 0.01434 | 14.34 mm | m | Berechnung der Werte!H115 | Excel-Auslegung/Cache |
| stations[115].clear_height | 0.013389 | 13.389 mm | m | Berechnung der Werte!J115 | Excel-Auslegung/Cache |
| stations[115].theoretical_thickness | 0.0004755 | 0.4755 mm | m | Berechnung der Werte!K115 | Excel-Auslegung/Cache |
| stations[115].plies_top | 5 | 5 1 | 1 | Berechnung der Werte!M115 | Excel-Auslegung/Cache |
| stations[115].plies_bottom | 5 | 5 1 | 1 | Berechnung der Werte!M115 | Excel-Auslegung/Cache |
| stations[115].web_required | 0.000193019 | 0.193019 mm | m | Berechnung der Werte!R115 | Excel-Auslegung/Cache |
| stations[116].x | 0.9 | 900 mm | m | Berechnung der Werte!C116 | Excel-Auslegung/Cache |
| stations[116].width_top | 0.0229643 | 22.9643 mm | m | Berechnung der Werte!D116 | Excel-Auslegung/Cache |
| stations[116].width_bottom | 0.0229643 | 22.9643 mm | m | Berechnung der Werte!D116 | Excel-Auslegung/Cache |
| stations[116].height | 0.01348 | 13.48 mm | m | Berechnung der Werte!H116 | Excel-Auslegung/Cache |
| stations[116].clear_height | 0.0126469 | 12.6469 mm | m | Berechnung der Werte!J116 | Excel-Auslegung/Cache |
| stations[116].theoretical_thickness | 0.000416545 | 0.416545 mm | m | Berechnung der Werte!K116 | Excel-Auslegung/Cache |
| stations[116].plies_top | 5 | 5 1 | 1 | Berechnung der Werte!M116 | Excel-Auslegung/Cache |
| stations[116].plies_bottom | 5 | 5 1 | 1 | Berechnung der Werte!M116 | Excel-Auslegung/Cache |
| stations[116].web_required | 0.000170287 | 0.170287 mm | m | Berechnung der Werte!R116 | Excel-Auslegung/Cache |
| stations[117].x | 1 | 1000 mm | m | Berechnung der Werte!C117 | Excel-Auslegung/Cache |
| stations[117].width_top | 0.0185714 | 18.5714 mm | m | Berechnung der Werte!D117 | Excel-Auslegung/Cache |
| stations[117].width_bottom | 0.0185714 | 18.5714 mm | m | Berechnung der Werte!D117 | Excel-Auslegung/Cache |
| stations[117].height | 0.01262 | 12.62 mm | m | Berechnung der Werte!H117 | Excel-Auslegung/Cache |
| stations[117].clear_height | 0.0119203 | 11.9203 mm | m | Berechnung der Werte!J117 | Excel-Auslegung/Cache |
| stations[117].theoretical_thickness | 0.000349836 | 0.349836 mm | m | Berechnung der Werte!K117 | Excel-Auslegung/Cache |
| stations[117].plies_top | 4 | 4 1 | 1 | Berechnung der Werte!M117 | Excel-Auslegung/Cache |
| stations[117].plies_bottom | 4 | 4 1 | 1 | Berechnung der Werte!M117 | Excel-Auslegung/Cache |
| stations[117].web_required | 0.000144533 | 0.144533 mm | m | Berechnung der Werte!R117 | Excel-Auslegung/Cache |
| stations[118].x | 1.1 | 1100 mm | m | Berechnung der Werte!C118 | Excel-Auslegung/Cache |
| stations[118].width_top | 0.0141786 | 14.1786 mm | m | Berechnung der Werte!D118 | Excel-Auslegung/Cache |
| stations[118].width_bottom | 0.0141786 | 14.1786 mm | m | Berechnung der Werte!D118 | Excel-Auslegung/Cache |
| stations[118].height | 0.0109 | 10.9 mm | m | Berechnung der Werte!H118 | Excel-Auslegung/Cache |
| stations[118].clear_height | 0.0103036 | 10.3036 mm | m | Berechnung der Werte!J118 | Excel-Auslegung/Cache |
| stations[118].theoretical_thickness | 0.000298203 | 0.298203 mm | m | Berechnung der Werte!K118 | Excel-Auslegung/Cache |
| stations[118].plies_top | 3 | 3 1 | 1 | Berechnung der Werte!M118 | Excel-Auslegung/Cache |
| stations[118].plies_bottom | 3 | 3 1 | 1 | Berechnung der Werte!M118 | Excel-Auslegung/Cache |
| stations[118].web_required | 0.000125409 | 0.125409 mm | m | Berechnung der Werte!R118 | Excel-Auslegung/Cache |
| stations[119].x | 1.2 | 1200 mm | m | Berechnung der Werte!C119 | Excel-Auslegung/Cache |
| stations[119].width_top | 0.00978571 | 9.78571 mm | m | Berechnung der Werte!D119 | Excel-Auslegung/Cache |
| stations[119].width_bottom | 0.00978571 | 9.78571 mm | m | Berechnung der Werte!D119 | Excel-Auslegung/Cache |
| stations[119].height | 0.00918 | 9.18 mm | m | Berechnung der Werte!H119 | Excel-Auslegung/Cache |
| stations[119].clear_height | 0.00872644 | 8.72644 mm | m | Berechnung der Werte!J119 | Excel-Auslegung/Cache |
| stations[119].theoretical_thickness | 0.000226781 | 0.226781 mm | m | Berechnung der Werte!K119 | Excel-Auslegung/Cache |
| stations[119].plies_top | 3 | 3 1 | 1 | Berechnung der Werte!M119 | Excel-Auslegung/Cache |
| stations[119].plies_bottom | 3 | 3 1 | 1 | Berechnung der Werte!M119 | Excel-Auslegung/Cache |
| stations[119].web_required | 9.87163e-05 | 0.0987163 mm | m | Berechnung der Werte!R119 | Excel-Auslegung/Cache |
| stations[120].x | 1.3 | 1300 mm | m | Berechnung der Werte!C120 | Excel-Auslegung/Cache |
| stations[120].width_top | 0.00539286 | 5.39286 mm | m | Berechnung der Werte!D120 | Excel-Auslegung/Cache |
| stations[120].width_bottom | 0.00539286 | 5.39286 mm | m | Berechnung der Werte!D120 | Excel-Auslegung/Cache |
| stations[120].height | 0.007675 | 7.675 mm | m | Berechnung der Werte!H120 | Excel-Auslegung/Cache |
| stations[120].clear_height | 0.00743333 | 7.43333 mm | m | Berechnung der Werte!J120 | Excel-Auslegung/Cache |
| stations[120].theoretical_thickness | 0.000120836 | 0.120836 mm | m | Berechnung der Werte!K120 | Excel-Auslegung/Cache |
| stations[120].plies_top | 2 | 2 1 | 1 | Berechnung der Werte!M120 | Excel-Auslegung/Cache |
| stations[120].plies_bottom | 2 | 2 1 | 1 | Berechnung der Werte!M120 | Excel-Auslegung/Cache |
| stations[120].web_required | 5.79446e-05 | 0.0579446 mm | m | Berechnung der Werte!R120 | Excel-Auslegung/Cache |
| stations[121].x | 1.4 | 1400 mm | m | Berechnung der Werte!C121 | Excel-Auslegung/Cache |
| stations[121].width_top | 0.001 | 1 mm | m | Berechnung der Werte!D121 | Excel-Auslegung/Cache |
| stations[121].width_bottom | 0.001 | 1 mm | m | Berechnung der Werte!D121 | Excel-Auslegung/Cache |
| stations[121].height | 0.00617 | 6.17 mm | m | Berechnung der Werte!H121 | Excel-Auslegung/Cache |
| stations[121].clear_height | 0.00617 | 6.17 mm | m | Berechnung der Werte!J121 | Excel-Auslegung/Cache |
| stations[121].theoretical_thickness | 0 | 0 mm | m | Berechnung der Werte!K121 | Excel-Auslegung/Cache |
| stations[121].plies_top | 0 | 0 1 | 1 | Berechnung der Werte!M121 | Excel-Auslegung/Cache |
| stations[121].plies_bottom | 0 | 0 1 | 1 | Berechnung der Werte!M121 | Excel-Auslegung/Cache |
| stations[121].web_required | 0 | 0 mm | m | Berechnung der Werte!R121 | Excel-Auslegung/Cache |

## Rekonstruierte Excel-Näherungen

Die Vorlage bestimmt Auftrieb aus ca, Geschwindigkeit und Fläche; G ist in N angegeben, keine Masse in kg. n=A/G wird geprüft. Die in Excel verwendete konstante Streckenlast integriert zu A/2. Eine explizite Unterscheidung Grenz-/Bruchlast ist nicht vorhanden und muss bestätigt werden.
Die Höhen H (Profil), h (unter Beplankung), h1 (lichte Steghöhe) und t (theoretische Gurtdicke) sind zu unterscheiden. Das Standardmapping verwendet h als Holm-Außenhöhe. Fertigungslagen verschieben Gurtschwerpunkte gegenüber der theoretischen Excel-Geometrie.

Für konstantes EI an der Wurzel gelten:
- Gleichlast-Kragträger: δ=qL⁴/(8EI), M₀=qL²/2. Die ausgeschriebene Excel-Näherung M₀L²/(2EI) überschätzt diesen Referenzfall um Faktor 2.
- Gelenkiger Auflagenversuch, zentrale Kraft: δ₀=F(2pL)³/(48EI). Freie Überhänge ohne Eigengewicht sind krümmungsfrei, aber wegen der Auflagerneigung nicht verschiebungsfrei.
- Zentraler Feder-Masse-Ersatz: k=6EI/(pL)³ und f=√(k/m)/(2π). Strukturmasse fehlt in dieser einfachen Excel-Näherung.

| Größe | neu rekonstruierter Wert | Bedeutung |
|---|---:|---|
| uniform_q_N_m | 775.298 | konstante Halbflügel-Streckenlast N/m |
| root_moment_Nm | 759.792 | Wurzelmoment Nm |
| flight_uniform_root_EI_m | 0.317115 | korrekte Gleichlastformel, m; konstantes korrigiertes Excel-Wurzel-EI |
| excel_written_flight_root_EI_m | 0.634229 | ausgeschriebene Excel-Näherung, m |
| test_root_constant_EI_m | 0.00380672 | Wurzelabsenkung, m; konstantes korrigiertes Excel-Wurzel-EI |
| test_tip_constant_EI_m | 0.00321192 | Spitzenhebung relativ Auflagen, m |
| spring_frequency_excel_mass_Hz | 6.66736 | Feder-Masse-Näherung mit C170, Hz |

Diese Werte verwenden das theoretische Excel-Wurzel-EI und ersetzen keine Rechnung der Fertigungsvarianten. C144 ist die statische Laständerungsmasse; C170 wird separat als gesamte mitbewegte Zentralmasse interpretiert. Ihre physische Bedeutung muss am Aufbau bestätigt werden.

| gespeicherte Excel-/Messgröße | Wert in SI |
|---|---:|
| excel_I_old | 4.4903e-07 |
| excel_I_new | 8.69642e-09 |
| excel_flight_old | 0.0122832 |
| excel_flight_new | 0.634229 |
| measured_root | 0.00702 |
| measured_tip | 0.005985 |
| measured_frequency | 4.5 |
| measured_stiffness | 5310.26 |
| excel_test_root | 0.00380672 |
| excel_frequency | 6.66736 |

## Berechnungsverfahren und Randbedingungen

A verwendet abschnittsweise konstante ganze Lagenzahlen [xᵢ,xᵢ₊₁); der Spitzenwert 0 beschreibt das Ende, kein endliches gurtloses Intervall. Breiten und Höhen werden linear interpoliert. B übernimmt nur die oberen/unteren Wurzellagen; restliche Geometrie bleibt gleich.
Querschnitt: zₙ=Σ(EAz)/Σ(EA), EI=ΣE[Iₑ+A(z−zₙ)²]. Orthotrope Nachgiebigkeitsmatrix ist symmetrisch (νji=νij Ej/Ei) und muss positiv definit sein. Es wird ebene vertikale Biegung um eine gemeinsame Breitenmittellinie angenommen; damit keine Biege-Torsionskopplung. Ein Verbinder wird ohne bestätigten Schub-/Momentenübertragungsmechanismus nicht addiert.
Flug: M(x)=∫ₓᴸq(s)(s−x)ds, κ=M/EI, θ=∫κdx und w=∫θdx. Krümmung wird innerhalb jedes diskreten Lagenintervalls einseitig mit Gaußquadratur integriert; kein Glätten der Steifigkeitssprünge. Zusätzlich eine an allen Geometrie- und Lagensprüngen segmentierte numerische Balkenlösung mit Gaußintegration. Positive Fluglast bedeutet positive Durchbiegung.
Versuch: vollständiger Flügel, zwei vertikale Gelenkauflager bei ±pL (oder expliziten Koordinaten), freie Überhänge, zentrale Last. Die Wurzel ist beweglich und nicht eingespannt. Positive Auflagerbreiten werden in 1D als ideale Gelenke an ihren Mittelpunkten modelliert, in 3D als flächige Bänder; dadurch kann zusätzliche lokale Steifigkeit entstehen.
Dynamik: Euler-Bernoulli-Hermite-Elemente, konsistente verteilte Masse und separate Zentralmasse am beweglichen Wurzelknoten; optional Rotationsträgheit. Vollmodell erfasst symmetrische und antisymmetrische Biegemoden. Zentralmasse ist fest mitbewegend; lose aufgelegte Massen können Kontakt verlieren. Statische Versuchsmasse und dynamische Gesamtmasse werden nicht addiert.
Rayleigh: statische Einheitslast-Biegelinie als zulässige Ansatzfunktion; ω²=φᵀKφ/(φᵀMφ). Effektive Masse m_eff=φᵀMφ/φ(0)². Der mit derselben Ansatzfunktion gebildete Feder-Masse-Wert ist mathematisch identisch und kein unabhängiger Genauigkeitsnachweis. Numerische Eigenwerte sind keine geschlossene Formel.
Schub: optionaler Fluganteil ∫V/(κGA)dx wird separat ausgegeben. Versuch und Eigenwerte bleiben Euler-Bernoulli; keine behauptete Timoshenko-Validierung.

## Variantenvergleich

| Größe | A | B | (B−A)/A |
|---|---:|---:|---:|
| half_spar_mass_kg | 0.139683 | 0.172464 | 23.5 % |
| flight_tip_m | 0.64847 | 0.492477 | -24.1 % |
| flight_integral_tip_m | 0.64847 | 0.492477 | -24.1 % |
| test_root_m | -0.0056406 | -0.00494968 | -12.2 % |
| test_right_tip_m | 0.00593223 | 0.00478371 | -19.4 % |
| rayleigh_Hz | 5.3901 | 5.74767 | 6.63 % |

| Eigenform | A [Hz] / Symmetrie | B [Hz] / Symmetrie |
|---|---|---|
| 1 | 5.3901 / symmetrisch | 5.7476 / symmetrisch |
| 2 | 108.31 / antisymmetrisch | 105.11 / antisymmetrisch |
| 3 | 162.92 / symmetrisch | 139.3 / symmetrisch |
| 4 | 212.32 / antisymmetrisch | 191.69 / antisymmetrisch |
| 5 | 258.72 / symmetrisch | 250.69 / symmetrisch |
| 6 | 508.31 / antisymmetrisch | 508.29 / antisymmetrisch |

A: Test-Reaktionsrest -5.509e-08 N; Flugreaktion -1085.4 N, -759.79 Nm. Materialvolumen (Halbflügel) {'top': np.float64(3.35867857142857e-05), 'bottom': np.float64(3.35867857142857e-05), 'rear_core': np.float64(8.28748829843904e-05), 'rear_left_0': np.float64(2.067439302667676e-06), 'rear_left_1': np.float64(2.0674393026676754e-06), 'rear_right_0': np.float64(2.0674393026676754e-06), 'rear_right_1': np.float64(2.0674393026676775e-06), 'rear_bottom_0': np.float64(7.303386289023829e-07), 'rear_bottom_1': np.float64(7.303386289023824e-07), 'rear_top_0': np.float64(7.303386289023824e-07), 'rear_top_1': np.float64(7.303386289023829e-07), 'front_core': np.float64(5.077022657614689e-05), 'front_left_0': np.float64(1.561565983431138e-06), 'front_left_1': np.float64(1.561565983431149e-06), 'front_right_0': np.float64(1.5615659834311484e-06), 'front_right_1': np.float64(1.5615659834311363e-06), 'front_bottom_0': np.float64(5.146308559632856e-07), 'front_bottom_1': np.float64(5.146308559632854e-07), 'front_top_0': np.float64(5.146308559632854e-07), 'front_top_1': np.float64(5.146308559632856e-07)}. Max. Flugdurchbiegung 0.64847 m bei x=1.4 m.
**Große Verformung: lineare Rechnung nur bedingt gültig; geometrisch nichtlineare FEM vergleichen.**

B: Test-Reaktionsrest 1.257e-07 N; Flugreaktion -1085.4 N, -759.79 Nm. Materialvolumen (Halbflügel) {'top': np.float64(4.444999999999998e-05), 'bottom': np.float64(4.444999999999998e-05), 'rear_core': np.float64(7.834488298439049e-05), 'rear_left_0': np.float64(1.9906783437197766e-06), 'rear_left_1': np.float64(1.990678343719777e-06), 'rear_right_0': np.float64(1.9906783437197766e-06), 'rear_right_1': np.float64(1.9906783437197783e-06), 'rear_bottom_0': np.float64(7.303386289023827e-07), 'rear_bottom_1': np.float64(7.303386289023824e-07), 'rear_top_0': np.float64(7.303386289023824e-07), 'rear_top_1': np.float64(7.303386289023827e-07), 'front_core': np.float64(4.957022657614691e-05), 'front_left_0': np.float64(1.5309401612854913e-06), 'front_left_1': np.float64(1.5309401612855023e-06), 'front_right_0': np.float64(1.530940161285502e-06), 'front_right_1': np.float64(1.5309401612854898e-06), 'front_bottom_0': np.float64(5.146308559632857e-07), 'front_bottom_1': np.float64(5.14630855963285e-07), 'front_top_0': np.float64(5.14630855963285e-07), 'front_top_1': np.float64(5.146308559632857e-07)}. Max. Flugdurchbiegung 0.49248 m bei x=1.4 m.
**Große Verformung: lineare Rechnung nur bedingt gültig; geometrisch nichtlineare FEM vergleichen.**

## Räumliche FEM und Netzkonvergenz

Aktives Biest-Schlauchmodell: keilförmige UD-Gurte mit gerader hinterer Kante, hinterer 5-mm-Depronkern bis x=1,29 m, vorderer bis x=0,70 m. Hintere Kernmitte y=3 mm; Verbindertasche 35 mm breit. Taschenlänge 0,14 m als Excel-basierte Annahme; vorderer Steg danach linear zur Keilkontur geführt. Idealer Verbund. Der Verbinder und seine Tasche werden als Lage-/Freiraumvorgabe dokumentiert, ohne unbelegten Steifigkeitsbeitrag. Jeder CFK-Schlauch besitzt zwei senkrechte Wände und obere/untere Abschnitte, jeweils R(x), in zwei halbe ±45°-Teilschichten zerlegt. Orientierungen beziehen sich auf die globale Spannweitenrichtung; die kleine lokale Schräglage des vorderen Stegs wird in der Faserorientierung vernachlässigt. Depron isotrop mit E=20 MPa, ν=0,30, ρ=40 kg/m³; CFK-Werte vorläufig. Der eigene strukturierte 3D-Netzgenerator erzeugt quadratische C3D20R-Hexaeder statt Gmsh-Tetraeder. Alle Materialgrenzen innerhalb eines Intervalls teilen Knoten. Nichtpassende Knoten an Lagensprüngen werden über quadratische Flächen-Verschiebungsinterpolation verbunden, ohne starre Lastspider; zusätzliche lokale Diskretisierungssteifigkeit ist durch Netzverfeinerung zu prüfen. Vorläufe mit linearen C3D8I-Elementen wurden wegen auffälliger lokaler Niedrigfrequenzformen verworfen und werden nicht als validierte Ergebnisse gezeigt.
CAD in mm; der strukturierte Netzgenerator arbeitet direkt in m. Solver: m, N, kg, s, Pa; Dichte kg/m³. E-Modul N/mm² aus Excel wird mit 10⁶ in Pa umgerechnet. UD-Gurtfaser entlang x; Schlauchfasern ±45° zur Spannweitenrichtung in der jeweiligen Wandebene. Ausgegebene σxx sind globale Längsspannungen, nur im UD-Gurt zugleich Fasernormalspannungen.
Lasten werden über die Elementflächen in konsistente Knotenkräfte umgerechnet; kein starrer Lastspider. Auflagen beschränken vertikale Verschiebung auf unteren Flächenbändern; drei weitere skalare Bedingungen verhindern Starrkörperbewegungen in der Ebene. Zusätzliche Zentralmasse verteilt sich über das Lastband. Ein Band kann lokal steifer wirken als die idealisierte Balken-Punktauflage.
Mindestens drei Netzfaktoren; relative Änderung zwischen den letzten zwei Stufen bezogen auf feinste Stufe. Räumliche Modalsuche liefert auch Quer-/Torsionsmoden; deren erste Frequenz darf erst nach Prüfung der Form einer vertikalen Balkenmode zugeordnet werden. Nichtlineare Statik wird separat gerechnet; Modalanalyse ist unbelastet linear, keine vorgespannte Analyse.

Status: **ausgeführt**.

### FEM A

| Netzfaktor | Flugtip [m] | Testwurzel [m] | f₁ [Hz] |
|---|---:|---:|---:|
| 1 | 28.8235 | -0.0112773 | 3.29358 |
| 2 | 29.0094 | -0.0143267 | 2.6365 |
| 3 | 29.0492 | -0.0134086 | 2.809 |

**Netzkonvergenz:** Konvergenzziel NICHT erreicht.
Änderung der letzten beiden Stufen, bezogen auf die feinste: flight_tip_m: 0.137 %, test_root_m: 6.85 %, frequency_Hz: 6.14 %.
Eigenfrequenzen 1–6 nach Index: 6.14 %, 1.62 %, 2.33 %, 0.0862 %, 0.0847 %, 0.0943 %. Ein Modenwechsel wird damit nicht ausgeschlossen.

**Netz 1: nicht erfolgreich abgeschlossen:** Nichtlinearer Vergleich: Zeitlimit 600s überschritten; kein abgeschlossenes Volllastergebnis. Siehe C:\Users\USER\Documents\ChatGPT\Erweiterte_Holmberechnung_nach_Christian_Baron\results\fem_sandwich_q20\A\level_1\flight\nonlinear.log

FEM-Strukturmasse: Halbflügel 0.139683 kg; Vollflügel 0.279367 kg. Enthält Gurte, CFK-Schläuche und Depron, keine Flügelschale und keine zentrale Zusatzmasse.

Reaktionen der drei gemittelten Vertikalbedingungen (aus dem globalen Gleichgewicht rekonstruiert): links hinten: -28.781 N, links vorne: 47.42 N, rechts: 18.638 N.
**Kontaktgrenze:** Das bilaterale Lagerungsmodell erfordert eine Zug-/Niederhaltereaktion. Lose Unterlagen können diese nicht aufbringen. Für eine physische Nachbildung des Auflagenversuchs müssen Kontaktlage bzw. Lastübertragung über die reale Flügelschale ergänzt werden. Die vorliegenden Werte gelten für die ausdrücklich idealisierten Gelenk-/Mittelungsbedingungen, nicht für einen nachgewiesenen einseitigen Kontaktversuch.

| 3D-Eigenform | Frequenz [Hz] | Symmetrie | Anteil vertikaler Verschiebung |
|---|---:|---|---:|
| 1 | 2.809 | gemischt | 83.6 % |
| 2 | 6.22987 | gemischt | 67 % |
| 3 | 17.5419 | gemischt | 56.5 % |
| 4 | 43.2581 | gemischt | 100 % |
| 5 | 43.2768 | gemischt | 100 % |
| 6 | 43.4251 | gemischt | 100 % |
Die Zuordnung erfolgt aus den räumlichen Eigenformen; Tabellenindizes sind kein Beweis einer Übereinstimmung mit den reinen 1D-Biegemoden.

| Größe | Balken | räumliche FEM (feinstes Netz) | (FEM−Balken)/Balken |
|---|---:|---:|---:|
| flight_tip_m | 0.64847 | 29.0492 | 4380 % |
| test_root_m | -0.0056406 | -0.0134086 | 137.7 % |
Frequenzvergleich erfordert Eigenformzuordnung. Die ausgewählte 3D-Form hat überwiegend vertikale Verschiebungen; Biege-Torsions-Mischformen sind möglich und müssen anhand der Bilder geprüft werden. Die Dreipunktstabilisierung der Auflagen erlaubt keine pauschale Annahme exakt symmetrischer/antisymmetrischer räumlicher Moden.

### FEM B

| Netzfaktor | Flugtip [m] | Testwurzel [m] | f₁ [Hz] |
|---|---:|---:|---:|
| 1 | 0.817002 | -0.00665861 | 4.83361 |
| 2 | 0.825007 | -0.00703083 | 4.60224 |
| 3 | 0.824473 | -0.00690111 | 4.68272 |

**Netzkonvergenz:** Konvergenzziel NICHT erreicht.
Änderung der letzten beiden Stufen, bezogen auf die feinste: flight_tip_m: 0.0647 %, test_root_m: 1.88 %, frequency_Hz: 1.72 %.
Eigenfrequenzen 1–6 nach Index: 1.72 %, 2.27 %, 3.34 %, 5.19 %, 1.6 %, 0.841 %. Ein Modenwechsel wird damit nicht ausgeschlossen.

**Netz 1: nicht erfolgreich abgeschlossen:** Nichtlinearer Vergleich: Zeitlimit 600s überschritten; kein abgeschlossenes Volllastergebnis. Siehe C:\Users\USER\Documents\ChatGPT\Erweiterte_Holmberechnung_nach_Christian_Baron\results\fem_sandwich_q20\B\level_1\flight\nonlinear.log

FEM-Strukturmasse: Halbflügel 0.172464 kg; Vollflügel 0.344929 kg. Enthält Gurte, CFK-Schläuche und Depron, keine Flügelschale und keine zentrale Zusatzmasse.

Reaktionen der drei gemittelten Vertikalbedingungen (aus dem globalen Gleichgewicht rekonstruiert): links hinten: -28.781 N, links vorne: 47.42 N, rechts: 18.638 N.
**Kontaktgrenze:** Das bilaterale Lagerungsmodell erfordert eine Zug-/Niederhaltereaktion. Lose Unterlagen können diese nicht aufbringen. Für eine physische Nachbildung des Auflagenversuchs müssen Kontaktlage bzw. Lastübertragung über die reale Flügelschale ergänzt werden. Die vorliegenden Werte gelten für die ausdrücklich idealisierten Gelenk-/Mittelungsbedingungen, nicht für einen nachgewiesenen einseitigen Kontaktversuch.

| 3D-Eigenform | Frequenz [Hz] | Symmetrie | Anteil vertikaler Verschiebung |
|---|---:|---|---:|
| 1 | 4.68272 | gemischt | 95.4 % |
| 2 | 7.95304 | gemischt | 35.7 % |
| 3 | 22.2702 | gemischt | 63.4 % |
| 4 | 74.6676 | gemischt | 99.4 % |
| 5 | 78.2093 | quasi-symmetrisch | 99.8 % |
| 6 | 99.1764 | gemischt | 99.2 % |
Die Zuordnung erfolgt aus den räumlichen Eigenformen; Tabellenindizes sind kein Beweis einer Übereinstimmung mit den reinen 1D-Biegemoden.

| Größe | Balken | räumliche FEM (feinstes Netz) | (FEM−Balken)/Balken |
|---|---:|---:|---:|
| flight_tip_m | 0.492477 | 0.824473 | 67.41 % |
| test_root_m | -0.00494968 | -0.00690111 | 39.43 % |
Frequenzvergleich erfordert Eigenformzuordnung. Die ausgewählte 3D-Form hat überwiegend vertikale Verschiebungen; Biege-Torsions-Mischformen sind möglich und müssen anhand der Bilder geprüft werden. Die Dreipunktstabilisierung der Auflagen erlaubt keine pauschale Annahme exakt symmetrischer/antisymmetrischer räumlicher Moden.

## Bilder

![geometry_plies](images/geometry_plies.png)

![supports](images/supports.png)

![beam_comparison](images/beam_comparison.png)

![loads](images/loads.png)

![modes](images/modes.png)

![sections](images/sections.png)

![stegannahmen](images/stegannahmen.png)


**Stegfreier Spitzenbereich:** Nach x=1,29 m bestehen nur die beiden Gurte. Die reale Flügelschale ist nicht enthalten. Dort ist der ideale Gurtverbund der Balkenrechnung nicht gegeben; insbesondere Flug-Spitzenverschiebungen und lokale Moden dürfen nicht als vollständige Flügelantwort interpretiert werden.

Flug-Spitzenverschiebung bezeichnet den belasteten oberen Gurt; der untere Gurt wird in der JSON/CSV getrennt ausgewiesen. Die Versuchswurzel wird über die obere Gurtfläche im 35-mm-Taschenbereich bei x=0 gemittelt. Zentrale Kraft und Masse wirken über dieses Taschenband und 50 mm in Spannweitenrichtung. Nichtlineare Statik wird für den großen Fluglastfall versucht; beim kleinen Auflagenversuch bleibt die Statik linear. [FEM-Ergebnistabelle als CSV](fem_summary.csv).

Die drei gemittelten Vertikalbedingungen der Auflagenbänder unterdrücken Starrkörperbewegungen, lassen aber die Rotation in Spannweitenrichtung frei. Eine flächige Fixierung aller Auflagenknoten wird im aktiven Modell ausdrücklich nicht verwendet. Reaktionskräfte werden aus den ursprünglichen Flächenknoten zurückgewonnen.


### fem_sandwich_q20/A

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/convergence.png)


### fem_sandwich_q20/A/level_1/flight

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/flight/static_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/flight/static_detail_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/flight/static_detail_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/flight/static_detail_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/flight/static_detail_stress_xx.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/flight/static_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/flight/static_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/flight/static_stress_xx.png)


### fem_sandwich_q20/A/level_1/test

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/test/static_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/test/static_detail_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/test/static_detail_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/test/static_detail_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/test/static_detail_stress_xx.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/test/static_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/test/static_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_1/test/static_stress_xx.png)


### fem_sandwich_q20/A/level_3/flight

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/flight/static_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/flight/static_detail_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/flight/static_detail_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/flight/static_detail_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/flight/static_detail_stress_xx.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/flight/static_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/flight/static_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/flight/static_stress_xx.png)


### fem_sandwich_q20/A/level_3/test

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/mode_1.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/mode_2.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/mode_3.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/mode_4.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/mode_5.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/mode_6.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/static_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/static_detail_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/static_detail_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/static_detail_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/static_detail_stress_xx.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/static_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/static_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/A/level_3/test/static_stress_xx.png)


### fem_sandwich_q20/B

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/convergence.png)


### fem_sandwich_q20/B/level_1/flight

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/flight/static_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/flight/static_detail_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/flight/static_detail_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/flight/static_detail_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/flight/static_detail_stress_xx.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/flight/static_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/flight/static_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/flight/static_stress_xx.png)


### fem_sandwich_q20/B/level_1/test

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/test/static_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/test/static_detail_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/test/static_detail_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/test/static_detail_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/test/static_detail_stress_xx.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/test/static_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/test/static_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_1/test/static_stress_xx.png)


### fem_sandwich_q20/B/level_3/flight

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/flight/static_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/flight/static_detail_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/flight/static_detail_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/flight/static_detail_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/flight/static_detail_stress_xx.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/flight/static_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/flight/static_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/flight/static_stress_xx.png)


### fem_sandwich_q20/B/level_3/test

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/mode_1.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/mode_2.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/mode_3.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/mode_4.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/mode_5.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/mode_6.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/static_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/static_detail_deformation.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/static_detail_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/static_detail_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/static_detail_stress_xx.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/static_mesh.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/static_model.png)

![FEM: tatsächlicher Solveroutput](fem_sandwich_q20/B/level_3/test/static_stress_xx.png)


## FEM-Bilder des synthetischen Prüffalls – keine Biest-Ergebnisse

**Diese Modelle, Netze und Solverergebnisse gehören ausschließlich zum synthetischen Software-Prüffall. Sie sind kein FEM-Nachweis der Excel-Holmauslegung und kein A/B-Vergleich des Biest-Holms.**
Gezeigt wird der vorhandene homogene I-Holm-Prüffall (L=0,15 m je Halbflügel, E=70 GPa, ν=0,3, ρ=2700 kg/m³) auf seiner feinsten vorhandenen Netzstufe. Die Statik wurde für die Spannungsanforderung erneut mit CalculiX gerechnet. Das 2-%-Konvergenzziel des Auflagenversuchs war noch nicht erreicht; insbesondere Spannungen an Last- und Lagerstellen sind netzabhängig.
Modellbilder zeigen die parametrischen Körper aus den tatsächlichen CAD-Eingaben; Netzbilder zeigen die zugehörigen quadratischen Tetraeder. Verformungsbilder überlagern das unverformte Netz; Farbskala und Vergrößerungsfaktor sind getrennt angegeben.
Spannungsbilder zeigen globale Längsspannung σxx in MPa, positiv bei Zug und negativ bei Druck. x entspricht der UD-Gurtfaserrichtung; im ±45°-Schlauch ist σxx keine lokale Faserspannung. Dargestellt werden Mittelwerte der echten Integrationspunktspannungen innerhalb jedes Elements, ohne Glättung über Materialgrenzen. Die Farbskala enthält daher nicht zwingend die Integrationspunktspitze. Eine Spannungsdarstellung ist kein CFK-Festigkeitsnachweis.

### Synthetischer Prueffall: Flug-Halbmodell

1846 Knoten, 867 C3D10-Elemente; max. reale Verschiebung 0.0091631 mm. Max. |σxx| an Integrationspunkten: 1.2645 MPa.
[Solverdaten und Herkunft](fem_reference/flight/gallery.json); [CalculiX-Ergebnisdatei](fem_reference/flight/gallery_static.dat).

**Parametrisches räumliches Modell**

![Synthetischer FEM-Prüffall: Parametrisches räumliches Modell](fem_reference/flight/model.png)

**Quadratisches Volumennetz**

![Synthetischer FEM-Prüffall: Quadratisches Volumennetz](fem_reference/flight/mesh.png)

**Verformung aus CalculiX**

![Synthetischer FEM-Prüffall: Verformung aus CalculiX](fem_reference/flight/deformation.png)

**Längsspannung σxx aus CalculiX**

![Synthetischer FEM-Prüffall: Längsspannung σxx aus CalculiX](fem_reference/flight/stress_xx.png)

### Synthetischer Prueffall: Auflagenversuch-Vollmodell

3630 Knoten, 1721 C3D10-Elemente; max. reale Verschiebung 0.0019459 mm. Max. |σxx| an Integrationspunkten: 0.46719 MPa.
[Solverdaten und Herkunft](fem_reference/test/gallery.json); [CalculiX-Ergebnisdatei](fem_reference/test/gallery_static.dat).

**Parametrisches räumliches Modell**

![Synthetischer FEM-Prüffall: Parametrisches räumliches Modell](fem_reference/test/model.png)

**Quadratisches Volumennetz**

![Synthetischer FEM-Prüffall: Quadratisches Volumennetz](fem_reference/test/mesh.png)

**Verformung aus CalculiX**

![Synthetischer FEM-Prüffall: Verformung aus CalculiX](fem_reference/test/deformation.png)

**Längsspannung σxx aus CalculiX**

![Synthetischer FEM-Prüffall: Längsspannung σxx aus CalculiX](fem_reference/test/stress_xx.png)

## Versionen und Reproduzierbarkeit

```json
{
  "python": "3.9.7 (tags/v3.9.7:1016ef3, Aug 30 2021, 20:19:38) [MSC v.1929 64 bit (AMD64)]",
  "packages": {
    "numpy": "2.0.2",
    "scipy": "1.13.1",
    "matplotlib": "3.9.4",
    "xlrd": "2.0.2",
    "openpyxl": "3.1.5",
    "PyYAML": "6.0.3"
  },
  "freecad_python": {
    "path": "C:/Program Files/FreeCAD 1.1/bin/python.exe",
    "available": true,
    "returncode": 0,
    "version": "['1', '1', '4', '20260928 (Git shallow)', 'Unknown', '2026/09/28 13:46:34', '(HEAD detached at 4fd3bf320)', '4fd3bf320d9566a27e60069fc8387448aaa3a094']"
  },
  "calculix": {
    "path": "C:/Program Files/FreeCAD 1.1/bin/ccx.exe",
    "available": true,
    "returncode": 201,
    "version": "This is Version 2.22"
  },
  "gmsh": {
    "path": "C:/Program Files/FreeCAD 1.1/bin/gmsh.exe",
    "available": true,
    "returncode": 0,
    "version": "4.15.0"
  }
}
```

## Offizielle technische Quellen

- [CalculiX 2.22 Handbuch](https://www.dhondt.de/ccx_2.22.pdf): C3D10, C3D20R, *ELASTIC / ENGINEERING CONSTANTS, *ORIENTATION, *SOLID SECTION, *EQUATION, *FREQUENCY, *MASS, *NODE PRINT und *EL PRINT.
- [FreeCAD Part-Scripting](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Topological_data_scripting.md): Part-Geometrie und Export.
- [Gmsh-Handbuch](https://gmsh.info/doc/texinfo/gmsh.html): STEP-Import, MSH2, quadratische Tetraeder und Knotenreihenfolge.

Quelle der Excel-Auslegung: Christian Baron, 11/2013; Bearbeitungen und Kommentare der gelieferten Arbeitsmappe bleiben unverändert.

## Separater Software-Prüfnachweis

[Referenztests und tatsächlich ausgeführte synthetische Solverläufe](validation.md). Diese Ergebnisse gehören nicht zur gelieferten Excel-Holmauslegung.

## Numerische Balkenkonvergenz

[Verdopplung der Balkenelemente](beam_convergence.json): relative Änderungen der statischen Durchbiegungen und der ersten sechs Eigenfrequenzen bezogen auf das verfeinerte Modell dokumentiert. Dies prüft die Diskretisierung, nicht die Richtigkeit der Material-/Fertigungsannahmen.

## Unabhängiger einfacher C3D20R-Referenzfall

Ein separater homogener 3D-Kragträger wurde tatsächlich mit CalculiX gerechnet und mit geschlossenen Balkenformeln verglichen. Dieser synthetische Referenzfall prüft Elementexport, Einheiten, Statik und Dynamik; er bestätigt keine Genauigkeit des komplexen Biest-Modells.
Abweichung der Spitzendurchbiegung: -0.747 %; Abweichung der ersten Eigenfrequenz: 0.278 %.
[Eingaben und tatsächliche Referenzergebnisse](c3d20r_reference/validation.json).

## CAD-/Netz-Konsistenz

[Erneut geöffnete CAD-Dateien, gültige Volumenkörper und Vergleich der CAD-/Netzmassen](cad_validation.json).

[Prüfung der tatsächlichen Original-FEM-Dateien und Reaktionsgleichgewichte](original_fem_validation.json).
