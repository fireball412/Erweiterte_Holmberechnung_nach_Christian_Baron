"""Figure-specific reading guidance, using the current calculated values."""
import json


def beam_notes(name,model,cfg,analysis):
    variants=analysis.get('variants',{})
    summaries={v:r['summary'] for v,r in variants.items()}
    def values(key,factor=1,unit=''):
        return '; '.join(f"{v}: {s[key]*factor:.4g}{unit}" for v,s in summaries.items())
    L=model['half_span'];a=model['parameters']['support_fraction']*L
    q=model['reconstructed'].get('uniform_q_N_m',model['parameters']['total_lift']/2/L)
    moment=model['reconstructed'].get('root_moment_Nm',q*L**2/2)
    if cfg['flight']['distribution']=='chord_proportional':
        from .loads import chord_resultants
        loads=chord_resultants(model,cfg)
        load_reading='Oben links tiefenproportionale Streckenlast q(x) [N/m], oben rechts Querkraft V [N], unten links Moment M [N·m], unten rechts Krümmung κ=M/EI [1/m]. A/B haben dieselbe äußere Last; ihre Kurven können übereinanderliegen.'
        load_meaning=f"Die Last folgt der separat aus Excel importierten Flächentiefe, nicht der Gurtbreite: q(0)={loads['root_q_N_m']:.4g} N/m und q(L)={loads['tip_q_N_m']:.4g} N/m. Das Integral beträgt unverändert {loads['force_N']:.5g} N je Halbflügel. V und M fallen daher nicht mehr wie bei Gleichlast linear beziehungsweise rein quadratisch über die gesamte Spannweite ab; die abschnittsweise lineare Tiefenkontur erzeugt entsprechende Übergänge. Das Wurzelmoment beträgt {loads['moment_Nm']:.5g} N·m, gegenüber {moment:.5g} N·m bei der früheren Gleichlast. Unterschiede zwischen A/B entstehen in κ über EI, nicht in q, V oder M. Ein örtlich konstanter c_l ist eine Annahme; Randwirbel, Verwindung und lokale Profile sind nicht aerodynamisch gelöst. Die endliche Spitzenlast folgt dieser Annahme und ist keine behauptete reale Randwirbelverteilung. κ ist kein Festigkeitskriterium."
    else:
        load_reading='Oben links Gleichlast q [N/m], oben rechts Querkraft V [N], unten links Moment M [N·m], unten rechts Krümmung κ=M/EI [1/m]. Alle vier Kurven beziehen sich auf den Flug-Halbflügel; A/B-Farben können bei gleichen Werten vollständig übereinanderliegen.'
        load_meaning=f'Die Last q≈{q:.4g} N/m ist für A/B gleich. V nimmt linear und M quadratisch auf null ab; das Wurzelmoment beträgt {moment:.4g} N·m. Unterschiede in κ=M/EI stammen aus den Steifigkeiten. Krümmungssprünge sind keine zusätzlichen äußeren Kräfte und kein Bruchkriterium.'
    notes={
        'geometry_plies':('Geometrie und Lagenplan',
            'Oben: Außenhöhe und Gurtbreite in mm über der Halbspannweite x. Unten: UD-Lagen je Gurt; die Stufenlinie A zeigt die diskreten Excel-Intervalle, B die durchgehenden Wurzellagen.',
            f"Der Gurt folgt dem Keil und bleibt nach Erreichen der YAML-Mindestbreite {cfg['geometry'].get('minimum_cap_width_m',0)*1000:g} mm breit. Die Höhe nimmt weiter ab. Der Nullwert der A-Lagen am Endpunkt kennzeichnet das Ende, keinen endlichen gurtlosen Abschnitt. B behält mehr Material außen und ist deshalb steifer und schwerer; die Mindestbreite ändert nicht den Lagenplan."),
        'supports':('Lastfälle und Lagerung',
            f'Oben: eingespannter Halbflügel von 0 bis {L:g} m mit aufwärts gerichteter Fluglast. Unten: vollständiger Flügel mit beweglicher Mitte, zwei Auflagen bei ±{a:.3f} m und zentraler Abwärtskraft.',
            'Die Flugeinspannung und die Versuchslager sind unterschiedliche Randbedingungen; ihre Verformungswerte sind nicht direkt vergleichbar. Das Bild zeigt das mechanische Prinzip. Die räumlichen Auflagerbedingungen sind im FEM-Abschnitt beschrieben. Bei bottom_contact_line werden nur Unterseitenknoten auf einer Linie je Auflager vertikal gehalten. Innere und obere Knoten bleiben vertikal frei; Biegeneigung und horizontales Gleiten werden zugelassen, abgesehen von der Starrkörperstabilisierung. Die Lagerung bleibt bilateral.'),
        'beam_comparison':('Balkenvergleich A/B: Steifigkeit, Masse und Verformung',
            'Vier Teilbilder: oben links Biegesteifigkeit EI [N·m²], oben rechts längenbezogene Masse μ [kg/m], unten links Flugverformung w [mm], unten rechts Auflagenversuch w [mm]. x ist jeweils die Spannweitenkoordinate in m.',
            'Lagenabstufungen erzeugen Sprünge in EI und μ bei A; das vordere Stegende bei 0,70 m erzeugt zusätzlich einen Übergang bei beiden Varianten. Mindestbreite und Mindestwanddicke ändern weitere Kurvensteigungen. B liegt außerhalb der Wurzel überwiegend höher: zusätzliche Masse erkauft zusätzliche Steifigkeit. Flugtip im Balken: '+values('flight_tip_m',1000,' mm')+'. Die gestrichelte Krümmungsintegration und die numerische Balkenlösung liegen fast übereinander; das ist eine interne Verfahrensprüfung, kein unabhängiger Bauteilnachweis. Im Versuch sinkt die Mitte ab ('+values('test_root_m',1000,' mm')+'); die freien Überhänge heben sich durch die Auflagerneigung. Die großen Flugverformungen verlangen eine nichtlineare Prüfung; ihr tatsächlicher Abschlussstatus steht im FEM-Abschnitt.'),
        'loads':('Fluglast, Querkraft, Biegemoment und Krümmung',
            load_reading,load_meaning),
        'modes':('Normierte Biegeeigenformen des 1D-Balkens',
            'Je ein Teilbild für A und B: x über den ganzen Flügel, vertikal φ/max|φ| ohne Einheit. Die Legende nennt die Eigenfrequenz jeder Kurve. Vorzeichen und Amplitude einer Eigenform sind frei wählbar.',
            'Die erste Balkenfrequenz beträgt '+ '; '.join(f"{v}: {s['frequencies_Hz'][0]:.4g} Hz" for v,s in summaries.items())+'. Weitere Vorzeichenwechsel kennzeichnen höhere Biegeformen. Eine hohe normierte Auslenkung ist keine vorhergesagte Schwingungsamplitude. Die Zentralmasse wirkt besonders auf Formen mit großer Bewegung in der Mitte. Der 1D-Balken beschreibt reine vertikale Biegung; 3D-FEM-Indizes können wegen Torsions- und Mischformen nicht ungeprüft zugeordnet werden.'),
        'sections':('Tatsächliche Wurzelquerschnitte A und B',
            'Die beiden Teilbilder zeigen y und z in mm. Blau: UD-Gurte; beige: Depron; grau: CFK-Schlauch. Die Querpositionen der beiden Stege und der freie Taschenbereich werden geometrisch dargestellt.',
            'A und B besitzen dieselben Wurzellagen und damit hier denselben Querschnitt. Ihre Unterschiede entstehen weiter außen. Der große Abstand zwischen Ober- und Untergurt erzeugt die hohe Biegesteifigkeit; die Stege übertragen Schub zwischen den Gurten. Eine gleiche Wurzelgeometrie bedeutet daher nicht gleiche Gesamtverformung oder Gesamtmasse. Ein zusätzlicher Verbinder-Steifigkeitsbeitrag ist nicht enthalten.'),
        'stegannahmen':('Geometrieskizze und Spitzenquerschnitt',
            'Draufsicht, Wurzelquerschnitt und vergrößerter Spitzenquerschnitt B. Maßangaben sind maßgebend; die Gesamtzeichnung ist schematisch. Der hintere Steg läuft bis 1,40 m, der vordere bis 0,70 m.',
            'Die konstante 6-mm-Gurtbreite schafft Platz für den unverändert 5 mm breiten Kern und den CFK-Schlauch. Der Steg bleibt bis zur Spitze mit beiden Gurten verbunden; der frühere stegfreie Bereich entfällt. Die Mindestwanddicke 0,10 mm ist eine Annahme, kein aus Excel oder Messung bestätigter Fertigungswert. Diese Skizze erläutert Eingaben und enthält selbst kein Solverergebnis.')}
    if name=='beam_comparison' and analysis.get('fem_bending_overlay'):
        title,reading,meaning=notes[name]
        reading+=' Gepunktet: lineare 3D-FEM der feinsten abgeschlossenen Netzstufe, ohne Darstellungsfaktor. Die Linie ist das arithmetische Mittel der vertikalen Knotenverschiebungen je x-Querschnitt; das transparente Band zeigt deren Minimum bis Maximum (einschließlich Torsion und lokaler Verformung).'
        meaning+=' Die FEM-Überlagerung verwendet dieselben Flug- beziehungsweise Versuchslasten. Unterschiede zum Balken können aus Schub, Torsion, örtlicher Querschnittsverformung und der räumlichen Lagerung stammen. Der Knotenmittelwert ist keine flächengewichtete Querschnittsverschiebung; das Band zeigt die Streuung innerhalb des Querschnitts. Nichtlineare Ergebnisse sind in dieser Überlagerung nicht enthalten.'
        meaning+=(' Das konfigurierte 2-%-Netzkonvergenzziel ist für die ausgewerteten Verschiebungen und sechs Eigenfrequenzen erreicht; dies belegt keine lokale Spannungskonvergenz.' if analysis.get('fem_bending_converged') else ' Die FEM-Netzkonvergenz ist noch nicht für alle ausgewerteten Größen erreicht.')
        if analysis.get('test_measurements_plotted'):
            reading+=' Schwarze Punkte: Excel-Messungen des B-Modells, ΔHöhe an x=0 abwärts und ΔTip aufwärts; Vorzeichen gemäß YAML. Die Tip-Seite ist nur für die Darstellung als +L angenommen, da Excel keine Seite angibt.'
            meaning+=' Messwerte sind unabhängig von den berechneten Kurven und wurden nicht zum Anpassen der Materialwerte verwendet. Die genaue Messposition über der Flächentiefe ist nicht dokumentiert; FEM-Knotenmittel und Tabellenwert im Taschenband sind daher nicht automatisch exakt dieselbe Messgröße.'
        return title,reading,meaning
    if name=='loads' and analysis.get('fem_rear_curvature'):
        title,reading,meaning=notes[name]
        reading+=' Im Krümmungsdiagramm zusätzlich gestrichelt: lineare Flug-FEM A/B entlang der Mitte des hinteren Depronkerns bei y=3 mm, z=0. Durchgezogen: Balkenkrümmung M/EI. Kein Versuchslastfall.'
        meaning+=' Die FEM-Kurve ist die zweite Ableitung w\u2032\u2032 der tatsächlichen vertikalen Knotenverschiebungen auf dieser Linie. Sie wird durch lokale kubische Ausgleichspolynome über jeweils fünf benachbarte Stationen gewonnen; dadurch werden Netzrauschen und scharfe Übergänge geglättet. Die örtlich variable Auswertebreite steht zusammen mit Verschiebung und Krümmung in flight_rear_curvature_A.csv beziehungsweise flight_rear_curvature_B.csv. Dies ist eine lineare kinematische Linienkrümmung einschließlich örtlicher Schub-/Verformungseinflüsse, nicht direkt aus den Spannungen bestimmte reine Balkenbiegung. An Einspannung, Lagensprüngen und Endpunkten ist die Ableitung besonders empfindlich; lokale Krümmungskonvergenz wurde nicht nachgewiesen. Die große Flugverformung wird hier nicht geometrisch nichtlinear korrigiert; w\u2032\u2032 darf nicht als exakte geometrische Krümmung der stark verformten Linie gelesen werden.'
        meaning+=' Die ersten und letzten zwei FEM-Stationen werden im Diagramm ausgelassen, weil dort der zentrierte Fünf-Punkte-Ansatz nicht verfügbar ist; ihre nicht zentrierten Schätzwerte bleiben in der CSV ausdrücklich mit interior_stencil=False markiert. Es wird kein FEM-Krümmungswert an der exakten Wurzel oder Spitze behauptet.'
        return title,reading,meaning
    return notes[name]


def fem_notes(path,out,fem):
    rel=path.relative_to(out).parts
    variant=rel[1];record=fem['variants'][variant]
    if path.stem=='convergence':
        changes=record['convergence'].get('relative_changes',{})
        labels={'flight_tip_m':'Flugtip','test_root_m':'Versuchswurzel','frequency_Hz':'ausgewählte Biegemode'}
        percentages=', '.join(f'{labels[k]} {100*changes[k]:.3g} %' for k in labels if k in changes)
        return (f'FEM {variant}: Netzkonvergenz',
            'Drei Teilbilder zeigen Flug-Spitzenverschiebung [m], Versuchswurzel [m] und ausgewählte Eigenfrequenz [Hz] gegen den Netzverfeinerungsfaktor. Faktor 3 ist das feinste Netz, keine physische Laststeigerung. Die y-Achsen sind unterschiedlich skaliert.',
            f'Änderung der letzten beiden Stufen, bezogen auf die feinste: {percentages}. '+('Das konfigurierte Ziel ist erreicht.' if record['convergence']['converged'] else 'Das 2-%-Ziel ist nicht für alle geprüften Größen erreicht.')+' Der Frequenzgraph zeigt nur eine ausgewählte Form; für den Gesamtstatus werden alle sechs Frequenzen geprüft. Ein optisch flacher Verlauf beweist keine vollständige Konvergenz, insbesondere nicht für lokale Spannungen oder bei Modenwechseln.')
    level=int(rel[2].split('_')[-1]);case=rel[3]
    row=next(r for r in record['meshes'] if r['level']==level)
    context=f"FEM {variant}, Netz {level}, {'Flug' if case=='flight' else 'Auflagenversuch'}"
    stem=path.stem
    if stem.startswith('nonlinear'):
        context+=', geometrisch nichtlinear'
    elif stem.startswith('static'):
        context+=', linear'
    if stem.startswith('mode_'):
        index=int(stem.split('_')[-1])-1
        freq=row['frequencies_Hz'][index]
        parity=row.get('mode_symmetry',['nicht klassifiziert']*6)[index]
        frac=row.get('vertical_fractions',[0]*6)[index]*100
        return (context+f': Eigenform {index+1}, {freq:.4g} Hz',
            'Seitenprojektion in die x-z-Ebene. Schwarze Punkte: unverformtes Netz; farbige Fläche: Eigenform mit willkürlich gewählter Darstellungsamplitude. Die Farbskala φz/max|φz| ist dimensionslos; die Achsen geben die gezeichneten Koordinaten in m an.',
            f'Diese Form ist {parity}; der rechnerische Anteil Σuz²/Σ|u|² beträgt {frac:.3g} %. Das ist eine Verschiebungskennzahl, keine effektive Modalmasse oder Energiequote. '+('Sie ist die im Konvergenzgraphen verwendete überwiegend vertikale Form. ' if row.get('selected_mode')==index+1 else 'Sie ist eine weitere räumliche Eigenform und nicht automatisch die gleich nummerierte Balkenmode. ')+'Formen mit ähnlicher Frequenz können sich bei Netzänderung mischen oder die Reihenfolge wechseln. Die 2D-Projektion zeigt seitliche Bewegung und Torsion nur eingeschränkt. Weder Amplitude noch Vorzeichen sagen eine reale Schwingungsantwort voraus; die Modalanalyse ist unbelastet und linear.')
    detail='detail_' in stem
    zoom='Wurzelausschnitt derselben Rechnung; keine zusätzliche Laststufe. ' if detail else ''
    if stem.endswith('model'):
        return (context+(': Wurzeldetail des Modells' if detail else ': räumliches Modell'),
            zoom+'Geometrie aus den tatsächlichen CAD-Eingaben; Achsen in mm. Blau sind die Gurte, grau die CFK-Schläuche, beige die Depronkerne. Verdeckte Innenflächen können in der Außenansicht unsichtbar sein.',
            'Hier wird die angenommene Bauweise kontrolliert, nicht die Beanspruchung: gerader hinterer Steg bis zur Spitze, vorderer Steg nur im inneren Bereich, diskrete Gurtdicken in A beziehungsweise durchgehende Wurzellagen in B. '+('Im Wurzelausschnitt ist vor allem die Trennung der beiden Stege wichtig; die 6-mm-Spitze ist hier nicht sichtbar. ' if detail else 'Die äußere Mindestgurtbreite beträgt 6 mm; eine durchgehende Verbindung ersetzt den früheren freien Gurtauslauf. ')+'Flügelschale und ein nachgewiesener steifer Verbinder fehlen weiterhin.')
    if stem.endswith('mesh'):
        return (context+(': Netz am Wurzeldetail' if detail else ': Volumennetz'),
            zoom+f"Gezeigt wird die sichtbare Oberfläche des 3D-Netzes mit insgesamt {row[case+'_nodes']:,} Knoten und {row[case+'_elements']:,} quadratischen C3D20R-Volumenelementen. Achsen in mm; sichtbare Dreieckslinien stammen auch aus der Darstellung der Elementflächen und sind keine Tetraederelemente.",
            'Die schmalen CFK-Schichten erzeugen stark unterschiedliche Elementabmessungen. Feinere Netze prüfen deren Einfluss; eine dichte Oberfläche allein beweist keine Genauigkeit. Innerhalb der Abschnitte teilen Materialien Knoten, an Lagensprüngen verbinden interpolierende Gleichungen nichtpassende Flächen. '+('Das Detail hilft, Last-/Lagerband und dünne Schichten zu erkennen; daraus folgt noch kein konvergierter örtlicher Spannungswert.' if detail else 'Die Modellabmessungen und Lasten sind auf den Netzstufen gleich; nur die Diskretisierung wird verfeinert.'))
    nonlinear=stem.startswith('nonlinear')
    if stem.endswith('deformation'):
        scalar=row.get('flight_nonlinear_m' if nonlinear else 'flight_tip_m' if case=='flight' else 'test_root_m')
        measured=f"{scalar*1000:.4g} mm" if scalar is not None else 'oben tabelliert'
        scope='Die Versuchslager sind bilateral. Die aktive Lageridealisation ist im FEM-Abschnitt dokumentiert. Bei bottom_contact_line sind nur die Unterseitenknoten auf einer Kontaktlinie vertikal gehalten; die übrigen Querschnittsknoten bleiben vertikal frei und die Außenflügel können die Biegeneigung fortsetzen. Dies ist kein einseitiger Kontaktversuch und kein Nachweis realer Kontaktpressungen.'
        if case=='flight':
            scope='Geometrisch nichtlinearer Vergleich auf dieser Netzstufe; kein netzkonvergierter nichtlinearer oder CFK-Festigkeitsnachweis.' if nonlinear else 'Die lineare Flugverformung ist groß relativ zur Halbspannweite. Der Abschlussstatus der nichtlinearen Vergleichsläufe steht oben; der lineare Wert ist kein bestätigter realer Flugzustand.'
        return (context+(': Verformung im Wurzeldetail' if detail else ': Verformung'),
            zoom+'Grau: unverformte Lage; farbig: verformte Oberfläche mit dem im Bild genannten Faktor. Achsen sind mm. Die Farbe zeigt den realen Betrag |u| [mm], nicht die mit dem Darstellungsfaktor multiplizierte Auslenkung und nicht nur die vertikale Komponente.',
            ('Die obere Flugtip-Verschiebung uz beträgt '+measured+'. Ober- und Untergurt bewegen sich durch den durchgehenden Steg gemeinsam; der alte freie Gurtauslauf ist beseitigt. ' if case=='flight' else 'Die gemittelte vertikale Wurzelverschiebung im Taschenband beträgt '+measured+'. Die Mitte sinkt ab, freie Überhänge können sich heben. Der größte räumliche Verschiebungsbetrag muss nicht an der Wurzel liegen und darf nicht mit diesem Tabellenwert gleichgesetzt werden. ') + ('Der Wurzelausschnitt zeigt vor allem lokale Bewegungen und nicht den Verlauf bis zur Spitze. ' if detail else '')+scope)
    if stem.endswith('stress_xx'):
        meta_path=path.parent/('nonlinear.gallery.json' if nonlinear else 'static.gallery.json')
        peak=''
        if meta_path.exists():
            peak_value=json.loads(meta_path.read_text(encoding='utf-8'))['max_abs_sigma_xx_integration_point_Pa']/1e6
            peak=f'Der größte Betrag an Integrationspunkten im gesamten Modell beträgt {peak_value:.4g} MPa; er kann außerhalb des Ausschnitts oder über der gemittelten Elementfarbskala liegen. '
        return (context+(': Längsspannung im Wurzeldetail' if detail else ': globale Längsspannung'),
            zoom+'Unverformte Geometrie mit globaler σxx [MPa]: positiv Zug, negativ Druck, gemäß Farbskala. Gezeigt sind Integrationspunktmittelwerte je Element; es wird nicht über Materialgrenzen geglättet.',
            peak+'Die gegensinnigen Normalspannungen in Ober- und Untergurt kennzeichnen Biegung. Im unverformten UD-Gurt verläuft die Faserrichtung entlang x. Bei großen nichtlinearen Rotationen ist globales σxx auch dort nicht automatisch die lokale Faserspannung. Im ±45°-Schlauch ist σxx keine lokale Faserspannung und zeigt auch nicht die gesamte Schubbeanspruchung. Lokale Spitzen an Lagensprüngen, Lasten und Lagern sind netzabhängig. Es fehlen CFK-Festigkeitswerte sowie Klebe-, Delaminations- und Beulnachweise; die Farben bedeuten weder sicher noch gebrochen. '+('Wegen der großen linearen Flugverformung sind auch diese Spannungen nur Ergebnisse des linearen Vergleichsmodells.' if case=='flight' and not nonlinear else 'Die ideale Verklebung und die jeweiligen Lagerbedingungen beeinflussen die örtliche Lastübertragung.'))
    raise ValueError(f'Keine Bildinterpretation für {path}')


def reference_notes(filename,manifest):
    kind=filename.rsplit('.',1)[0]
    notes={
        'model':('Achsen in mm; dargestellt ist die parametrische Geometrie des homogenen Referenz-I-Holms.', 'Der einfache, ausdrücklich definierte Querschnitt dient der Softwareprüfung. Seine Steifigkeit und Lastübertragung sind nicht die des CFK-/Depron-Holms; dieses Bild validiert keine Biest-Geometrie.'),
        'mesh':('Die Drahtdarstellung zeigt die Oberfläche des quadratischen C3D10-Tetraedernetzes; Achsen in mm.', 'Hier wird ein anderer Netz-/Elementadapter als beim aktuellen C3D20R-Biest-Modell geprüft. Die Netzfeinheit und die Genauigkeit des Referenzfalls dürfen nicht auf das Originalmodell übertragen werden.'),
        'deformation':('Grau ist die unverformte Lage; Farbe ist der reale Betrag |u| in mm. Der gezeichnete Weg ist mit dem Bildfaktor vergrößert.', f"Die maximale reale Verschiebung dieses Referenzfalls beträgt {manifest['max_displacement_m']*1000:.4g} mm; die große sichtbare Biegung ist eine Darstellungsvergrößerung. Diese Antwort prüft den definierten Referenzlastfall und ist keine Vorhersage für den Biest-Holm."),
        'stress_xx':('Globale σxx in MPa auf der unverformten Geometrie; positiv Zug, negativ Druck; Mittelwerte je Element.', f"Maximaler Betrag an Integrationspunkten: {manifest['max_abs_sigma_xx_integration_point_Pa']/1e6:.4g} MPa. Der Zug-/Druckwechsel zwischen den Gurten ist mit Biegung vereinbar. Lokale Spitzen hängen vom Netz und der Lasteinleitung ab. Dies prüft Spannungsexport und Darstellung; es ist kein CFK-Festigkeitsnachweis.")}
    reading,meaning=notes[kind]
    return manifest['label']+': '+kind,reading,meaning


def explanation(notes):
    title,reading,meaning=notes
    return ['', '**Lesen:** '+reading, '', '**Einordnung:** '+meaning, '']
